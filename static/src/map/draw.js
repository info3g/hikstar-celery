export const mapDrawData = {
  drawControl: new L.Control.Draw(),
  editControl: new L.Control.Draw(),
  drawnItems: new L.FeatureGroup(),
  trailSectionShapeGeojson: {
    features: []
  },

  drawType: {
    trailSectionDetail: "trail-section-detail"
  }
};

export const mapDrawMethods = {
  getEditControl() {
    return new L.Control.Draw({
      draw: false,
      edit: {
        featureGroup: this.drawnItems
      }
    });
  },
  setUpTrailSectionDraw(config) {
    // We use old version of leaflet draw in trailsection page
    // because of leaflet.snap not working on latest version
    const validFeatures = this.trailSectionShapeGeojson.features.filter(
      item => item.geometry !== null
    );
    this.$set(this.trailSectionShapeGeojson, "features", validFeatures);

    const draw = {
      polyline: {
        guideLayers: this.guideLayers.getLayers()
      },
      polygon: true,
      rectangle: true,
      circle: true,
      marker: true,
      circlemarker: true
    };
    if (config && config.enabled) {
      Object.keys(draw).forEach(key => {
        if (!config.enabled.includes(key)) {
          draw[key] = false;
        }
      });
    }

    this.drawControl = new L.Control.Draw({
      draw: draw
    });

    this.editControl = this.getEditControl();

    if (validFeatures.length > 0) {
      this.drawnItems = L.geoJson(this.trailSectionShapeGeojson).addTo(
        this.map
      );
      this.map.fitBounds(this.drawnItems.getBounds().pad(0.25), {
        animate: true
      });
      this.editControl = this.getEditControl();
      this.map.addControl(this.editControl);
    } else {
      this.drawnItems.addTo(this.map);
      this.map.addControl(this.drawControl);

      if (config.type && config.type === this.drawType.trailSectionDetail) {
        this.fitToLocations(true);
      }
    }
    this.map.on("draw:created", e => {
      const type = e.layerType;
      const layer = e.layer;
      layer.snapediting = new L.Handler.PolylineSnap(this.map, layer);
      layer.snapediting.addGuideLayer(this.guideLayers.getLayers());
      layer.snapediting.enable();
      this.drawnItems.addLayer(layer);
      this.onShapeCreated();
    });
    this.map.on("draw:deleted", e => {
      if (this.drawnItems.getLayers().length === 0) {
        this.map.removeControl(this.editControl);
        this.map.addControl(this.drawControl);
      }
    });
  },
  hasDrawnItems() {
    return this.drawnItems.getLayers().length > 0;
  },
  onShapeCreated() {
    this.map.removeControl(this.drawControl);
    this.map.addControl(this.editControl);
    this.map.fitBounds(this.drawnItems.getBounds().pad(0.25), {
      animate: true
    });
  },
  setUpMapFileUploader() {
    L.Control.FileLayerLoad.LABEL =
      '<img class="icon" src="/static/img/folder.svg" alt="file icon"/>';
    const control = L.Control.fileLayerLoad({
      // Allows you to use a customized version of L.geoJson.
      // For example if you are using the Proj4Leaflet leaflet plugin,
      // you can pass L.Proj.geoJson and load the files into the
      // L.Proj.GeoJson instead of the L.geoJson.
      layer: L.geoJson,
      // See http://leafletjs.com/reference.html#geojson-options
      layerOptions: { style: { color: "red" } },
      // Add to map after loading (default: true) ?
      addToMap: true,
      // File size limit in kb (default: 1024) ?
      fileSizeLimit: 1024,
      // Restrict accepted file formats (default: .geojson, .json, .kml, and .gpx) ?
      formats: [".geojson", ".kml", ".gpx"]
    });
    control.addTo(this.map);
    control.loader.on("data:loaded", event => {
      this.drawnItems.clearLayers();
      this.drawnItems = L.geoJSON(event.layer.toGeoJSON()).addTo(this.map);
      this.map.removeLayer(event.layer);
      this.map.removeControl(this.editControl);
      this.editControl = this.getEditControl();
      this.onShapeCreated();
    });
  }
};
