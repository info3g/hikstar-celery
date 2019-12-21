import "@babel/polyfill";

import Vue from "@/vue.js";
import axios from "axios";

import { MapHikster, mapData } from "@/map/data.js";
import { mapMethods } from "@/map/methods.js";
import { networkMethods } from "@/map/networkMethods.js";

import "leaflet.pm";
import "leaflet.pm/dist/leaflet.pm.css";

axios.defaults.xsrfHeaderName = "X-CSRFToken";
axios.defaults.withCredentials = true;

new Vue({
  el: "#trail-section-detail-component",
  data: {
    ...mapData,
    errors: {},
    loading: false,
    map: null,
    trailSectionShapeGeojson: null,
    otherTrailSectionsGeojson: null,
    attribution: "",
    activities: [],
    drawnItems: new L.FeatureGroup(),
    trailSection: {
      activities: []
    }
  },
  mounted() {
    $(".alert").removeClass("d-none");
    this.activities = this.getJsonData("activities_data");
    this.otherTrailSectionsGeojson = this.getGeojsonData(
      "other_trail_sections_geojson"
    );
    if (this.isEditMode) {
      this.trailSectionShapeGeojson = this.getGeojsonData(
        "trail_section_shape_geojson"
      );
      this.trailSection = this.getJsonData("trail_section_data");
      this.activities.forEach(item => {
        if (this.selectedActivities.includes(item.id)) {
          item.selected = true;
        }
      });
    }

    this.initMap();
  },
  computed: {
    isEditMode() {
      return pageMode === "edit";
    },
    selectedActivities() {
      return this.trailSection.activities.map(item => item.activity);
    }
  },
  methods: {
    ...mapMethods,
    ...networkMethods,
    initMap() {
      const config = {
        center: [50.13466432216696, -72.72949218750001],
        zoom: 10,
        zoomControl: true,
        zoomAnimation: true,
        minZoom: 3,
        maxZoom: 17,
        scrollWheelZoom: true
      };

      this.setMapStyles();

      this.map = L.map("map", config);
      this.setAttribution();

      this.map.on("zoomend", e => {
        this.updateAttribution();
      });

      this.map.on("pm:create", e => {
        this.drawnItems.addLayer(e.layer);
      });

      if (this.isEditMode) {
        this.drawnItems.clearLayers();
        this.drawnItems = L.geoJSON(this.trailSectionShapeGeojson).addTo(this.map);
      }

      this.map.pm.addControls({
        position: "topleft",
        drawCircle: false,
        drawMarker: false,
        drawCircleMarker: false,
        drawRectangle: false,
        drawPolygon: false
      });
      this.resultLayers = L.geoJson().addTo(this.map);
      this.selectionLayers = L.geoJson().addTo(this.map);
      this.highlightLayers = L.geoJson().addTo(this.map);

      this.guideLayers = L.geoJson(this.otherTrailSectionsGeojson, {
        color: "#4e822c",
        pmIgnore: true
        // snapIgnore : true
      }).addTo(this.map);

      if (this.otherTrailSectionsGeojson.features.length > 0) {
        this.map.fitBounds(this.guideLayers.getBounds());
      } else {
        this.fitToLocations(true);
      }

      this.setUpMapFileUploader();
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
      });
    },
    setMapStyles() {
      this.selectedTrailStyle = {
        color: MapHikster.DARK_GREEN,
        weight: 3,
        opacity: 1
      };
    },
    getError(key) {
      let error = this.errors;
      for (const k of key.split(".")) {
        error = error[k];
        if (!error) {
          return;
        }
      }
      if (Array.isArray(error)) {
        return error[0];
      }
      return error;
    },
    cancel() {
      window.trailSection.href = "/admin/";
    },
    getShapeValue() {
      const layers = this.drawnItems.getLayers();
      if (layers.length > 0) {
        var geometry = this.drawnItems.getLayers()[0].toGeoJSON().geometry;

        var new_geos = {
          type: geometry.type,
          coordinates: []
        };
        geometry.coordinates.forEach(geo => {
          new_geos.coordinates.push([geo[0], geo[1]]);
        });
        return new_geos;
      }
      return null;
    },
    save(redirect) {
      this.errors = {};
      this.loading = true;
      const shape = this.getShapeValue();
      if (shape) {
        this.$set(this.trailSection, "shape_2d", shape);
      } else {
        delete this.trailSection.shape_2d;
      }
      var newActivities = [];

      this.activities.forEach((activity, i) => {
        var selected = this.selectedActivities.find(
          item => item.activity === activity.id
        );
        if (activity.selected) {
          newActivities.push({
            id: activity.id, //selected ? selected.id : null,
            activity: activity.id
          });
        }
      });

      this.$set(this.trailSection, "activities", newActivities);
      const data = { ...this.trailSection };
      delete data.shape;

      let url = "/admin/api/trail-sections/";
      let method = "post";

      if (this.isEditMode) {
        url = `${url}${this.trailSection.trailsection_id}/`;
        method = "patch";
      }

      axios({
        method: method,
        url: url,
        data: data
      })
        .then(res => {
          if (redirect) {
            window.location.href = "../";
          } else {
            $("li.breadcrumb-item")
              .last()
              .text(this.trailSection.name);
          }
        })
        .catch(error => {
          console.log(error, "error");
          this.errors = error.response.data;
        })
        .finally(() => {
          this.loading = false;
          window.scrollTo({ top: 0, behavior: "smooth" });
        });
    }
  }
});
