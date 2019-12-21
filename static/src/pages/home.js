import "@babel/polyfill";
import Vue from "vue";

import { searchMethods } from "@/search/methods.js";

Vue.options.delimiters = ["{[", "]}"];

new Vue({
  el: "#search-component",
  data() {
    return {
      searchTimeout: null,
      searchTerm: "",
      suggestions: [],
      regions: [],
      activities: [],
      selectedRegion: {},
      selectedActivity: {},
      withDog: false,
      showRegions: false,
      showActivities: false
    };
  },
  mounted() {
    $("#loading-mask").fadeOut();
    $("body").removeClass("no-scroll");
    this.regions = JSON.parse(
      document.getElementById("regions-data").textContent
    );
    this.activities = JSON.parse(
      document.getElementById("activities-data").textContent
    );
    this.selectedActivity = this.activities[0];
  },
  methods: {
    ...searchMethods,
    toggleShowRegions() {
      this.showRegions = !this.showRegions;
    },
    toggleShowActivities() {
      this.showActivities = !this.showActivities;
    },
    selectLocation(item) {
      if (item.type === "trail") {
        window.open(item.url, "_blank");
      } else {
        this.searchTerm = item.name;
        this.locationId = item.url.split("=")[1];
        this.suggestions = [];
      }
    },
    selectRegion(region) {
      this.selectedRegion = region;
      this.locationId = region.location_id;
      this.searchTerm = region.name;
      this.toggleShowRegions();
    },
    selectActivity(activity) {
      this.selectedActivity = activity;
      this.toggleShowActivities();
    },
    showResultsPage() {
      let query = {};

      if (this.searchTerm) {
        query.search_term = this.searchTerm;
      }

      if (this.selectedActivity.id) {
        query.activities = this.selectedActivity.id;
      }

      if (this.withDog) {
        query.dog_allowed = 1;
      }

      if (this.locationId) {
        query.loc = this.locationId;
      }

      window.location.href = "/results/?".concat(this.getQueryString(query));
    },
    debounceSearch(val) {
      this.selectedLocation = {};
      this.locationId = null;
      this.searchTerm = val;
      if (this.searchTimeout) clearTimeout(this.searchTimeout);
      this.searchTimeout = setTimeout(() => {
        this.fetchSuggestions();
      }, 400);
    }
  }
});
