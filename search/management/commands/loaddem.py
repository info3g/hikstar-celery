import os
import tempfile

from subprocess import call, PIPE

from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.conf import settings

try:
    from osgeo import gdal, osr
except ImportError:
    msg = "GDAL Python bindings are not available. Can not proceed."
    raise CommandError(msg)


class Command(BaseCommand):
    help = "Load DEM data (projecting and clipping it if necessary).\n"
    help += "You may need to create a GDAL Virtual Raster if your DEM is "
    help += "composed of several files.\n"
    can_import_settings = True

    def add_arguments(self, parser):
        parser.add_argument(
            "--replace",
            action="store_true",
            default=False,
            help="Replace existing DEM if any.",
        )

    def get_tif_files(self):
        root = "/home/freebsd/extracted_mnt"

        directories = []

        for filename in os.listdir(root):
            directories.append(filename)

        tif_files = []

        for directory in directories:
            for filename in os.listdir(os.path.join(root, directory)):
                if filename.endswith(".tif"):
                    tif_files.append(f"{root}/{directory}/{filename}")

        return tif_files

    def load_to_sql(self, dem_path, verbose=True):
        # Open GDAL dataset
        if not os.path.exists(dem_path):
            raise CommandError("DEM file does not exists at: %s" % dem_path)

        ds = gdal.Open(dem_path)
        if ds is None:
            raise CommandError("DEM format is not recognized by GDAL.")

        # GDAL dataset check 1: ensure dataset has a known SRS
        if ds.GetProjection() == "":
            raise CommandError("DEM coordinate system is unknown.")

        # Obtain dataset SRS
        srs_r = osr.SpatialReference()
        srs_r.ImportFromWkt(ds.GetProjection())

        # Obtain project SRS
        srs_p = osr.SpatialReference()
        srs_p.ImportFromEPSG(settings.SRID)

        # Obtain dataset BBOX
        gt = ds.GetGeoTransform()
        if gt is None:
            raise CommandError("DEM extent is unknown.")

        # Allow GDAL objects to be garbage-collected
        ds = None
        srs_p = None
        srs_r = None

        if verbose:
            self.stdout.write("Everything looks fine, we can start loading DEM\n")

        # Unfortunately, PostGISRaster driver in GDAL does not have write mode
        # so far. Therefore, we relay parameters to standard commands using
        # subprocesses.

        # Step 2: Convert to PostGISRaster format
        output = tempfile.NamedTemporaryFile()  # SQL code for raster creation
        # cmd = "raster2pgsql -c -C -x -I -M -t 100x100 %s mnt %s" % (
        #     dem_path,
        #     "" if verbose else "2>/dev/null",
        # )

        cmd = "raster2pgsql -a -I -M -t 100x100 %s mnt %s" % (
            dem_path,
            "" if verbose else "2>/dev/null",
        )
        try:
            if verbose:
                self.stdout.write("\n-- Relaying to raster2pgsql ------------\n")
                self.stdout.write(cmd)
            kwargs_raster2 = {"shell": True, "stdout": output.file, "stderr": PIPE}
            ret = self.call_command_system(cmd, **kwargs_raster2)
            if ret != 0:
                raise Exception("raster2pgsql failed with exit code %d" % ret)
        except Exception as e:
            output.close()
            msg = "Caught %s: %s" % (e.__class__.__name__, e)
            raise CommandError(msg)

        if verbose:
            self.stdout.write("DEM successfully converted to SQL.\n")

        # Step 3: Dump SQL code into database
        if verbose:
            self.stdout.write("\n-- Loading DEM into database -----------\n")

        cur = connection.cursor()
        output.file.seek(0)
        for sql_line in output.file:
            # if sql_line.startswith(b"CREATE TABLE"):
            #     continue
            cur.execute(sql_line)

        cur.close()
        output.close()
        if verbose:
            self.stdout.write("DEM successfully loaded.\n")
        return

    def load(self, verbose):
        # Check if DEM table already exists
        cur = connection.cursor()
        sql = "SELECT * FROM raster_columns WHERE r_table_name = 'mnt'"
        cur.execute(sql)
        dem_exists = cur.rowcount != 0
        cur.close()

        for dem_path in self.get_tif_files():
            self.load_to_sql(dem_path)

        return

    def handle(self, *args, **options):
        verbose = options["verbosity"] != 0
        self.load(True)

    def call_command_system(self, cmd, **kwargs):
        return_code = call(cmd, **kwargs)
        return return_code
