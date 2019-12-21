import "@babel/polyfill";

import Vue from "@/vue.js";
import axios from "axios";
import CKEditor from "@ckeditor/ckeditor5-vue";

import "@/components/icons/hk-plus.js";
import "@/components/icons/hk-times.js";
import { highlightMethods } from "@/map/methods.js";
import { isObject, jsonToFormData, getRandomString, orderBy } from "@/utils.js";
import { mapData, MapHikster } from "@/map/data.js";
import { mapDrawData, mapDrawMethods } from "@/map/draw.js";
import { mapUtils } from "@/map/utils.js";
import { poiMethods } from "@/map/poi.js";
import { ckeditorConfig } from "@/ckeditor/config.js";

axios.defaults.xsrfHeaderName = "X-CSRFToken";
axios.defaults.withCredentials = true;

Vue.use(CKEditor);

new Vue({
  el: "#poi-detail-component",
  data: {
    ...mapData,
    ...mapDrawData,
    ...ckeditorConfig,
    drawControl: null,
    poiShapeGeojson: {},
    errors: {},
    loading: false,
    map: null,
    attribution: "",
    poi: {
      images: [],
      address: {},
      contact: [],
      category: null
    },
    poiMarker: null,
    poiPopup: null,
    imagesForm: [],
    categories: [],
    contactTypes: [],
    successMessage: "",
    addNew: false,
    trailSectionsLayer: null
  },
  mounted() {
    $(".alert").removeClass("d-none");
    this.trailSectionsGeojson = this.getGeojsonData("trail_sections_geojson");
    this.categories = this.getJsonData("poi_categories");
    this.contactTypes = this.getJsonData("contact_types_data");
    this.initMap();
    this.trailSectionsLayer = L.geoJson(this.trailSectionsGeojson, {
      style: {
        color: MapHikster.LIGHT_GREEN,
        weight: 3,
        opacity: 1
      }
    }).addTo(this.map);
    this.map.fitBounds(this.trailSectionsLayer.getBounds().pad(0.25), {
      animate: true
    });
    this.highlightLayers.clearLayers();
    if (this.isEditMode) {
      this.poi = this.getJsonData("poi_data");
      if (!this.poi.address) {
        this.$set(this.poi, "address", {});
      }
      if (this.poi.shape) {
        const coords = this.poi.shape.coordinates;
        if (coords.length > 1) {
          const latlng = new L.LatLng(coords[1], coords[0]);
          this.addMarker(latlng);
          this.map.fitBounds(L.geoJSON(this.poi.shape).getBounds().pad(0.25));
        }
      }
    }
    this.addImage();
    this.addContact();
  },
  computed: {
    orderedImages() {
      return orderBy(this.poi.images, "image_type");
    },
    isEditMode() {
      return pageMode === "edit";
    },
    selectedActivities() {
      return this.poi.activities.map(item => item.activity);
    },
    hasTopology() {
      return this.topology && this.topology.serialized;
    },
    hasSteps() {
      return this.poi.steps.length > 0;
    },
    selectedCategory() {
      let cat = this.categories.find(item => item.id == this.poi.category);
      if (cat) {
        return cat;
      } else if (this.categories.length > 0) {
        return this.categories[0];
      }
      return {};
    },
    typeChoices() {
      if (this.selectedCategory.types) {
        return this.selectedCategory.types;
      }
      return [];
    },
    selectedType() {
      const type = this.typeChoices.find(
        item => item.id == this.poi.type
      );
      return type ? type : {};
    }
  },
  methods: {
    ...mapUtils,
    ...mapDrawMethods,
    ...highlightMethods,
    ...poiMethods,
    initMap() {
      const config = {
        center: [50.13466432216696, -72.72949218750001],
        zoom: 10,
        zoomControl: true,
        zoomAnimation: true,
        minZoom: 3,
        maxZoom: 17,
        scrollWheelZoom: true,
        fullscreenControl: true,
        fullscreenControlOptions: {
          position: "topleft"
        }
      };

      this.map = L.map("map", config);
      this.setAttribution();
      this.map.on("zoomend", e => {
        this.updateAttribution();
      });
      this.fitToLocations(true);
      this.resultLayers = L.geoJson().addTo(this.map);
      this.selectionLayers = L.geoJson().addTo(this.map);
      this.highlightLayers = L.geoJson().addTo(this.map);
      this.setupDrawControl();
    },
    openDeletePopup(marker) {
      const content = `
        <button id="btn-remove" class="mt-2 btn btn-danger btn-sm">Remove</button>
      `;
      const popup = L.popup({
        offset: new L.point(0, -36)
      })
        .setLatLng(marker.getLatLng())
        .setContent(content)
        .openOn(this.map);
      const btnRemove = L.DomUtil.get("btn-remove");
      L.DomEvent.on(btnRemove, "click", e => {
        this.map.closePopup();
        this.map.removeLayer(marker);
        this.poiMarker = null;
        this.map.addControl(this.drawControl);
      });
    },
    setPoiPopup(latlng) {
      this.map.closePopup();
      const popup = L.popup({
        offset: new L.point(0, -36)
      })
        .setLatLng(latlng)
        .setContent(this.getPopupContent(latlng, true))
        .openOn(this.map);
    },
    addMarker(latlng) {
      this.map.closePopup();
      this.poiMarker = L.marker(latlng, {
        draggable: true,
        icon: L.icon({
          iconSize: [41, 41],
          iconAnchor: [20, 41], // Tip of the icon (geographical location) relative to it's top left corner
          iconUrl: "/static/img/markers/Icones_Hikster_" + this.poi.type + ".svg"
        })
      });
      this.map.addLayer(this.poiMarker);
      this.map.removeControl(this.drawControl);
      this.setPoiPopup(latlng);
      this.poiMarker.on("dragstart dragend", e => {
        if (e.type == "dragstart") {
          this.map.closePopup();
        } else {
          this.setPoiPopup(this.poiMarker.getLatLng());
        }
      });
      this.poiMarker.on("click", e => {
        this.openDeletePopup(this.poiMarker);
      });
    },
    getPopupContent(latlng, hideBtn) {
      let info = "";
      let buttons = `
          <div class="col-12 d-flex justify-content-center">
            <button id="btn-add" class="mx-1 btn btn-success btn-sm">Add</button>
            <button id="btn-cancel" class="mx-1 btn btn-danger btn-sm">Close</button>
          </div>
      `;
      if (hideBtn) {
        buttons = "";
        info = `
              <li class="list-group-item"><strong>Name:</strong>
                ${this.poi.name || ""}
              </li>
              <li class="list-group-item"><strong>Category:</strong>
                ${this.selectedCategory.name}
              </li>
              <li class="list-group-item"><strong>Type:</strong>
                ${this.selectedType.name || ""}
              </li>
        `;
      }
      const content = `
        <div class="row">
          <div class="col-12">
            <ul class="list-group list-group-flush">
              ${info}
              <li class="list-group-item"><strong>Lat:</strong>
                ${latlng.lat}
              </li>
              <li class="list-group-item"><strong>Lng:</strong>
                ${latlng.lng}
              </li>
            </ul>
          </div>
          ${buttons}
        </div>
      `;
      return content;
    },
    openPopup(latlng) {
      const popup = L.popup()
        .setLatLng(latlng)
        .setContent(this.getPopupContent(latlng))
        .openOn(this.map);

      const btnAdd = L.DomUtil.get("btn-add");
      const btnCancel = L.DomUtil.get("btn-cancel");

      L.DomEvent.on(btnAdd, "click", e => {
        this.addMarker(latlng);
      });

      L.DomEvent.on(btnCancel, "click", e => {
        this.map.closePopup();
      });
    },
    setupDrawControl() {
      L.drawLocal.draw.toolbar.buttons.marker = "POI";
      L.drawLocal.draw.toolbar.actions = {
        title: "Finish",
        text: "Finish"
      };

      this.drawControl = new L.Control.Draw({
        draw: {
          polyline: false,
          polygon: false,
          rectangle: false,
          circle: false,
          circlemarker: false,
          marker: true
        }
      });
      this.map.addControl(this.drawControl);
      this.map.on(L.Draw.Event.CREATED, e => {
        this.openPopup(e.layer.getLatLng());
      });
      this.map.on("draw:drawstart", e => {
        if (!this.poi.type) {
          alert("Set type first.")
          this.drawControl._toolbars.draw.disable();
        }
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
    addContact() {
      this.poi.contact.push({
        id: 0,
        type: null,
        value: ""
      });
    },
    removeContact(idx) {
      this.poi.contact.splice(idx, 1);
    },
    addImage() {
      this.poi.images.push({
        credit: ""
      });
    },
    removeImage(idx) {
      this.poi.images.splice(idx, 1);
    },
    setAsBanner(newBanner) {
      this.$set(newBanner, "randomId", getRandomString());
      this.poi.images.forEach((item, idx) => {
        if (item.randomId == newBanner.randomId) {
          this.$set(item, "image_type", "banner");
        } else {
          this.$set(item, "image_type", "photo");
        }
        this.$set(this.poi.images, idx, item);
      });
    },
    uploadImage(event, item) {
      this.addImage();
      delete item.id;
      item.image_file = event.target.files[0];
      item.image_type = "photo";

      if (!this.isEditMode) {
        item.image = window.URL.createObjectURL(item.image_file);
      }
      const formData = jsonToFormData(item);

      if (this.isEditMode) {
        const url = `/admin/api/point-of-interests/${
          this.poi.poi_id
        }/upload-image/`;
        item.randomId = getRandomString();
        axios
          .post(url, formData, {
            headers: {
              "Content-Type": "multipart/form-data"
            }
          })
          .then(res => {
            const idx = this.poi.images.findIndex(
              im => im.randomId === item.randomId
            );
            this.$set(this.poi.images, idx, res.data);
          })
          .catch(error => {
            console.log(error.response.data);
          });
      } else {
        this.imagesForm.push(formData);
      }
    },
    saveImages(poiId, redirect) {
      const url = `/admin/api/point-of-interests/${poiId}/upload-image/`;
      const requests = [];

      this.imagesForm.forEach((item, idx) => {
        const image = this.poi.images[idx];
        item.append("credit", image.credit);
        item.append("image_type", image.image_type);
        requests.push(
          axios.post(url, item, {
            headers: {
              "Content-Type": "multipart/form-data"
            }
          })
        );
      });

      axios.all(requests).finally(() => {
        if (this.addNew) {
          window.location.href = "../new/";
        } else if (redirect) {
          window.location.href = "../";
        } else {
          window.history.pushState({}, document.title, `../${poiId}/`);
          this.successMessage = "Poi saved successfully.";
        }
      });
    },
    save(redirect, addNew) {
      this.addNew = addNew;
      this.successMessage = "";
      this.errors = {};
      this.loading = true;
      if (!this.poiMarker) {
        this.errors.shape = "Please provide a valid marker";
        window.scrollTo({ top: 0, behavior: "smooth" });
        this.loading = false;
        return;
      }
      const newImages = [];
      const contacts = this.poi.contact.filter(
        item => item.type && item.value.trim()
      );
      this.$set(this.poi, "contact", contacts);

      this.poi.images.forEach((item, idx) => {
        if (idx + 1 < this.poi.images.length) {
          delete item.image_file;
          if (!item.image_type) {
            item.image_type = "photo";
          }
          newImages.push(item);
        }
      });
      this.$set(this.poi, "images", newImages);

      if (this.poiMarker) {
        this.$set(this.poi, "shape", this.poiMarker.toGeoJSON().geometry);
      } else {
        this.$set(this.poi, "shape", null);
      }

      const data = { ...this.poi };
      let url = "/admin/api/point-of-interests/";
      let method = "post";

      if (this.isEditMode) {
        url = `${url}${this.poi.poi_id}/`;
        method = "patch";
      } else {
        delete data.images;
      }

      axios({
        method: method,
        url: url,
        data: data
      })
        .then(res => {
          if (!this.isEditMode) {
            this.saveImages(res.data.poi_id, redirect);
          } else {
            if (this.addNew) {
              window.location.href = "../new/";
            } else if (redirect) {
              window.location.href = "../";
            } else {
              $("li.breadcrumb-item")
                .last()
                .text(this.poi.name);
              this.successMessage = "Poi saved successfully.";
            }
          }
        })
        .catch(error => {
          this.errors = error.response.data;
        })
        .finally(() => {
          this.addImage();
          this.loading = false;
          window.scrollTo({ top: 0, behavior: "smooth" });
        });
    }
  }
});
