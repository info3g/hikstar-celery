import Vue from "@/vue.js";

import { MapHikster, mapData } from "@/map/data.js";
import { mapMethods } from "@/map/methods.js";
import { networkMethods } from "@/map/networkMethods.js";

new Vue({
  el: "#map",
  data: {
    ...mapData,
    visiblePois: [],
    geoJSON: {},
    trailLocation: {}
  },
  mounted() {
    this.setInitialData();
    if (!this.isPoiPage()) {
      this.geoJSON = JSON.parse(
        JSON.parse(document.getElementById("geojson-data").textContent)
      );
      this.poiCategories = this.getJsonData("poi-categories-data");
    }
    this.sport = defaultSport;
    this.initMap();

    if (this.isTrailPage()) {
      this.trailLocation = this.getJsonData("trail-location-data");
      this.poiCategories = this.getJsonData("poi-categories-data");
      this.selectTrails({
        trailLayers: [this.geoJSONToTrailLayer(this.geoJSON["features"][0])],
        zoomType: MapHikster.ZOOM_FITBOUNDS
      });
      this.addElevation();
    } else if (this.isLocationPage()) {
      const trailsJSON = JSON.parse(
        JSON.parse(document.getElementById("trails-json-data").textContent)
      );
      this.selectNetwork(trailsJSON);
      this.poiCategories = this.getJsonData("poi-categories-data");
    } else if (this.isAdminLocationListPage()) {
      this.selectNetwork(this.geoJSON);
    } else if (this.isPoiPage()) {
      const poi = this.getJsonData("poi-data");
      if (poi.shape) {
        const coords = poi.shape.coordinates;
        if (coords.length > 1) {
          const latlng = new L.LatLng(coords[1], coords[0]);
          const poiMarker = L.marker(latlng, {
            draggable: true,
            icon: L.icon({
              iconSize: [41, 41],
              iconAnchor: [20, 41], // Tip of the icon (geographical location) relative to it's top left corner
              iconUrl: "/static/img/markers/Icones_Hikster_" + poi.type + ".svg"
            })
          });
          this.map.addLayer(poiMarker);
          this.map.fitBounds(
            L.geoJSON(poi.shape)
              .getBounds()
              .pad(0.25)
          );
        }
      }
    }
  },
  methods: {
    ...mapMethods,
    ...networkMethods,
    addElevation() {
      const el = L.control.elevation({
        position: "bottomright"
      });
      el.addTo(this.map);

      const trail = L.geoJson(this.geoJSON, {
        onEachFeature: el.addData.bind(el) //working on a better solution
      }).addTo(this.map);
      trail.setStyle(this.selectedTrailStyle);
    }
  }
});
