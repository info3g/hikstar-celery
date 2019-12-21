import "@babel/polyfill";
import Vue from "@/vue.js";
import axios from "axios";

import "@/components/icons/hk-sort-icon.js";
import { orderBy } from "@/utils.js";
import { MapHikster, mapData } from "@/map/data.js";
import { mapMethods } from "@/map/methods.js";
import { networkMethods } from "@/map/networkMethods.js";

axios.defaults.xsrfHeaderName = "X-CSRFToken";
axios.defaults.withCredentials = true;

new Vue({
  el: "#trail-section-list",
  data() {
    return {
      ...mapData,
      newActivities: [],
      selectedActivity: {},
      deleting: false,
      headerNames: headerNames,
      activities: [],
      trailSections: [],
      trailSectionLayer: null,
      selectedTrailSectionInMap: null,
      sortBy: {
        key: "name",
        ascending: false
      },
      showFilter: false,
      trailSectionsByActivity: {}
    };
  },
  computed: {
    validActivities() {
      return this.activities.filter(item => item.id > 0);
    },
    btnFilterCls() {
      return {
        btn: true,
        "btn-sm": true,
        "btn-outline-success": !this.showFilter,
        "btn-success": this.showFilter
      };
    },
    hasSelected() {
      return this.trailSections.find(item => item.selected);
    },
    selectedTrailSections() {
      return this.trailSectionsByActivity[this.selectedActivity.id].filter(
        item => item.selected
      );
    },
    filteredTrailSections() {
      const sections = this.trailSectionsByActivity[this.selectedActivity.id];
      if (!sections) {
        return [];
      }
      const method = this.sortBy.ascending ? "asc" : "desc";
      return orderBy(sections, this.sortBy.key, method);
    },
    filteredIds() {
      return this.filteredTrailSections.map(item => item.pk);
    },
    filteredGeoJSON() {
      const geojson = { ...this.geoJSON };
      const features = geojson.features.filter(item => {
        return this.filteredIds.includes(Number.parseInt(item.properties.pk));
      });
      this.$set(geojson, "features", features);
      return geojson;
    },
    hasTrailSections() {
      return this.filteredTrailSections.length > 0;
    },
    activityChoices() {
      return this.activities.filter(
        item => item.id != this.selectedActivity.id
      );
    }
  },
  mounted() {
    this.setInitialData();
    this.geoJSON = this.getGeojsonData("geojson-data");
    this.trailSections = this.getJsonData("trail-sections-data");
    const activities = [
      {
        id: -1,
        name: allLabel
      }
    ];
    this.activities = [...activities, ...this.getJsonData("activities-data")];
    this.selectedTrailStyle = {
      color: MapHikster.DARK_GREEN,
      weight: 3,
      opacity: 1
    };
    this.initMap();
    if (this.activities.length > 0) {
      this.setTrailSectionsByActivity();
      this.updateSelectedActivity(this.activities[0]);
    }
    this.setMapSections();
  },
  methods: {
    ...mapMethods,
    ...networkMethods,
    setTrailSectionsByActivity() {
      this.activities.forEach(item => {
        this.trailSectionsByActivity[item.id] = [];
      });
      this.trailSectionsByActivity[-1] = this.trailSections;
      this.trailSectionsByActivity[0] = [];
      this.trailSections.forEach(item => {
        if (item.activity_ids.length == 0) {
          this.trailSectionsByActivity[0].push(item);
        } else {
          item.activity_ids.forEach(id => {
            this.trailSectionsByActivity[id].push(item);
          });
        }
      });
    },
    updateSelectedActivity(activity) {
      this.selectedActivity = activity;
      this.sport = activity.id;
      this.setMapSections();
      // this.updateTrailLayer({ sport: this.sport });
    },
    setMapSections() {
      if (this.hasTrailSections) {
        this.selectNetwork(this.filteredGeoJSON);
      } else {
        this.selectionLayers.clearLayers();
        this.highlightLayers.clearLayers();
        this.trailPopup = null;
        this.fitToLocations();
      }
    },
    sortData(sortKey) {
      this.$set(this.sortBy, "ascending", !this.sortBy.ascending);
      this.$set(this.sortBy, "key", sortKey);
    },
    getRowClass(trailSectionId) {
      return {
        "secton-row": true,
        row: true,
        "py-2": true,
        selected:
          trailSectionId === Number.parseInt(this.selectedTrailSectionInMap)
      };
    },
    getSelectedIds() {
      const selected = this.trailSectionsByActivity[
        this.selectedActivity.id
      ].filter(item => item.selected);
      const activityIds = [-1];
      const ids = selected.map(item => item.trailsection_id);

      for (const section of selected) {
        for (const activityId of section.activity_ids) {
          if (activityIds.indexOf(activityId) < 0) {
            activityIds.push(activityId);
          }
        }
        ids.push(section.trailsection_id);
      }
      return ids;
    },
    showUpdateActivityModal() {
      this.newActivities = [];
      $("#update-activity-modal").modal("show");
    },
    updateActivities() {
      this.deleting = true;
      const ids = this.getSelectedIds();

      axios
        .post("/admin/api/trail-sections/bulk-update/?ids=" + ids.join(","), {
          activity_ids: this.newActivities.join(",")
        })
        .then(() => {
          location.reload();
        });
    },
    deleteTrailSections() {
      this.deleting = true;
      const ids = this.getSelectedIds();

      axios
        .delete("/admin/api/trail-sections/bulk-delete/?ids=" + ids.join(","))
        .then(() => {
          ids.forEach(id => {
            for (const activityId of activityIds) {
              const idx = this.trailSectionsByActivity[activityId].findIndex(
                t => t.trailsection_id == id
              );
              if (idx >= 0) {
                this.trailSectionsByActivity[activityId].splice(idx, 1);
              }
            }

            const idx = this.geoJSON.features.findIndex(
              f => Number.parseInt(f.properties.pk) == id
            );
            if (idx >= 0) {
              this.geoJSON.features.splice(idx, 1);
            }
          });
          this.setMapSections();
        })
        .catch(error => {
          console.log(error);
          console.log(error.response);
        })
        .finally(() => {
          this.deleting = false;
        });
    },
    highlightTrailSection(trailSectionId) {
      const geoJSON = this.geoJSON.features.find(item => {
        return Number.parseInt(item.properties.pk) == trailSectionId;
      });
      if (geoJSON && geoJSON.geometry) {
        this.highlightTrails({
          trailLayers: [this.geoJSONToTrailLayer(geoJSON)],
          popup: false
        });
      }
    },
    scrollToSection(sectionId) {
      $("#scrollable-content").animate({
        scrollTop:
          $("#scrollable-content").scrollTop() +
          ($(`#section-${sectionId}`).offset().top -
            $("#scrollable-content").offset().top)
      });
    },
    onTrailSectionClick(layer) {
      window.open(`${layer.feature.properties.pk}`, "_blank");
    }
  }
});
