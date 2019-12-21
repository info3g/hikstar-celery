import "@babel/polyfill";
import "url-search-params-polyfill";

import Vue from "@/vue.js";
import axios from "axios";

import "@/components/icons/hk-search.js";
import "@/components/icons/hk-globe.js";
import { mapData } from "@/map/data.js";
import { mapMethods } from "@/map/methods.js";
import { networkMethods } from "@/map/networkMethods.js";
import { searchMethods } from "@/search/methods.js";

Vue.component("dropdown-filter", {
  props: {
    label: {
      type: String
    },
    selected: {
      type: [Object, Array]
    },
    items: {
      type: Array
    },
    multiple: {
      type: Boolean,
      default: false
    },
    showValue: {
      type: Boolean,
      default: false
    }
  },
  computed: {
    linkClass() {
      return {
        "nav-link": true,
        "dropdown-toggle": true,
        "has-value": this.multiple ? this.selected.length : this.selected.id
      };
    }
  },
  methods: {
    click(item) {
      this.$emit("click", item);
    },
    isSelected(item) {
      if (this.multiple) {
        return this.selected.includes(item.id);
      } else {
        return this.selected.id === item.id;
      }
    }
  },
  template: `
        <li class="nav-item dropdown">
            <a
                :class="linkClass"
                href="#"
                role="button"
                data-toggle="dropdown"
                aria-haspopup="true"
                aria-expanded="false"
                >
                {[ label ]}
                <template v-if="showValue && selected.name">({[ selected.name ]})</template>
                <template v-if="multiple && selected.length">({[ selected.length ]})</template>
            </a>
            <div class="dropdown-menu" aria-labelledby="navbarDropdown">
                <a
                    v-for="item in items"
                    :key="item.id"
                    :class="{'dropdown-item': true, active: isSelected(item)}"
                    @click="click(item)"
                >{[ item.name ]}</a>
            </div>
        </li>
    `
});

new Vue({
  el: "#results-page",
  data() {
    return {
      ...mapData,
      showResults: true,
      results: [],
      noResult: false,
      searchTerm: "",
      locationId: null,
      searchTimeout: null,
      suggestions: [],
      activityChoices: [],
      typeChoices: [],
      difficultyChoices: [],

      coordinateFilters: null,
      searching: false,
      loadingNextPage: false,

      pagination: {},
      baseSearchUrl: null,
      showPoiFilter: false,

      selectedActivity: {},
      selectedLength: {},
      selectedTypes: [],
      selectedDifficulties: [],
      withDog: false,

      lengths: [
        {
          id: "0-2000",
          name: "0-2 km"
        },
        {
          id: "2000-5000",
          name: "2-5 km"
        },
        {
          id: "5000-10000",
          name: "5-10 km"
        },
        {
          id: "10000",
          name: "+10 km"
        }
      ]
    };
  },
  filters: {
    duration(activities) {
      if (activities.length < 1) return "-";
      let min = activities[0].duration;
      for (const item of activities) {
        if (item.duration < min) {
          min = item.duration;
        }
      }
      const hours = Math.floor(min / 60);
      const minutes = min % 60;
      return `${hours}h${minutes}`;
    },
    distance(value) {
      return `${Number(value / 1000).toFixed(2)} km`;
    }
  },
  mounted() {
    this.setInitialData();
    this.activityChoices = JSON.parse(
      document.getElementById("activities-data").textContent
    );
    this.typeChoices = JSON.parse(
      document.getElementById("types-data").textContent
    );
    this.difficultyChoices = JSON.parse(
      document.getElementById("difficulties-data").textContent
    );
    const urlParams = new URLSearchParams(window.location.search);
    this.poiCategories = JSON.parse(
      document.getElementById("poi-categories-data").textContent
    );
    $("#poi-accordion").collapse();

    const activities = urlParams.get("activities");
    if (activities) {
      this.selectedActivity = this.getDefaultActivity(activities);
      this.sport = this.selectedActivity.id;
    } else if (!this.selectedActivity.id) {
      this.selectedActivity = this.getDefaultActivity();
      this.sport = this.selectedActivity.id;
    }

    if (urlParams.get("dog_allowed")) {
      this.withDog = true;
    }

    this.searchTerm = urlParams.get("search_term");
    const loc = urlParams.get("loc");
    if (loc) {
      this.baseSearchUrl = `${API_URL}trails/?loc=${loc}`;
      this.locationId = loc;
      this.search();
    }

    this.setCoordinateFilters();
    if (this.coordinateFilters) {
      this.searchByCoordinates(this.coordinateFilters);
    }

    this.initMap();

    if (this.coordinateFilters) {
      /**
       * Fit map bounds to selected coordinate filters
       **/
      const p1 = [
        this.coordinateFilters.min_lat,
        this.coordinateFilters.min_lng
      ];
      const p2 = [
        this.coordinateFilters.max_lat,
        this.coordinateFilters.max_lng
      ];
      this.map.fitBounds([p1, p2], {
        animate: true
      });
    }

    this.$nextTick(function() {
      window.addEventListener('resize', () => {
        const width = document.documentElement.clientWidth;
        if (width > 575) {
          this.showResultList()
        }
      });
    })
  },
  computed: {
    searchBtnClass() {
      return {
        btn: true,
        ui: true,
        "btn-outline-secondary": true,
        "btn-search": true,
        button: true,
        loading: this.searching
      }
    },
    toggleResultCls() {
      return {
        active: !this.showResults,
        btn: true,
        "toggle-result": true,
        "d-md-none": true,
      }
    },
    activities() {
      return this.activityChoices.filter(item => item.id !== 0);
    },
    types() {
      return this.typeChoices.map(item => {
        return { id: item[0], name: item[1] };
      });
    },
    difficulties() {
      return this.difficultyChoices.map(item => {
        return { id: item[0], name: item[1] };
      });
    },
    hasOtherPage() {
      return this.pagination.prev || this.pagination.next;
    },
    disableSearch() {
      return this.searching || !this.baseSearchUrl;
    },
    poiBtnFilterClass() {
      return {
        "poi-filter": true,
        btn: true,
        "d-none": true,
        "d-lg-inline-block": true,
        "mx-4": true,
        active: this.showPoiFilter
      };
    },
    filters() {
      /**
       * Filters used in API request
       *
       **/
      const query = {};
      if (this.selectedActivity.id) {
        query.activities = this.selectedActivity.id;
      }
      if (this.withDog) {
        query.dog_allowed = 1;
      }
      if (this.selectedDifficulties.length > 0) {
        query.difficulty = this.selectedDifficulties.join(",");
      }
      if (this.selectedLength.id) {
        query.length = this.selectedLength.id;
      }
      query.expand = "location";
      return query;
    }
  },
  methods: {
    ...searchMethods,
    ...mapMethods,
    ...networkMethods,
    showResultList() {
      $('.results-page .accordion-wrapper').show()
      $('.results-page .map').css({left: "355px", width: "calc(100vw - 355px)"})
    },
    toggleResult() {
      if (this.showResults) {
        $('.results-page .accordion-wrapper').hide()
        $('.results-page .map').css({left: 0, width: "100%"})
      } else {
        this.showResultList();
      }
      this.showResults = !this.showResults
    },
    setCoordinateFilters() {

      if (mapStyle === "widget") {

        this.coordinateFilters = {
          min_lng: parseFloat(widgetLngMin),
          min_lat: parseFloat(widgetLatMin),
          max_lng: parseFloat(widgetLngMax),
          max_lat: parseFloat(widgetLatMax)
        };


      } else {

        const urlParams = new URLSearchParams(window.location.search);
        const min_lng = urlParams.get("min_lng");
        const min_lat = urlParams.get("min_lat");
        const max_lng = urlParams.get("max_lng");
        const max_lat = urlParams.get("max_lat");

        if (min_lat && min_lat && max_lng && max_lat) {
          this.coordinateFilters = {
            min_lng: parseFloat(min_lng),
            min_lat: parseFloat(min_lat),
            max_lng: parseFloat(max_lng),
            max_lat: parseFloat(max_lat)
          };
        }
      }

    },
    togglePoiSelectAll(category) {
      category.show_all = !category.show_all;
      for (const item of category.types) {
        item.show = category.show_all;
      }
      this.updatePOIClusters();
    },
    onPoiTypeFilterClick(poiType) {
      /**
       * Gets selected POI types and updates map to show
       * selected POI types
       */
      poiType.show = !poiType.show;
      for (const item of this.poiCategories) {
        for (const type of item.types) {
          if (poiType.id === type.id) {
            type.show = poiType.show;
          }
        }
      }
      this.updatePOIClusters();
    },
    getPoiIconClass(id) {
      /**
       * Returns image url of POI Icon
       * :param id:
       *   Number -- ID of `PointOfInterestType` instance
       */
      return {
        backgroundImage: `url('/static/img/markers/Icones_Hikster_${id}.svg')`
      };
    },
    togglePoiTypes(categoryId) {
      /*
      Show/hide POI Category accordion
      :param categoryId:
        Number -- One of POI_CATEGORY choices
      */
      for (const category of this.poiCategories) {
        const element = document.getElementById(`#collapse${category.id}`);
        if (category.id !== categoryId) {
          element.classList.remove("show");
        } else {
          element.classList.toggle("show");
        }
      }
    },
    getDefaultActivity(id) {
      /**
       * Gets activity with the smallest id and return it.
       */
      if (id) {
        return this.activities.find(item => item.id == parseInt(id));
      }

      if (this.isWidgetPage()) {
         return {id: 0, name: 'Activities'};
      }

      let defaultActivity = {
        id: Number.POSITIVE_INFINITY
      };
      for (const item of this.activities) {
        if (item.id < defaultActivity.id) {
          defaultActivity = item;
        }
      }
      return defaultActivity;
    },
    displayResults(results) {
      /**
       * Renders the results (i.e. trails) on the map using a client-side layer
       * @param {Object} params
       *   results {Object} Trails from the API
       *   callback? {Function} Function to call after rendering is complete
       */
      this.resultLayers.clearLayers();
      if (!results) {
        return;
      }
      const trails = results.filter(trail => trail.shape !== null);
      for (const trail of trails) {
        let convertedTrail = this.trailToGeoJSON(trail);
        convertedTrail.setStyle(this.resultTrailStyle);

        let haloClone = cloneLayer(convertedTrail);
        haloClone.setStyle(this.resultHaloTrailStyle);
        this.resultLayers.addLayer(haloClone);
        this.resultLayers.addLayer(convertedTrail);

        convertedTrail.bringToFront();
      }
      if (!this.coordinateFilters) {
        this.zoomResults();
      }
    },
    zoomResults(params) {
      /**
       * Zooms to bounds that contain all the results
       * @param {Object} params
       *   flyTo? {Boolean} Zoom animation mode
       */
      if (this.resultLayers.getLayers().length > 0) {
        if (params && params.hasOwnProperty("flyTo") && params.flyTo) {
          this._flyToBounds(this.resultLayers.getBounds().pad(0.25), {
            animate: true
          });
        } else {
          this.map.fitBounds(this.resultLayers.getBounds().pad(0.25), {
            animate: true
          });
        }
      }
    },
    getBanner(trail) {
      return trail.banner
        ? trail.banner
        : "/static/img/accueil-1--thumbnail.jpeg";
    },
    debounceSearch(val) {
      this.noResult = false;
      this.baseSearchUrl = "";
      this.searchTerm = val;
      if (this.searchTimeout) clearTimeout(this.searchTimeout);
      this.searchTimeout = setTimeout(() => {
        this.fetchSuggestions();
      }, 400);
    },
    selectItem(selectedItems, item) {
      /**
       * When an item is selected in the dropdown filter
       * This is used in filters that support multiple values, i.e. Difficulty
       */
      const index = selectedItems.findIndex(elem => elem === item.id);
      if (index >= 0) {
        selectedItems.splice(index, 1);
      } else {
        selectedItems.push(item.id);
      }
      this.search();
    },
    selectActivity(activity) {
      /**
       * Sets selectedActivity and updates the search result
       * :param activity:
       *   Object -- {id: Number, ...}
       */
      if (activity.id === this.selectedActivity.id) {
        return;
      }
      this.selectedActivity = activity;
      this.sport = activity.id;
      this.updateTrailLayer({ sport: this.sport });
      // this.updateIncompleteTrails({ sport: this.sport });
      this.resultLayers.clearLayers();
      this.search();
    },
    selectLength(length) {
      /**
       * Sets selectedLength and updates the search result
       */
      if (length.id === this.selectedLength.id) {
        this.selectedLength = {};
      } else {
        this.selectedLength = length;
      }
      this.search();
    },
    selectType(type) {
      this.selectItem(this.selectedTypes, type);
    },
    selectDifficulty(difficulty) {
      this.selectItem(this.selectedDifficulties, difficulty);
    },
    toggleWithDog() {
      this.withDog = !this.withDog;
      this.search();
    },
    onSuggestionClick(value) {
      if (value.type === "trail") {
        if (this.isWidgetPage()) {
          console.log('518 open with correct page');
          openWithCorrectUrl(value.url);
        } else {
          window.open(value.url, "_blank");
        }
      } else {
        this.searchTerm = value.name;
        this.baseSearchUrl = value.url;
        this.locationId = value.url.split("=")[1];
        this.suggestions = [];
      }
    },
    onResultScroll(event) {
      const element = event.target;
      if (element.scrollTop === element.scrollHeight - element.offsetHeight) {
        if (this.pagination.next) {
          this.loadingNextPage = true;
          this.search(this.pagination.next);
        }
      }
    },
    searchByLocation() {
      this.loadingNextPage = false;
      this.coordinateFilters = null;
      this.search();
    },
    searchByCoordinates(params) {
      this.loadingNextPage = false;
      this.locationId = null;
      this.searchTerm = "";
      this.results = [];
      this.searching = true;

      const baseUrl = `${API_URL}trails/`;
      let query = params;

      if (!query) {
        const bounds = this.map.getBounds();
        const northEast = bounds.getNorthEast();
        const southWest = bounds.getSouthWest();
        query = {
          min_lng: northEast.lng,
          min_lat: northEast.lat,
          max_lng: southWest.lng,
          max_lat: southWest.lat
        };

        this.coordinateFilters = { ...query };
      }

      if (mapStyle === 'widget') {
        query['locations'] = widgetLocations;
      }

      this.baseSearchUrl = `${baseUrl}?${this.getQueryString(query)}`;
      this.search();
    },
    updateUrlDisplay(queryString) {
      /**
       * Changes URL in address bar based on the search queries
       */
      let pathName = `${window.location.pathname}?`;
      const query = {};
      if (this.searchTerm) {
        query.search_term = this.searchTerm;
      }
      if (this.locationId) {
        query.loc = this.locationId;
      }

      if (this.searchTerm || this.locationId) {
        pathName = `${pathName}${this.getQueryString(query)}&`;
      }
      window.history.pushState({}, document.title, `${pathName}${queryString}`);
    },
    search(url) {
      /**
       * Executes in the following cases:
       *   1. Clicking Search button
       *   2. Loading next page upon scrolling
       *   3. After dragging the map and search by coordinates
       */
      this.noResult = false;
      if (!this.baseSearchUrl && !url) {
        return;
      }
      let searchUrl = url;
      if (!searchUrl) {
        this.results = [];
        this.searching = true;
        let filters = { ...this.filters };
        const baseUrl = this.baseSearchUrl;
        searchUrl = `${baseUrl}&${this.getQueryString(filters)}`;
        if (this.coordinateFilters) {
          filters = { ...this.coordinateFilters, ...filters };
        }
        const queryString = this.getQueryString(filters);
        if (mapStyle !== "widget") {
            this.updateUrlDisplay(queryString);
        }
      }

      axios
        .get(searchUrl)
        .then(response => {
          const data = response.data;
          const results = data.results || [];

          if (results.length < 1) {
            this.noResult = true;
          }
          this.results = [...this.results, ...results];
          this.displayResults(this.results);
          this.pagination = {
            next: data.next,
            prev: data.prev
          };
        })
        .finally(() => {
          this.searching = false;
          this.loadingNextPage = false;
        });
    }
  }
});
