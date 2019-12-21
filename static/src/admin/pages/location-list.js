import "@babel/polyfill";
import Vue from "@/vue.js";

import "@/components/icons/hk-globe.js";
import "@/components/icons/hk-sort-icon.js";
import { orderBy } from "@/utils.js";
import { mapData } from "@/map/data.js";
import { mapMethods } from "@/map/methods.js";
import { networkMethods } from "@/map/networkMethods.js";

new Vue({
  el: "#location-list",
  data() {
    return {
      ...mapData,
      locations: [],
      headerNames: headerNames,
      selectedLocationInMap: null,
      sortBy: {
        key: "name",
        ascending: false
      }
    };
  },
  mounted() {
    this.setInitialData();
    this.geoJSON = this.getGeojsonData("geojson-data");
    this.locations = this.getJsonData("locations-data");
    console.log(this.locations)
    this.locations = this.locations.map(item => {
      item.modified_date = new Date(item.modified_date);
      return item;
    });
    this.poiCategories = this.getJsonData("poi-categories-data");
    this.sport = defaultSport;
    this.initMap();
    this.selectNetwork(this.geoJSON);
    this.sortData("name");
  },
  filters: {
    dateFormat(value) {
      const date = new Date(value);
      const month = date.getMonth() + 1;
      return `${date.getDate()}/${month}/${date.getFullYear()}`;
    }
  },
  methods: {
    ...mapMethods,
    ...networkMethods,
    sortData(sortKey) {
      this.$set(this.sortBy, "ascending", !this.sortBy.ascending);
      const method = this.sortBy.ascending ? "asc" : "desc";
      this.locations = orderBy(this.locations, sortKey, method);
      this.$set(this.sortBy, "key", sortKey);
    },
    getRowClass(locationId) {
      return {
        selected: locationId === Number.parseInt(this.selectedLocationInMap)
      };
    },
    highlightLocation(locationId) {
      const geoJSON = this.geoJSON.features.find(item => {
        return Number.parseInt(item.properties.pk) == locationId;
      });
      this.highlightTrails({
        trailLayers: [this.geoJSONToTrailLayer(geoJSON)],
        popup: false
      });
    }
  }
});
