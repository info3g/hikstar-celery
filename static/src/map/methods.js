import axios from "axios";

import { MapHikster, Sport } from "./data.js";
import { mapUtils } from "@/map/utils.js";
import { poiMethods } from "@/map/poi.js";

export const highlightMethods = {
  _overflowsBounds(layer) {
    /**
     * Finds out if the current layer fits in the map at the current zoom level
     * Confusion: Note that it doesn't check if the layer fits in the current extent, it checks if it would fit in the extent if it was at that location
     * @param {L.Layer} layer
     * @return {Boolean} True if the current layer wouldn't fit in the map at the current zoom level
     */
    return this.map.getBoundsZoom(layer.getBounds()) < this.map.getZoom();
  },
  _flyToBounds(bounds, options) {
    /**
     * Does a slow zoom animation to go from the current bonds to the next
     * @param {L.latLngBounds} bounds The new map bounds to fly to
     * @param {Object} options? Same as fitBounds options
     */
    // Some layers are kinda ugly when scaled during the flyTo animation. Hide them during the animation.
    this._toggleLayer(this.trailClientLayer, false);
    for (let tileLayer of this.tileLayers) {
      this._toggleLayer(tileLayer, false);
    }
    this._toggleLayer(this.incompleteMarkers, false);

    // Some path layers bug out during the flyTo animation. Hide the entire overlay pane. This hides all path layers within the pane.
    L.DomUtil.setOpacity(
      document.getElementsByClassName("leaflet-overlay-pane")[0],
      0
    );

    // Fly you fools
    this.map.flyToBounds(bounds, options);
  },
  _handleHighlightOff() {
    this.highlightLayers.clearLayers();
  },
  popupTrail(params) {
    /**
     * Displays a popup for the specified trail(s)
     * @param {Object} params
     *   offset? {Number} Alters the vertical position of the popup by this Y offset (in pixels)
     *   latlng? {L.latLng}
     */
    let offset = params.hasOwnProperty("offset") ? params.offset : 0;
    let latlng = params.latlng;
    let trail = params.hasOwnProperty("trail") ? params.trail : null;
    let length = params.length;

    let layer = params.hasOwnProperty("layer")
      ? params.layer
      : this.selectionLayers;
    let details = params.hasOwnProperty("details") ? params.details : true;

    let popup = L.popup({
      offset: new L.point(0, offset),
      autoPan: false
    }).setLatLng(latlng);

    let name = trail ? trail.name : "Sentier";
    let description = trail ? trail.description : null;
    let difficulty = this.getDifficulty
      ? this.getDifficulty(trail.activities)
      : "";
    let surface_type = trail ? trail.surface_type : null;

    let location = {};
    if (this.isTrailPage()) {
      location = this.trailLocation;
    } else if (trail && trail.location) {
      location = trail.location;
    }
    const locationId = location.location_id;
    const locationName = location.name;

    const hideTrail =
      params.hasOwnProperty("incomplete") &&
      params.incomplete &&
      this.map.getZoom() < 15;

    const trailId = trail.pk || trail.id || trail.trail_id;

    let content = "";
    let locationContent = "";
    let locationDetail = "";

    let isWidget = (mapStyle === 'widget');
    var additionalParams = isWidget ? `?${WIDGET_PARAMS}` : '';
    if (this.isResultsPage() || this.isWidgetPage()) {
      var prefix = additionalParams === '' ? '' : '&';
      additionalParams = `${additionalParams}${prefix}sport=${this.sport}`;
    }

    let locationSection = isWidget ? '/map-widget/locations/' : '/locations/';
    let locationLink = `${window.location.origin}${locationSection}${locationId}/?${additionalParams}`;

    let trailContent = "";
    let trailDetail = "";
    let trailLink = "";

    if (this.isResultsPage() || this.isWidgetPage()) {
      locationLink = `${locationLink}?sport=${this.sport}`;
    }

    if (details) {
      if (isWidget) {
      locationDetail = `
        <a
          id="network-${locationId}"
          class="link network"
          href="${locationLink}"
          onclick="openDetailFrame(this.href); return false;"
        >${seeDetails}</a>
      `;
      } else {
      locationDetail = `
        <a
          id="network-${locationId}"
          class="link network"
          href="${locationLink}"
          target="_blank"
        >${seeDetails}</a>
      `;
      }
    }
    if (locationName) {
      locationContent = `
        <div class="section network">
          <div class="section-name">${networkLabel}:</div>
          <div class="section-values">
            <div>${locationName}</div>
            ${details ? locationDetail : ""}
          </div>
        </div>
      `;
    }
    if (!hideTrail) {
      const lengthDiv = length ? `<div>${length}</div>` : "";
      const difficultyDiv = difficulty ? `<div>${difficulty}</div>` : "";

      if (locationName) {
        if (trailId) {

          if (mapStyle === 'widget') {
            trailLink = `
              <a
                id="details-${trailId}"
                class="link details"
                href="/map-widget/hikes/${trailId}/?${WIDGET_PARAMS}"
                onclick="openDetailFrame(this.href); return false;"
              >${seeDetails}</a>
            `;
          } else {
            trailLink = `
              <a
                id="details-${trailId}"
                class="link details"
                href="/hikes/${trailId}/"
                target="_blank"
              >${seeDetails}</a>
            `;
          }
        }
      }

      trailDetail = `
          <div class="section-name">${pathLabel}:</div>
          <div class="section-values">
            <div>${name}</div>
            ${lengthDiv}
            ${difficultyDiv}
            ${trailLink}
          </div>
        `;

      let trailID = "";
      let sectionClass = "section trail";
      if (
        this.isAdminTrailSectionListPage() ||
        this.isAdminTrailSectionDetailPage() ||
        this.isAdminPoiListPage() ||
        this.isAdminPoiDetailPage()
      ) {
        sectionClass = "section";
        trailID = `
          <div class="section">
            <div class="section-name">ID:</div>
            <div class="section-values">${params.trail.pk}</div>
          </div>
        `;
      }
      trailContent = `
        ${trailID}
        <div class="${sectionClass}">
          ${trailDetail}
        </div>
      `;
    }
    content = `
      <div class="lf-popup trail">
        ${locationContent}
        ${trailContent}
      </div>
    `;

    popup.setContent(content);
    layer.addLayer(popup);
    popup.id = trail ? trail.trail_id : null;
    return popup;
  },
  highlightTrails(params) {
    /**
     * Highlights a trail(s) when the user moves the mouse over it.
     * It does this by creating a duplicate (but larger) line behind the original trail(s)
     * @param {Object} params
     *   popup? {Boolean} Displays a popup of the trail(s) after the highlight
     */
    let trailLayers = params.trailLayers;
    let popup = params.hasOwnProperty("popup") ? params.popup : true;

    this.highlightLayers.clearLayers();

    if (trailLayers) {
      for (const trailLayer of trailLayers) {
        const clone = cloneLayer(trailLayer);
        const haloClone = cloneLayer(trailLayer);
        const trail = this.getFeatureProps(trailLayer);
        clone.setStyle(this.selectedTrailStyle);
        haloClone.setStyle(this.highlightHaloTrailStyle);
        this.highlightLayers.addLayer(haloClone);
        this.highlightLayers.addLayer(clone);

        clone.bringToFront();

        // If the trail is not already selected, add a pop for quick info about the trail (but no details link)
        if (
          popup &&
          (this.trailPopup === null ||
            this.trailPopup === undefined ||
            this.trailPopup.id !== this.getFeatureProps(trailLayer).id)
        ) {
          let latlng = this.getTrailHighestCoord(trailLayer);
          let total_length = this.getFeatureProps(trailLayer).total_length;

          if (
            this.isAdminLocationListPage() ||
            this.isAdminTrailSectionDetailPage
          ) {
            latlng = params.e.latlng;
            const length = null;
          } else {
            const length =
              total_length >= 1000
                ? Math.round((total_length / 1000) * 100) / 100 + " km"
                : Math.round(total_length * 10) / 10 + " m";
          }
          Object.assign(params, {
            trail: trail,
            latlng: latlng,
            layer: this.highlightLayers,
            details: false,
            length: length
          });

          this.popupTrail(params);
        }

        if (this.isAdminTrailSectionListPage()) {
          clone.on("click", e => {
            L.DomEvent.stopPropagation(e);
            this.onTrailSectionClick(e.layer);
          });
        }

        clone.on("mouseout", e => {
          L.DomEvent.stopPropagation(e);
          clearTimeout(this.timer);
          this.timer = setTimeout(() => {
            this.highlightLayers.clearLayers();
            if (this.isAdminLocationListPage()) {
              this.selectedLocationInMap = null;
            } else if (
              this.isAdminTrailSectionListPage() ||
              this.isAdminPoiListPage()
            ) {
              this.selectedTrailSectionInMap = null;
            }
          }, 200);
        });
      }
    }
  },

  selectTrails(params) {
    /**
     * Renders the selected trail(s) using a client-side layer
     * @param {Object} params
     *   trailLayers {Layer[]} ex: L.geoJSON().getLayers() or [L.geoJSON]
     *   latlng? {L.latLng} Highest latitude in the trail(s)
     *   popup? {Boolean} Displays a popup of the trail(s) after selection
     *   zoomSelection? {Boolean} Zoom after selection
     *   zoomType? {Number} Type of zooming animation
     *   incomplete? {Boolean} Indicates that the trail(s) is incomplete (i.e. not displayed)
     */
    if (this.selectionLayers) this.selectionLayers.clearLayers();
    if (this.highlightLayers) this.highlightLayers.clearLayers();
    this.trailPopup = null;

    const trailLayers = params.trailLayers;

    if (trailLayers.length > 0) {
      let latlng = params.latlng;
      let popup = params.hasOwnProperty("popup") ? params.popup : true;
      let zoomType = params.hasOwnProperty("zoomType")
        ? params.zoomType
        : MapHikster.ZOOM_FLYTO;

      // Display the selected trails
      this.selectedTrailStyle.opacity = params.hasOwnProperty("incomplete")
        ? 0
        : 1;

      for (const trailLayer of trailLayers) {
        const clone = cloneLayer(trailLayer);
        clone.data = trailLayer.data;
        clone.setStyle(this.selectedTrailStyle);

        clone.on("mouseover", e => {
          L.DomEvent.stopPropagation(e);
          clearTimeout(this.timer);
          this.highlightTrails({
            trailLayers: [trailLayer],
            e: e
          });
          if (this.isAdminLocationListPage()) {
            this.selectedLocationInMap = e.layer.feature.properties.pk;
          } else if (this.isAdminTrailSectionListPage()) {
            const sectionId = e.layer.feature.properties.pk;
            this.selectedTrailSectionInMap = sectionId;
            this.scrollToSection(sectionId);
          } else if (this.isAdminTrailListPage()) {
            const trailId = e.layer.feature.properties.pk;
            this.selectedTrailInMap = trailId;
            this.scrollToTrail(trailId);
          }
        });

        if (
          !this.isAdminTrailSectionListPage() &&
          !this.isAdminTrailSectionDetailPage() &&
          !this.isAdminTrailDetailPage() &&
          !this.isAdminPoiListPage() &&
          !this.isAdminPoiDetailPage()
        ) {
          // Light green glow
          const haloClone = cloneLayer(trailLayer);
          haloClone.setStyle(this.selectHaloTrailStyle);
          this.selectionLayers.addLayer(haloClone);
        }

        this.selectionLayers.addLayer(clone);

        clone.bringToFront();
      }

      // Zoom to the selected trails
      if (
        (this.map.getZoom() < 13 ||
          this._overflowsBounds(this.selectionLayers)) &&
        !(
          params.hasOwnProperty("zoomSelection") &&
          params.zoomSelection === false
        )
      ) {
        switch (zoomType) {
          case MapHikster.ZOOM_FLYTO:
            this._flyToBounds(this.selectionLayers.getBounds().pad(0.25), {
              animate: true
            });
            break;
          case MapHikster.ZOOM_FITBOUNDS:
            this.map.fitBounds(this.selectionLayers.getBounds().pad(0.25), {
              animate: true
            });
            break;
        }
      } else {
        this.map.panTo(this.selectionLayers.getBounds().getCenter(), {
          animate: true,
          duration: 1
        });
      }

      // Display popup for each trail
      if (popup) {
        for (let selectionLayer of this.selectionLayers.getLayers()) {
          if (selectionLayer.hasOwnProperty("data")) {
            // Only consider the true layers, not the halo layers
            // For the popup coordinate, we use the highest latitude of the trail
            if (!params.hasOwnProperty("incomplete")) {
              latlng = this.getTrailHighestCoord(selectionLayer);
            }

            let total_length = this.getFeatureProps(selectionLayer)
              .total_length;
            Object.assign(params, {
              trail: this.getFeatureProps(selectionLayer),
              latlng: latlng,
              length:
                total_length >= 1000
                  ? Math.round((total_length / 1000) * 100) / 100 + " km"
                  : Math.round(total_length * 10) / 10 + " m"
            });

            this.trailPopup = this.popupTrail(params);
          }
        }
      }
    }
  }
};

export const mapMethods = {
  ...highlightMethods,
  ...mapUtils,
  ...poiMethods,
  setInitialData() {
    $("#loading-mask").fadeOut();
    $("body").removeClass("no-scroll");
    this.mapServer = MAP_SERVER;
    this.mapService = MAP_SERVICE;
  },

  _handleHikeClick(trail) {
    if (trail.shape)
      this.selectTrails({
        trailLayers: [this.trailToGeoJSON(trail)]
      });
  },

  _handleHighlight(trail) {
    if (trail.shape)
      this.highlightTrails({
        trailLayers: trail.trail_id ? [this.trailToGeoJSON(trail)] : null,
        popup: false
      });
  },

  initMap() {
    if (this.isTrailPage()) {
      this.initTrailMap();
    } else if (this.isLocationPage()) {
      this.initLocationMap();
    } else if (this.isResultsPage()) {
      this.initResultsMap();
    } else if (this.isAdminLocationListPage()) {
      this.initLocationMap();
    } else if (this.isAdminTrailSectionListPage()) {
      this.initLocationMap();
    } else if (this.isAdminTrailListPage()) {
      this.initLocationMap();
    } else if (this.isPoiPage()) {
      this.initPoiMap();
    } else if (this.isWidgetPage()) {
      this.initWidgetMap();
    }

    this.setAttribution();

    L.Control.zoomHome({
      position: "topright",
      parent: this
    }).addTo(this.map);

    this.addTileLayers();

    if (!this.isAdminTrailSectionListPage()) {
      // Display trail sections
      this.updateTrailLayer({ sport: this.sport });

      // Add incomplete later for incomplete trail sections
      //this.updateIncompleteTrails({ sport: this.sport });

      // Add FeatureLayer for the Regions
      this.updateRegionLayer();

      // Map event handlers
      this.map.on("click", e => {
        this.onMapClick(e);
      });
      this.map.on("zoomstart", e => {
        this._toggleLayer(this.poiClusterGroup, false);
      });
      this.map.on("dragstart", e => {});

      this.map.on("zoomend", e => {
        this.onZoomed(e);
        if (this.isResultsPage() || this.isWidgetPage()) {
          this.searchByCoordinates();
        }
      });
    }

    this.map.on("dragend", e => {
      clearTimeout(this.refreshAllTheThings);
      this.refreshAllTheThings = setTimeout(e => {
        this.updatePOIClusters();
        // this.updateIncompleteTrails({ sport: this.sport });
        this.updateTrailLayer({ sport: this.sport });

        if (this.isResultsPage() || this.isWidgetPage()) {
          this.searchByCoordinates();
        }
      }, 2000);
    });

    if (this.config.scale) {
      L.control
        .scale({ imperial: false, position: "topright" })
        .addTo(this.map);
    }

    this.resultLayers = L.geoJson().addTo(this.map);
    this.selectionLayers = L.geoJson().addTo(this.map);
    this.highlightLayers = L.geoJson().addTo(this.map);
  },
  initPoiMap() {
    const config = { ...this.baseMapConfig, scrollWheelZoom: false };
    this.map = L.map("map", config);
  },
  initTrailMap() {
    const config = { ...this.baseMapConfig, scrollWheelZoom: false };
    this.map = L.map("map", config);
  },
  initLocationMap() {
    const config = { ...this.baseMapConfig, scrollWheelZoom: false };
    this.selectHaloTrailStyle = {
      color: MapHikster.CLAIRE_LIGHT_GREEN,
      weight: 7,
      opacity: 1
    };
    this.map = L.map("map", config);
  },
  initResultsMap() {
    const config = {
      ...this.baseMapConfig,
      scrollWheelZoom: true,
      showRegionLayer: true
    };
    this.$set(this.config, "showRegionLayer", true);
    this.selectHaloTrailStyle = {
      color: MapHikster.CLAIRE_LIGHT_GREEN,
      weight: 7,
      opacity: 1
    };
    this.map = L.map("map", config);
  },
  initWidgetMap() {
    const config = {
      ...this.baseMapConfig,
      scrollWheelZoom: true,
      showRegionLayer: true
    };
    this.$set(this.config, "showRegionLayer", true);
    this.selectHaloTrailStyle = {
      color: MapHikster.CLAIRE_LIGHT_GREEN,
      weight: 7,
      opacity: 1
    };
    this.map = L.map("map", config);
    var bounds = L.latLngBounds([[widgetLatMin, widgetLngMin], [widgetLatMax, widgetLngMax]]);

    this.map.setMaxBounds(bounds);
    var setting_zoom = this.map.getBoundsZoom(bounds);
    this.map.zoom = setting_zoom;
    this.map.maxZoom = setting_zoom;
  },
  addTileLayers() {
    for (const key in Sport) {
      this.addTileLayer(Sport[key]);
    }
  },
  onZoomed(e) {
    clearTimeout(this.refreshAllTheThings);
    this.refreshAllTheThings = setTimeout(e => {
      this.updatePOIClusters();
      // this.updateIncompleteTrails({
      //   sport: this.sport
      // });
      this.updateTrailLayer({
        sport: this.sport
      });
    }, 2000);

    this.updateAttribution();

    if (this.latestRegionMouseOver && this.map.getZoom() > 7) {
      this.latestRegionMouseOver.setStyle(this.regionPolygonStyle);
      this.latestRegionMouseOver = null;
    }

    // Restore opacity to the overlay pane after a flyTo
    L.DomUtil.setOpacity(
      document.getElementsByClassName("leaflet-overlay-pane")[0],
      1
    );
  },
  addTileLayer(activityId) {
    var latMin = this.isWidgetPage() ? widgetLatMin :  -90,
        lngMin = this.isWidgetPage() ? widgetLngMin :  -180,
        latMax = this.isWidgetPage() ? widgetLatMax :  90,
        lngMax = this.isWidgetPage() ? widgetLngMax :  180,
        zoomLimit = this.isWidgetPage() ? this.map.maxZoom : 15;

    console.log(
        '556 - set bounds on Tile Layer: ' +
        'min_lng: ' + lngMin +
        'min_lat: ' + latMin +
        'max_lng: ' + lngMax +
        'max_lat: ' + latMax
    );

    var bounds = L.latLngBounds(
      L.latLng(latMin, lngMin),
      L.latLng(latMax, lngMax)
    );
    this.tileLayers.push(
      new L.tileLayer(
        this.mapServer +
          this.mapService +
          "_Tiles_Activity" +
          activityId +
          "/MapServer/tile/{z}/{y}/{x}",
        {
          activity_id: activityId,
          minZoom: 0,
          maxZoom: zoomLimit,
          bounds: bounds, // If set, tiles will only be loaded inside the set LatLngBounds
          updateWhenZooming: false,
          keepBuffer: 20 // When panning the map, keep this many rows and columns of tiles before unloading them
        }
      )
    );
  },

  getDistanceByZoomLevel() {
    /**
     * Finds the ideal distance a mouse click (projected onto the map) should be
     * from a trail to trigger a selection. Depends on the current zoom level.
     * @return {Number} distance (in meters)
     */
    const x = this.map.getZoom();
    const m = (200 - 20) / (10 - 16);
    const b = 20 - m * 16;
    var y = m * x + b;
    if (y < 0) y = 5;
    return y;
  },

  trailsToGeoJSON(trails) {
    /**
     * Takes a trail array from the API and outputs a new L.geoJSON layer of the trails
     * @param {Array} trails Array of trail objects from the API
     * @return {L.geoJSON} Layer that contains several other L.geoJSON layers of trail sections (one per trail)
     */
    const trailsLayer = L.geoJson();
    trailsLayer.layerType = "Network";
    for (const trail of trails) {
      trailsLayer.addLayer(this.trailToGeoJSON(trail));
    }
    return trailsLayer;
  },

  trailToGeoJSON(trail) {
    /**
     * Takes a trail object from the API and outputs a new L.geoJSON layer of the trail
     * @param {Object} trail Trail data from the API
     * @return {L.geoJSON} Trail Layer
     */
    const geoJSON = {
      geometry: Object.assign({}, trail.shape),
      properties: Object.assign({}, trail),
      id: trail.trail_id || trail.id,
      type: "Feature"
    };
    geoJSON.id = geoJSON.properties.pk;
    delete geoJSON.properties.shape;

    return this.geoJSONToTrailLayer(geoJSON);
  },

  updateTrailLayer(params) {
    /**
     * Renders the trails on the map
     * @param {Object} params
     *   sport {Sport} Indicates which sport(s) are enabled (there can be more then one at the same time)
     */
    let sport = params.sport;

    // Remove client-side layer
    this._toggleLayer(this.trailClientLayer, false);

    // Render tile layers for lower zoom levels.
    //Render a client-side layer for the highest levels (i.e. no tiles available)
    if (this.map.getZoom() <= 15) {
      for (let tileLayer of this.tileLayers) {
        this._toggleLayer(tileLayer, sport === tileLayer.options.activity_id);
      }
    } else {
      let where = null;
      switch (sport) {
        case Sport.NONE:
          where = "activity_id = 0";
          break;
        case Sport.ALL:
          where = "activity_id > 0";
          break;
        default:
          where = "activity_id = " + sport;
      }

      let query = L.esri.query({
        url:
          this.mapServer +
          this.mapService +
          "/MapServer/" +
          MapHikster.LAYER_TRAIL,
        useCors: true
      });
      query.intersects(this.map.getBounds());
      query.where(where);
      query.run((error, featureCollection, response) => {
        this.trailClientLayer = L.geoJson(featureCollection, {
          style: this.defaultTrailStyle,
          onEachFeature: (feature, layer) => {
            layer.on("mouseover", e => {
              if (e.target._map.getZoom() >= 16) {
                // L.esri.featureLayer bug? Sometimes this is called when zoom is outside min/max zoom bounds
                e.target.setStyle(this.highlightHaloTrailStyle);
              }
            });
            layer.on("mouseout", e => {
              e.target.setStyle(this.defaultTrailStyle);
            });
            layer.on("click", e => {
              if (e.target._map.getZoom() >= 16) {
                console.log("Trail clicked");
                // [YB 2016-12-08: We can't do anything here. We must do a spatial query and get ALL the trails at the point clicked in the map. see onMapClick]
              }
            });
          }
        });

        this.map.addLayer(this.trailClientLayer);
      });
    }
  },

  // updateIncompleteTrails(params) {
  //   /**
  //    * The geometry of trails that haven't been created yet is just a short line
  //    * segment located at the trail park location. Until they are created, we
  //    * represent them in the map as green markers
  //    * @param {Object} params
  //    *   sport {Sport} Indicates which sport(s) are enabled (there can be more then one at the same time)
  //    */
  //   var sport = params.sport;
  //   var zoomLevel = this.map.getZoom();
  //
  //   // If the scale is 1:1 million or smaller, update the incomplete trails clusters
  //   if (sport !== Sport.NONE && zoomLevel >= 7) {
  //     // Request incomplete trail geometry
  //     var query = L.esri.query({
  //       url:
  //         this.mapServer +
  //         this.mapService +
  //         "/MapServer/" +
  //         MapHikster.LAYER_INCOMPLETE_TRAIL,
  //       useCors: true
  //     });
  //
  //     query.within(this.map.getBounds());
  //
  //     // the current sport filter
  //     var where = null;
  //     switch (sport) {
  //       case Sport.ALL:
  //         where = "activity_id > 0";
  //         break;
  //       default:
  //         where = "activity_id = " + sport;
  //         break;
  //     }
  //     query.where(where);
  //
  //     query.run((error, featureCollection, response) => {
  //       var icon =
  //         zoomLevel >= 10 ? this.incompleteIcon50 : this.incompleteIcon100;
  //       var iconHover =
  //         zoomLevel >= 10
  //           ? this.incompleteIcon50Hover
  //           : this.incompleteIcon100Hover;
  //       params.offset = zoomLevel >= 10 ? -6 : -2;
  //       var incompleteMarkers = L.featureGroup([]);
  //
  //       if (featureCollection && featureCollection.features.length > 0) {
  //         // The geometries returned are polyline, not points.
  //         // However to display the incomplete markers on the map, we need points.
  //         // Use the first coord of the trail as the marker point.
  //         for (const feature of featureCollection.features) {
  //           var pt =
  //             feature.geometry.type === "MultiLineString"
  //               ? feature.geometry.coordinates[0][0]
  //               : feature.geometry.coordinates[0];
  //
  //           // Create the marker
  //           var marker = L.marker(
  //             L.latLng({
  //               lat: pt[1],
  //               lng: pt[0]
  //             }),
  //             {
  //               feature: feature,
  //               icon: icon
  //             }
  //           );
  //           marker.on("click", e => {
  //             this.onIncompleteMarkerClick(e, params);
  //           });
  //           marker.on("mouseover", e => {
  //             e.target.setIcon(iconHover);
  //           });
  //           marker.on("mouseout", e => {
  //             e.target.setIcon(icon);
  //           });
  //
  //           incompleteMarkers.addLayer(marker);
  //         }
  //
  //         this.map.addLayer(incompleteMarkers);
  //         this._toggleLayer(this.incompleteMarkers, false);
  //         this.incompleteMarkers = incompleteMarkers;
  //
  //         // If we are at a high zoom we want to see individual incomplete markers (that may be one on top of each other)
  //         // We do this by clustering them and using the cluster spiderify function
  //         this._toggleLayer(this.incompleteClusters, false);
  //         if (zoomLevel >= 15) {
  //           this.incompleteClusters = L.markerClusterGroup({
  //             spiderfyDistanceMultiplier: 3,
  //             zoomToBoundsOnClick: false,
  //             iconCreateFunction: cluster => {
  //               return icon;
  //             }
  //           }).addTo(map);
  //
  //           this.incompleteClusters.addLayers(
  //             this.incompleteMarkers.getLayers()
  //           );
  //         }
  //       } else {
  //         this._toggleLayer(this.incompleteMarkers, false);
  //         this._toggleLayer(this.incompleteClusters, false);
  //       }
  //     });
  //   } else {
  //     this._toggleLayer(this.incompleteMarkers, false);
  //     this._toggleLayer(this.incompleteClusters, false);
  //   }
  // },

  // onIncompleteMarkerClick(e, params) {
  //   const feature = e.target.options.feature;
  //
  //   // Get extra info about this trail from the API (e.g. Park information)
  //   // -- info which is not available directly in the map service layer
  //   axios
  //     .get(`${API_URL}trails/` + feature.properties.trail_id, {
  //       // TODO check to use id alias instead to make it more straightforward
  //       params: {
  //         include: "id,location,name,location_id",
  //         expand: "location"
  //       },
  //       responseType: "json",
  //       timeout: 20000
  //     })
  //     .then(response => {
  //       Object.assign(feature.properties, response.data);
  //       Object.assign(params, {
  //         trailLayers: [L.geoJSON(feature)],
  //         latlng: e.latlng,
  //         incomplete: true,
  //         zoomSelection: false
  //       });
  //       this.selectTrails(params);
  //     });
  // },

  updateRegionLayer() {
    /**
     * Renders the tourism regions on the map using a client-side layer
     * Only for the lowest zoom levels (e.g. 50km+)
     */
    if (this.config.showRegionLayer && this.regionFeatureLayer === null) {
      var regionTooltips = {};

      var query = L.esri.query({
        url:
          this.mapServer +
          this.mapService +
          "/MapServer/" +
          MapHikster.LAYER_REGION,
        useCors: false
      });
      query.run((error, featureCollection, response) => {
        this.regionFeatureLayer = L.geoJson(featureCollection, {
          style: this.regionPolygonStyle,
          onEachFeature: (feature, layer) => {
            layer.on("mouseover", e => {
              this.latestRegionMouseOver = e.target;
              if (e.target._map.getZoom() < 8) {
                // L.esri.featureLayer bug? Sometimes this is called when zoom is > then maxZoom
                e.target.setStyle(this.highlightRegionPolygonStyle);
                layer.tooltipTimeout = setTimeout(() => {
                  e.target.bindTooltip(e.target.feature.properties.name);
                  e.target.openTooltip();
                }, 500);
              }
            });
            layer.on("mouseout", e => {
              e.target.setStyle(this.regionPolygonStyle);
              clearTimeout(layer.tooltipTimeout);
              e.target.closeTooltip();
              e.target.unbindTooltip();
            });
            layer.on("click", e => {
              if (e.target._map.getZoom() < 8) {
                e.target.setStyle(this.regionPolygonStyle);
                this._flyToBounds(e.target.getBounds(), {
                  animate: true
                });
              }
            });
          }
        }).addTo(this.map);
      });
    }
  },
  onMapClick(e) {
    // Spatial query to find features located nearby the mouse click
    const query = L.esri.query({
      url:
        this.mapServer +
        this.mapService +
        "/MapServer/" +
        MapHikster.LAYER_TRAIL,
      useCors: false
    });
    query.nearby(e.latlng, this.getDistanceByZoomLevel());
    query.fields(
      "activity_id,description,difficulty,trail_id,name,shape,total_length"
    );

    // This returns the features in GeoJSON FeatureCollection format
    query.run((error, featureCollection, response) => {
      if (!error) {
        if (featureCollection.features.length > 0) {
          // Get extra info about these trails from the API (e.g. Park information)
          //-- info which is not available directly in the map service layer
          const featureIds = [];
          for (let feature of featureCollection.features) {
            featureIds.push(feature.properties.trail_id);
          }
          axios
            .get(`${API_URL}/trails/`, {
              params: {
                ids: featureIds.toString(),
                include: "trail_id,location,name,location_id",
                expand: "location"
              },
              responseType: "json",
              timeout: 20000
            })
            .then(response => {
              // Create a leaflet L.geoJSON from the GeoJSON FeatureCollection
              // it will contain an array of L.geoJSON (1 per trail)
              const trailLayers = L.geoJSON();

              // Append the extra info to each trail in the feature collection
              for (const data of response.data.results) {
                for (const feature of featureCollection.features) {
                  if (data.trail_id === feature.properties.trail_id) {
                    Object.assign(feature.properties, data);

                    trailLayers.addLayer(L.geoJSON(feature));
                  }
                }
              }

              // Display the trails in the map, as a new "Selection" of trails
              this.selectTrails({
                trailLayers: trailLayers.getLayers()
              });
            });
        }
      } else {
        console.log(error);
      }
    });
  },
  getDifficulty(activities) {
    if (!activities || activities.length < 1) return "";
    let min = activities[0].difficulty;
    for (const item of activities) {
      if (item.difficulty < min) {
        min = item.difficulty;
      }
    }

    for (const item of this.difficulties) {
      if (item.id === min) {
        return item.name;
      }
    }
    return "";
  }
};
