import "@babel/polyfill";
import Vue from "@/vue.js";
import axios from "axios";

import "@/components/icons/hk-globe.js";
import "@/components/icons/hk-sort-icon.js";
import { orderBy } from "@/utils.js";
import { mapData, MapHikster } from "@/map/data.js";
import { poiMethods } from "@/map/poi.js";
import { highlightMethods } from "@/map/methods.js";
import { mapUtils } from "@/map/utils.js";

axios.defaults.xsrfHeaderName = "X-CSRFToken";
axios.defaults.withCredentials = true;

new Vue({
  el: "#poi-list-component",
  data() {
    return {
      ...mapData,
      loading: true,
      deleting: false,
      poiCategories: [],
      activities: [],
      selectedCategory: {
        types: []
      },
      selectedType: {},
      pois: [],
      selectedPoiInMap: null,
      sortBy: {
        key: "display_name",
        ascending: false
      },
      popupLayer: null,
      trailSectionsLayer: null
    };
  },
  mounted() {
    this.geoJSON = this.getGeojsonData("geojson-data");
    this.trailSectionsGeojson = this.getGeojsonData("trail_sections_geojson");
    this.poiCategories = this.getJsonData("poi-categories-data");
    this.selectedCategory = this.getJsonData("selected-category-data");
    this.selectedType = this.getJsonData("selected-type-data");

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
    this.setPois(this.getJsonData("poi-data"));
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
    hasPois() {
      return this.pois.length > 0;
    },
    hasSelected() {
      return this.pois.find(item => item.selected);
    },
    typeChoices() {
      return this.selectedCategory.types.filter(
        item => item.id != this.selectedType.id
      );
    }
  },
  methods: {
    ...mapUtils,
    ...highlightMethods,
    ...poiMethods,
    initMap() {
      const config = {
        center: [50.13466432216696, -72.72949218750001],
        zoom: 13,
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
      this.resultLayers = L.geoJson().addTo(this.map);
      this.selectionLayers = L.geoJson().addTo(this.map);
      this.highlightLayers = L.geoJson().addTo(this.map);
    },
    setPois(pois) {
      this.pois = pois;
      this.pois.forEach(item => {
        item.date_modified = new Date(item.date_modified);
      });
      this.showPois(this.geoJSON);
    },
    updateFilter() {
      this.loading = true;
      const query = {};
      const category = this.selectedCategory.id;
      const type = this.selectedType.id;
      if (category != -1) {
        query.category = category;
      }
      if (type != -1) {
        query.type = type;
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
          if (geojson != "") {
            this.geoJSON = JSON.parse(geojson);
          }
          this.setPois(response.data.point_of_interests);
        })
        .catch(error => {
          console.log(error);
        })
        .finally(() => {
          this.loading = false;
        });
    },
    selectCategory(category) {
      this.selectedCategory = category;
      const newType = category.types.find(
        item => item.id == this.selectedType.id
      );
      if (newType) {
        this.updateFilter();
      } else {
        this.selectType(category.types[0]);
      }
    },
    selectType(type) {
      this.selectedType = type;
      this.updateFilter();
    },
    sortData(sortKey) {
      this.$set(this.sortBy, "ascending", !this.sortBy.ascending);
      const method = this.sortBy.ascending ? "asc" : "desc";
      this.pois = orderBy(this.pois, sortKey, method);
      this.$set(this.sortBy, "key", sortKey);
    },
    getRowClass(poiId) {
      return {
        "secton-row": true,
        row: true,
        "py-2": true,
        selected: poiId === Number.parseInt(this.selectedPoiInMap)
      };
    },
    deletePois() {
      this.loading = true;
      const ids = this.pois
        .filter(item => item.selected)
        .map(item => item.poi_id);
      axios
        .delete(
          "/admin/api/point-of-interests/bulk-delete/?ids=" + ids.join(",")
        )
        .then(response => {
          if (this.geoJSON) {
            const features = this.geoJSON.features.filter(
              item => !ids.includes(Number.parseInt(item.properties.pk))
            );
            this.$set(this.geoJSON, "features", features);
          }
          this.setPois(this.pois.filter(item => !item.selected));
        })
        .catch(err => {
          console.log(err);
        })
        .finally(() => {
          this.loading = false;
        });
    },
    getType(typeId) {
      return this.typeChoices.find(type => type.id == typeId);
    },
    getTypeName(typeId) {
      const type = this.getType(typeId);
      if (type) {
        return type.name;
      }
      return "";
    },
    highlightPoi(poiId) {
      const geoJSON = this.geoJSON.features.find(item => {
        return Number.parseInt(item.properties.pk) == poiId;
      });
      if (!geoJSON) {
        return;
      }
      const layer = this.geoJSONToTrailLayer(geoJSON);
      this.map.fitBounds(layer.getBounds());
      const latlng = layer.getLayers()[0].getLatLng();
      const popup = L.popup({
        offset: new L.point(0, -36)
      }).setLatLng(latlng);
      const name =
        geoJSON.properties.name || this.getTypeName(geoJSON.properties.type);
      popup.setContent(
        `
        <div class="lf-popup poi" >
          <div class="header" >
            <div class="type">${name}</div>
          </div>
        </div>
        `
      );
      this.highlightLayers.addLayer(popup);
    },
    scrollToPoi(poiId) {
      $("#scrollable-content").animate({
        scrollTop:
          $("#scrollable-content").scrollTop() +
          ($(`#poi-${poiId}`).offset().top -
            $("#scrollable-content").offset().top)
      });
    }
  }
});
