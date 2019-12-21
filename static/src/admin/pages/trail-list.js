import "@babel/polyfill";
import Vue from "@/vue.js";
import axios from "axios";

import "@/components/icons/hk-globe.js";
import "@/components/icons/hk-sort-icon.js";
import { orderBy } from "@/utils.js";
import { mapData } from "@/map/data.js";
import { mapMethods } from "@/map/methods.js";
import { networkMethods } from "@/map/networkMethods.js";

axios.defaults.xsrfHeaderName = "X-CSRFToken";
axios.defaults.withCredentials = true;

new Vue({
  el: "#trail-list-component",
  data() {
    return {
      ...mapData,
      loading: true,
      deleting: false,
      activities: [],
      locations: [],
      selectedLocation: {},
      selectedActivity: {},
      trails: [],
      selectedTrailInMap: null,
      sortBy: {
        key: "name",
        ascending: false
      }
    };
  },
  mounted() {
    this.setInitialData();
    // TODO:
    this.geoJSON = this.getGeojsonData("geojson-data");
    this.activities = this.getJsonData("activities-data");
    this.selectedActivity = this.getJsonData("selected-activity-data");
    this.locations = this.getJsonData("locations-data");
    this.selectedLocation = this.getJsonData("selected-location-data");
    this.poiCategories = this.getJsonData("poi-categories-data");
    this.sport = defaultSport;

    this.setTrails(this.getJsonData("trails-data"));
    this.initMap();
    this.selectNetwork(this.geoJSON);
    this.sortData("name");
    this.loading = false;
    $("#scrollable-container").removeClass("d-none");
  },
  filters: {
    dateFormat(value) {
      const date = new Date(value);
      const month = date.getMonth() + 1;
      return `${date.getDate()}/${month}/${date.getFullYear()}`;
    }
  },
  computed: {
    hasTrails() {
      return this.trails.length > 0;
    },
    hasSelected() {
      return this.trails.find(item => item.selected);
    },
    activityChoices() {
      return this.activities.filter(
        item => item.id != this.selectedActivity.id
      );
    },
    locationChoices() {
      return this.locations.filter(
        item => item.location_id != this.selectedLocation.location_id
      );
    }
  },
  methods: {
    ...mapMethods,
    ...networkMethods,
    setTrails(trails) {
      this.trails = trails;
      this.trails = this.trails.map(item => {
        item.last_modified = new Date(item.last_modified);
        return item;
      });
    },
    updateFilter() {
      this.loading = true;
      const query = {};
      const locId = this.selectedLocation.location_id;
      const activity = this.selectedActivity.id;
      if (locId != -1) {
        query.loc = locId;
      }
      if (activity != -1) {
        query.activity = activity;
      }
      const queryString = Object.keys(query)
        .map(key => key + "=" + query[key])
        .join("&");

      let url = window.location.href.split("?")[0];
      if (queryString) {
        url += `?${queryString}`;
      }
      window.history.pushState({}, document.title, url);
      axios({
        method: "get",
        url: url,
        headers: { "X-Requested-With": "XMLHttpRequest" }
      })
        .then(response => {
          const geojson = response.data.geo_json;
          this.setTrails(response.data.trails);

          if (geojson != "") {
            this.geoJSON = JSON.parse(geojson);
            this.selectNetwork(this.geoJSON);
          }
        })
        .catch(error => {
          console.log(error);
        })
        .finally(() => {
          this.loading = false;
        });
    },
    selectLocation(location) {
      this.selectedLocation = location;
      this.updateFilter();
    },
    selectActivity(activity) {
      this.selectedActivity = activity;
      this.updateFilter();
    },
    sortData(sortKey) {
      this.$set(this.sortBy, "ascending", !this.sortBy.ascending);
      const method = this.sortBy.ascending ? "asc" : "desc";
      this.trails = orderBy(this.trails, sortKey, method);
      this.$set(this.sortBy, "key", sortKey);
    },
    getRowClass(trailId) {
      return {
        "secton-row": true,
        row: true,
        "py-2": true,
        selected: trailId === Number.parseInt(this.selectedTrailInMap)
      };
    },
    deleteTrails() {
      this.loading = true;
      const ids = this.trails
        .filter(item => item.selected)
        .map(item => item.trail_id);
      axios
        .delete("/admin/api/trails/bulk-delete/?ids=" + ids.join(","))
        .then(response => {
          this.trails = this.trails.filter(item => !item.selected);
        })
        .catch(err => {
          console.log(err);
        })
        .finally(() => {
          this.loading = false;
        });
    },
    highlightTrail(trailId) {
      const geoJSON = this.geoJSON.features.find(item => {
        return Number.parseInt(item.properties.pk) == trailId;
      });
      if (geoJSON && geoJSON.geometry) {
        this.highlightTrails({
          trailLayers: [this.geoJSONToTrailLayer(geoJSON)],
          popup: false
        });
      }
    },
    scrollToTrail(trailId) {
      $("#scrollable-content").animate({
        scrollTop:
          $("#scrollable-content").scrollTop() +
          ($(`#trail-${trailId}`).offset().top -
            $("#scrollable-content").offset().top)
      });
    }
  }
});
