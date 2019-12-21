import "@babel/polyfill";

import Vue from "@/vue.js";
import CKEditor from "@ckeditor/ckeditor5-vue";
import axios from "axios";

import "@/components/icons/hk-plus.js";
import "@/components/icons/hk-times.js";
import Geotrek from "@/map/dijkstra.js";
import { pathMethods } from "@/map/path.js";
import { mapUtils } from "@/map/utils.js";
import { MapHikster } from "@/map/data.js";
import { mapMethods } from "@/map/methods.js";
import { networkMethods } from "@/map/networkMethods.js";
import { mapDrawData, mapDrawMethods } from "@/map/draw.js";
import { isObject, jsonToFormData, getRandomString, orderBy } from "@/utils.js";
import { ckeditorConfig } from "@/ckeditor/config.js";

axios.defaults.xsrfHeaderName = "X-CSRFToken";
axios.defaults.withCredentials = true;

Vue.use(CKEditor);

new Vue({
  el: "#trail-detail-component",
  data: {
    ...mapDrawData,
    ...ckeditorConfig,
    trailDescription: "",
    drawControl: null,
    trailShapeGeojson: {},
    graph: {},
    errors: {},
    loading: false,
    map: null,
    attribution: "",
    locations: [],
    activities: [],
    pathTypes: [],
    trail: {
      activities: [],
      images: [],
      events: [],
      steps: []
    },
    markers: [],
    imagesForm: [],
    steps: [],
    geotrek: Geotrek,
    guideLayers: null,
    markerId: 0,
    hasStartMarker: false,
    hasEndMarker: false,
    pathLayer: null,
    trailPath: null,
    startMarker: null,
    endMarker: null,
    guideStyle: {
      color: MapHikster.LIGHT_GREEN,
      weight: 3,
      opacity: 1
    },
    dragging: false,
    computedPaths: null,
    topology: null,
    successMessage: "",
    shapeChanged: false,
    sectionLayers: null,
    trailSectionsGeojson: null
  },
  mounted() {
    $(".alert").removeClass("d-none");
    this.graph = this.getJsonData("graph_data");
    this.locations = this.getJsonData("locations_data");
    this.activities = this.getJsonData("activities_data");
    this.pathTypes = this.getJsonData("path_types_data");
    this.trailSectionsGeojson = this.getGeojsonData("trail_sections_geojson");
    if (this.isEditMode) {
      this.trailShapeGeojson = this.getGeojsonData("trail_shape_geojson");
      this.trail = this.getJsonData("trail_data");
      this.markers = this.getJsonData("markers_data");
      this.activities.forEach(item => {
        if (this.selectedActivities.includes(item.id)) {
          item.selected = true;
        }
      });
    }
    this.addImage();
    this.initMap();
  },
  computed: {
    orderedImages() {
      return orderBy(this.trail.images, "image_type");
    },
    isEditMode() {
      return pageMode === "edit";
    },
    selectedActivities() {
      return this.trail.activities.map(item => item.activity);
    },
    hasTopology() {
      return this.topology && this.topology.serialized;
    },
    hasSteps() {
      return this.trail.steps.length > 0;
    }
  },
  methods: {
    ...mapUtils,
    ...mapDrawMethods,
    ...pathMethods,

    // Extract the complete edges list from the first to the last one
    extractAllEdges: function(computed_paths) {
      if (!computed_paths) return [];

      var edges = $.map(computed_paths, function(cpath) {
        var dups = $.map(cpath.path, function(path_component) {
          return path_component.real_edge || path_component.edge;
        });

        // Remove adjacent duplicates
        var dedup = [];
        for (var i = 0; i < dups.length; i++) {
          var e = dups[i];
          if (i === 0) dedup.push(e);
          else if (dups[i - 1].id != e.id) dedup.push(e);
        }
        return [dedup];
      });

      return edges;
    },
    // Extract the complete edges list from the first to the last one
    _extractAllEdges: function(computedPaths) {
      if (!computedPaths) return [];

      const edges = computedPaths.map(cpath => {
        const dups = cpath.path.map(path_component => {
          return path_component.real_edge || path_component.edge;
        });

        // Remove adjacent duplicates
        const dedup = [];
        for (var i = 0; i < dups.length; i++) {
          const e = dups[i];
          if (i === 0) dedup.push(e);
          else if (dups[i - 1].id != e.id) dedup.push(e);
        }
        return [dedup];
      });

      return edges;
    },
    _onComputedPaths(newComputedPaths) {
      const oldComputedPaths = this.computedPaths;
      this.computedPaths = newComputedPaths;

      // compute and store all edges of the new paths (usefull for further computation)
      this.allEdges = this._extractAllEdges(newComputedPaths);

      this.onComputedPaths({
        computed_paths: newComputedPaths,
        new_edges: this.allEdges,
        old: oldComputedPaths
      });
    },
    getMarkerIcon(type) {
      return L.icon({
        iconUrl: `/static/img/map/marker-${type}.png`,
        iconSize: [40, 40],
        iconAnchor: [20, 40]
      });
    },
    addMarker(latlng, type) {
      const marker = L.marker(latlng, {
        icon: this.getMarkerIcon(type),
        draggable: true
      }).addTo(this.map);
      marker.id = this.markerId;
      marker.type = type;
      this.markerId += 1;
      this.map.closePopup();

      let origLatLng = null;
      marker.on("dragstart dragend", e => {
        if (e.type == "dragstart") {
          this.dragging = true;
          origLatLng = marker.getLatLng();
        } else {
          const latlng = marker.getLatLng();
          const closest = this.getClosest(latlng);
          if (closest && closest.layer) {
            marker.setLatLng(closest.latlng);
            const idx = this.steps.findIndex(
              item => item.marker.id == marker.id
            );
            if (this.setPolData(closest, latlng)) {
              this.createStep(marker, idx, true);
            } else {
              marker.setLatLng(origLatLng);
            }
          } else {
            marker.setLatLng(origLatLng);
          }
          this.dragging = false;
        }
      });
      marker.on("click", e => {
        this.openDeletePopup(marker);
      });
      if (type == "start") {
        this.hasStartMarker = true;
      } else if (type == "end") {
        this.hasEndMarker = true;
      }
      this.createStep(marker, this.steps.length);
    },
    setPolData(closest, origLatLng) {
      this.origLatLng = origLatLng;
      this.ll = closest.latlng;
      this.polyline = closest.layer;
      this.pathLength = L.GeometryUtil.length(this.polyline);
      try {
        this.percentDistance = L.GeometryUtil.locateOnLine(
          this.polyline._map,
          this.polyline,
          this.ll
        );
        return true;
      } catch (e) {
        console.log(e);
        return false;
      }
    },
    createStep(marker, idx, update = false) {
      const step = new this.geotrek.PointOnPolyline({
        marker: marker,
        origLatLng: this.origLatLng,
        ll: this.ll,
        polyline: this.polyline,
        path_length: this.pathLength,
        percent_distance: this.percentDistance
      });
      if (update) {
        this.$set(this.steps, idx, step);
      } else if (marker.type == "start") {
        this.steps.splice(0, 0, step);
      } else if (marker.type == "step" && this.hasEndMarker) {
        // This happens when there is already an end marker
        // and the user inserts a step
        this.steps.splice(idx - 1, 0, step);
      } else {
        this.steps.splice(idx, 0, step);
      }
      this.computePaths();
    },
    computePaths() {
      if (this.steps.length > 1) {
        const computedPaths = this.geotrek.shortestPath(this.graph, this.steps);
        this._onComputedPaths(computedPaths);
      } else {
        this.topology = null;
        if (this.pathLayer) {
          this.map.removeLayer(this.pathLayer);
          this.pathLayer = null;
        }
      }
    },
    idToLayer(id) {
      return this.guideLayers
        .getLayers()
        .find(
          item =>
            Number.parseInt(item.feature.properties.pk) == Number.parseInt(id)
        );
    },
    openDeletePopup(marker) {
      const content = `
        <button id="btn-remove" class="mt-2 btn btn-danger btn-sm">Remove</button>
      `;
      const popup = L.popup()
        .setLatLng(marker.getLatLng())
        .setContent(content)
        .openOn(this.map);
      const btnRemove = L.DomUtil.get("btn-remove");
      L.DomEvent.on(btnRemove, "click", e => {
        const idx = this.steps.findIndex(item => item.marker.id == marker.id);
        if (marker.type == "start") {
          this.hasStartMarker = false;
        } else if (marker.type == "end") {
          this.hasEndMarker = false;
        }
        this.map.removeLayer(marker);
        this.map.closePopup();
        this.steps.splice(idx, 1);
        this.computePaths();
      });
    },
    openPopup(feature, latlng) {
      let disableStart = "";
      let disableEnd = "";

      if (this.hasStartMarker) {
        disableStart = "disabled";
      }
      if (this.hasEndMarker) {
        disableEnd = "disabled";
      }
      const content = `
        <div class="row">
          <div class="col-12">
            <ul class="list-group list-group-flush">
              <li class="list-group-item"><strong>Lat:</strong> ${
                latlng.lat
              }</li>
              <li class="list-group-item"><strong>Lng:</strong> ${
                latlng.lng
              }</li>
              <li class="list-group-item"><strong>Path:</strong> ${
                feature.properties.name
              }</li>
            </ul>
          </div>
          <div class="col-12 d-flex justify-content-center">
            <button ${disableStart} id="btn-start" class="mx-1 btn btn-success btn-sm">Start</button>
            <button id="btn-step" class="mx-1 btn btn-primary btn-sm">Step</button>
            <button ${disableEnd} id="btn-end" class="mx-1 btn btn-danger btn-sm">End</button>
          </div>
        </div>
      `;
      const popup = L.popup()
        .setLatLng(latlng)
        .setContent(content)
        .openOn(this.map);

      const btnStart = L.DomUtil.get("btn-start");
      const btnStep = L.DomUtil.get("btn-step");
      const btnEnd = L.DomUtil.get("btn-end");

      L.DomEvent.on(btnStart, "click", e => {
        this.addMarker(latlng, "start");
      });

      L.DomEvent.on(btnStep, "click", e => {
        this.addMarker(latlng, "step");
      });

      L.DomEvent.on(btnEnd, "click", e => {
        this.addMarker(latlng, "end");
        this.drawControl._toolbars.draw.disable();
      });
    },
    initMap() {
      const config = {
        center: [50.13466432216696, -72.72949218750001],
        zoom: 5,
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

      if (this.hasSteps) {
        config.zoom = 14;
      }

      this.map = L.map("map", config);
      this.setAttribution();
      this.map.on("zoomend", e => {
        this.updateAttribution();
      });

      this.guideLayers = L.geoJson().addTo(this.map);
      this.guideLayers = L.geoJson(this.trailSectionsGeojson, {
        style: this.guideStyle
      }).addTo(this.map);

      if (this.isEditMode && this.trailShapeGeojson.features[0].geometry) {
        if (this.trail.steps.length > 0) {
          this.showTrailPath();
          if (this.pathLayer) {
            this.map.fitBounds(this.pathLayer.getBounds(), { animate: true });
          }
        } else {
          this.showTrailPathWithoutSteps();
        }
      } else {
        this.map.fitBounds(this.guideLayers.getBounds().pad(0.25), {
          animate: true
        });
      }
      this.setupDrawControl();
    },
    setupDrawControl() {
      L.drawLocal.draw.toolbar.buttons.marker = "Route";
      L.drawLocal.draw.handlers.marker = {
        tooltip: {
          start: "Click near the trail"
        }
      };
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
          marker: {
            repeatMode: true
          }
        }
      });
      this.map.addControl(this.drawControl);
      this.map.on(L.Draw.Event.CREATED, e => {
        const layer = e.layer;
        const origLatLng = layer.getLatLng();
        const closest = this.getClosest(origLatLng);
        if (closest && closest.layer) {
          if (this.setPolData(closest, origLatLng)) {
            this.openPopup(closest.layer.feature, closest.latlng);
          }
        }
      });
      if (this.isEditMode && this.trail.steps.length == 0) {
        this.map.on("draw:drawstart", e => {
          this.shapeChanged = true;
          if (this.trailPath) {
            this.map.removeLayer(this.trailPath);
          }
          if (this.startMarker) {
            this.map.removeLayer(this.startMarker);
          }
          if (this.endMarker) {
            this.map.removeLayer(this.endMarker);
          }
        });
      }
    },
    showTrailPath() {
      let markerType = "start";
      const steps = this.trail.steps;
      const stepCount = steps.length;
      steps.forEach((step, idx) => {
        if (idx + 1 == stepCount) {
          markerType = "end";
        } else if (idx > 0) {
          markerType = "step";
        }
        // const coords = step.point.coordinates;
        // const latlng = L.latLng([coords[1], coords[0]]);
        const latlng = L.latLng(Number(step.lat), Number(step.lng));
        const closest = this.getClosest(latlng);
        if (closest && closest.layer) {
          if (this.setPolData(closest, latlng)) {
            this.addMarker(closest.latlng, markerType);
          }
        }
      });
    },
    showTrailPathWithoutSteps() {
      this.trailPath = L.geoJson(this.trailShapeGeojson, {
        style: {
          color: "yellow",
          weight: 5,
          opacity: 0.8
        }
      });
      this.map.addLayer(this.trailPath);
      this.map.fitBounds(this.trailPath.getBounds().pad(0.25), {
        animate: true
      });
      const layer = this.trailPath.getLayers()[0];
      const latlngs = layer.getLatLngs();

      if (!Array.isArray(latlngs[0])) {
        this.startMarker = L.marker(latlngs[0], {
          icon: this.getMarkerIcon("start")
        }).addTo(this.map);
        this.endMarker = L.marker(latlngs[latlngs.length - 1], {
          icon: this.getMarkerIcon("end")
        }).addTo(this.map);
      }
      if (layer) {
        if (typeof layer.setText == "function") {
          layer.setText(">  ", {
            repeat: true,
            attributes: { fill: "#FF5E00" }
          });
        }
      }
    },
    getClosest(latlng) {
      const closest = L.GeometryUtil.closestLayerSnap(
        this.map,
        this.guideLayers.getLayers(),
        latlng,
        null,
        true
      );
      if (!closest) {
        return null;
      }
      const point = turf.helpers.point([
        closest.latlng.lng,
        closest.latlng.lat
      ]);
      const nearest = turf.nearestPointOnLine(closest.layer.feature, point);
      if (!nearest) {
        return null;
      }
      const coords = nearest.geometry.coordinates;
      closest.latlng = L.latLng(coords[1], coords[0]);
      return closest;
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
    addImage() {
      this.trail.images.push({
        credit: ""
      });
    },
    removeImage(idx) {
      this.trail.images.splice(idx, 1);
    },
    setAsBanner(newBanner) {
      this.$set(newBanner, "randomId", getRandomString());
      this.trail.images.forEach((item, idx) => {
        if (item.randomId == newBanner.randomId) {
          this.$set(item, "image_type", "banner");
        } else {
          this.$set(item, "image_type", "photo");
        }
        this.$set(this.trail.images, idx, item);
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
        const url = `/admin/api/trails/${this.trail.trail_id}/upload-image/`;
        item.randomId = getRandomString();
        axios
          .post(url, formData, {
            headers: {
              "Content-Type": "multipart/form-data"
            }
          })
          .then(res => {
            const idx = this.trail.images.findIndex(
              im => im.randomId === item.randomId
            );
            this.$set(this.trail.images, idx, res.data);
          })
          .catch(error => {
            console.log(error.response.data);
          });
      } else {
        this.imagesForm.push(formData);
      }
    },
    saveImages(trailId, redirect) {
      const url = `/admin/api/trails/${trailId}/upload-image/`;
      const requests = [];

      this.imagesForm.forEach((item, idx) => {
        const image = this.trail.images[idx];
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
        if (redirect) {
          window.location.href = "../";
        } else {
          window.history.pushState({}, document.title, `../${trailId}/`);
          this.successMessage = "Trail saved successfully.";
        }
      });
    },
    getSteps() {
      return this.steps.map((step, idx) => {
        return {
          lat: step.origLatLng.lat,
          lng: step.origLatLng.lng,
          point: step.marker.toGeoJSON().geometry,
          order: idx + 1
        };
      });
    },
    save(redirect) {
      this.successMessage = "";
      this.errors = {};
      this.loading = true;
      const newActivities = [];
      const newImages = [];

      this.$set(this.trail, "steps", this.getSteps());

      if (!this.hasTopology) {
        if (this.hasSteps || this.shapeChanged) {
          this.errors.shape_2d = "Trail shape is invalid.";
          this.loading = false;
          window.scrollTo({ top: 0, behavior: "smooth" });
          return;
        }
      }

      if (this.hasSteps || this.shapeChanged) {
        let order = 0;
        const events = [];
        for (const item of this.topology.serialized) {
          item.paths.forEach((path, idx) => {
            const pos = item.positions[idx];
            if (pos) {
              events.push({
                trailsection: path,
                start_position: pos[0],
                end_position: pos[1],
                order: order
              });
              order += 1;
            }
          });
        }
        this.$set(this.trail, "events", events);
      }

      this.activities.forEach(activity => {
        const selected = this.selectedActivities.find(
          item => item.activity === activity.id
        );
        if (activity.selected) {
          newActivities.push({
            id: selected ? selected.id : null,
            activity: activity.id
          });
        }
      });
      this.$set(this.trail, "activities", newActivities);

      this.trail.images.forEach((item, idx) => {
        if (idx + 1 < this.trail.images.length) {
          delete item.image_file;
          if (!item.image_type) {
            item.image_type = "photo";
          }
          newImages.push(item);
        }
      });
      this.$set(this.trail, "images", newImages);

      const data = { ...this.trail };
      delete data.shape;

      let url = "/admin/api/trails/";
      let method = "post";

      if (this.isEditMode) {
        url = `${url}${this.trail.trail_id}/`;
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
            pageMode = "edit";
            this.saveImages(res.data.trail_id, redirect);
          } else {
            if (redirect) {
              window.location.href = "../";
            } else {
              $("li.breadcrumb-item")
                .last()
                .text(this.trail.name);
              this.successMessage = "Trail saved successfully.";
            }
          }
        })
        .catch(error => {
          if (error.response.status === 500) {
            this.errors.shape_2d =
              "An error occurred. Please try again later or clear the shape and draw again.";
          } else {
            this.errors = error.response.data;
          }
        })
        .finally(() => {
          this.addImage();
          this.loading = false;
          window.scrollTo({ top: 0, behavior: "smooth" });
        });
    }
  }
});
