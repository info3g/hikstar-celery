import "@babel/polyfill";

import Vue from "@/vue.js";
import axios from "axios";
import CKEditor from "@ckeditor/ckeditor5-vue";

import "@/components/icons/hk-plus.js";
import "@/components/icons/hk-times.js";
import { networkMethods } from "@/map/networkMethods.js";
import { mapUtils } from "@/map/utils.js";
import { jsonToFormData, getRandomString, orderBy } from "@/utils.js";
import { isObject } from "@/utils.js";
import { ckeditorConfig } from "@/ckeditor/config.js";

axios.defaults.xsrfHeaderName = "X-CSRFToken";
axios.defaults.withCredentials = true;

Vue.use(CKEditor);

new Vue({
  el: "#location-detail-component",
  data: {
    ...ckeditorConfig,
    errors: {},
    loading: false,
    map: null,
    attribution: "",
    location: {
      address: {},
      contact: [],
      images: []
    },
    drawControl: new L.Control.Draw(),
    editControl: new L.Control.Draw(),
    drawnItems: new L.FeatureGroup(),
    locationShapeGeojson: null,
    contactTypes: []
  },
  mounted() {
    this.location = JSON.parse(
      document.getElementById("location_data").textContent
    );
    this.locationShapeGeojson = JSON.parse(
      JSON.parse(document.getElementById("location_shape_geojson").textContent)
    );

    this.addImage();
    this.addContact();
    this.contactTypes = JSON.parse(
      document.getElementById("contact_types_data").textContent
    );
    this.initMap();
  },
  computed: {
    orderedImages() {
      return orderBy(this.location.images, "image_type");
    }
  },
  methods: {
    ...mapUtils,
    setAsBanner(newBanner) {
      this.location.images.forEach((item, idx) => {
        if (item.image_type === "banner") {
          item.image_type = "photo";
        }
      });
      newBanner.image_type = "banner";
    },
    initMap() {
      const config = {
        center: [50.13466432216696, -72.72949218750001],
        zoom: 6,
        zoomControl: true,
        zoomAnimation: true,
        minZoom: 3,
        maxZoom: 17,
        scrollWheelZoom: true
      };

      this.map = L.map("map", config);
      this.setAttribution();
      this.map.on("zoomend", e => {
        this.updateAttribution();
      });
      this.setUpMapFileUploader();
      this.setUpLocationDraw();
    },
    getEditControl() {
      return new L.Control.Draw({
        draw: false,
        edit: {
          featureGroup: this.drawnItems
        }
      });
    },
    setUpLocationDraw() {
      const validFeatures = this.locationShapeGeojson.features.filter(
        item => item.geometry !== null
      );
      this.$set(this.locationShapeGeojson, "features", validFeatures);

      this.drawControl = new L.Control.Draw();
      this.editControl = this.getEditControl();

      if (validFeatures.length > 0) {
        this.drawnItems = L.geoJson(this.locationShapeGeojson).addTo(this.map);
        this.map.fitBounds(this.drawnItems.getBounds().pad(0.25), {
          animate: true
        });
        this.editControl = this.getEditControl();
        this.map.addControl(this.editControl);
      } else {
        this.drawnItems.addTo(this.map);
        this.map.addControl(this.drawControl);
      }
      this.map.on(L.Draw.Event.CREATED, e => {
        const type = e.layerType;
        const layer = e.layer;
        this.drawnItems.addLayer(layer);
        this.onShapeCreated();
      });
      this.map.on(L.Draw.Event.DELETED, e => {
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
    addContact() {
      this.location.contact.push({
        id: 0,
        type: null,
        value: ""
      });
    },
    removeContact(idx) {
      this.location.contact.splice(idx, 1);
    },
    addImage() {
      this.location.images.push({
        credit: ""
      });
    },
    removeImage(idx) {
      this.location.images.splice(idx, 1);
    },
    cancel() {
      window.location.href = "/admin/";
    },
    getShapeValue() {
      const layers = this.drawnItems.getLayers();
      if (layers.length > 0) {
        return this.drawnItems.getLayers()[0].toGeoJSON().geometry;
      }
      return null;
    },
    uploadImage(event, item) {
      this.addImage();
      delete item.id;
      item.image_file = event.target.files[0];
      item.image_type = "photo";
      const formData = jsonToFormData(item);
      const url = `/admin/api/locations/${
        this.location.location_id
      }/upload-image/`;
      item.randomId = getRandomString();
      axios
        .post(url, formData, {
          headers: {
            "Content-Type": "multipart/form-data"
          }
        })
        .then(res => {
          const idx = this.location.images.findIndex(
            im => im.randomId === item.randomId
          );
          this.$set(this.location.images, idx, res.data);
        })
        .catch(error => {
          console.log(error.response.data);
        });
    },
    save(redirect) {
      this.loading = true;
      const contacts = this.location.contact.filter(
        item => item.type && item.value.trim()
      );
      const shape = this.getShapeValue();

      this.$set(this.location, "shape", shape);
      this.$set(this.location, "contact", contacts);

      const length = this.location.images.length;
      this.location.images.forEach((item, idx) => {
        if (idx + 1 < length) {
          delete item.image_file;
          if (!item.image_type) {
            item.image_type = "photo";
          }
        }
      });
      const url = `/admin/api/locations/${this.location.location_id}/`;
      axios
        .patch(url, this.location)
        .then(res => {
          if (redirect) {
            window.location.href = `/admin/${
              this.location.organization
            }/locations/`;
          } else {
            $("li.breadcrumb-item")
              .last()
              .text(this.location.name);
            window.scrollTo({ top: 0, behavior: "smooth" });
          }
        })
        .catch(error => {
          this.errors = error.response.data;
        })
        .finally(() => {
          this.loading = false;
          this.addContact();
        });
    }
  }
});
