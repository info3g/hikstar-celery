export const mapUtils = {
  isTrailPage() {
    return mapStyle === "trail";
  },
  isLocationPage() {
    return mapStyle === "location";
  },
  isPoiPage() {
    return mapStyle === "poi";
  },
  isResultsPage() {
    return mapStyle === "results";
  },
  isAdminLocationListPage() {
    return mapStyle === "admin-location-list";
  },
  isAdminTrailSectionListPage() {
    return mapStyle === "admin-trail-section-list";
  },
  isAdminTrailSectionDetailPage() {
    return mapStyle === "admin-trail-section-detail";
  },
  isAdminTrailListPage() {
    return mapStyle === "admin-trail-list";
  },
  isAdminTrailDetailPage() {
    return mapStyle === "admin-trail-detail";
  },
  isAdminPoiListPage() {
    return mapStyle === "admin-poi-list";
  },
  isAdminPoiDetailPage() {
    return mapStyle === "admin-poi-detail";
  },
  isWidgetPage() {
    return mapStyle === "widget";
  },
  setAttribution() {
    // const accessToken =
    //   "pk.eyJ1IjoiY2xhaXJlZGVndWVsbGUiLCJhIjoiY2ozazVraGkzMDB4NTJ3cXQ2NXd4YjZrYiJ9.aeR6EKn38zvZTvCVMgTdDA";
    // const tileUrl =
    //   "https://api.mapbox.com/styles/v1/mapbox/outdoors-v9/tiles/{z}/{x}/{y}";

    const tileUrl = "https://tile.thunderforest.com/landscape/{z}/{x}/{y}.png"

    let attribution = "Maps &copy; <a href='www.thunderforest.com'>Thunderforest</a>"
    attribution += ", Data &copy; <a href='http://www.openstreetmap.org/copyright'>OpenStreetMap</a>"
    L.tileLayer(`${tileUrl}?apikey=${THUNDERFOREST_KEY}`, {
      attribution: attribution
    }).addTo(this.map);



    attribution = this.map.attributionControl._container.innerHTML;
    this.attribution = attribution;
    this.map.attributionControl._container.innerHTML =
      attribution + " | " + this.map.getZoom();
  },

  getFeatureProps(layer) {
    /**
     * Returns the properties object from a L.geoJSON layer (with only 1 feature)
     * @param {L.geoJSON} layer A leaflet GeoJSON layer
     * @return {Object} The feature properties object
     */
    return layer.toGeoJSON().features[0].properties || null;
  },
  updateAttribution() {
    this.map.attributionControl._container.innerHTML =
      this.attribution + " | " + this.map.getZoom();
  },

  getJsonData(elementID) {
    return JSON.parse(document.getElementById(elementID).textContent);
  },

  getGeojsonData(elementID) {
    return JSON.parse(
      JSON.parse(document.getElementById(elementID).textContent)
    );
  },

  geoJSONToTrailLayer(geoJSON, highlight = true) {
    let trailLayer;
    try {
      trailLayer = L.geoJson(geoJSON);
    } catch (e) {
      trailLayer = L.geoJson({
        geometry: {},
        properties: {},
        id: trail.id,
        type: "Feature"
      });
    }
    trailLayer.layerType = "Trail";

    if (highlight) {
      trailLayer.on("mouseover", e => {
        L.DomEvent.stopPropagation(e);
        clearTimeout(this.timer);
        this.highlightTrails({
          trailLayers: [trailLayer],
          e: e
        });
      });
    }
    return trailLayer;
  },

  fitToLocations(maxBound) {
    this.locationGeoJSON = this.getGeojsonData("location_geojson_data");
    console.log('112 locationGeoJSON');
    console.log(this.locationGeoJSON);
    const layer = L.geoJson(this.locationGeoJSON);
    console.log('115 layer');
    console.log(layer);
    const bounds = layer.getBounds();
    // if (bounds !== {}) {
    //   console.log('118 bounds');
    //   console.log(bounds);
    //   this.map.fitBounds(bounds, {
    //     animate: true
    //   });
    //
    //   if (maxBound) {
    //     this.map.setMaxBounds(bounds);
    //   }
    // }
  },

  getTrailHighestCoord(layer) {
    /**
     * Finds the highest latitude in a LineString or MultiLineString geometry object
     * @param {L.geoJSON} layer A trail layer
     * @return {L.latLng} Highest latitude
     */

    const getHighestCoord = (line, latlng) => {
      for (let coord of line) {
        if (coord[1] > latlng.lat) {
          latlng = L.latLng({
            lat: coord[1],
            lng: coord[0]
          });
        }
      }
      return latlng;
    };

    let latlng = L.latLng(0, 0);
    let feature = layer.toGeoJSON().features[0];
    switch (feature.geometry.type) {
      case "LineString":
        let line = feature.geometry.coordinates;
        latlng = getHighestCoord(line, latlng);
        break;

      case "MultiLineString":
        let lines = feature.geometry.coordinates;
        for (let line of lines) {
          latlng = getHighestCoord(line, latlng);
        }
        break;
    }
    return latlng;
  },

  _toggleLayer(layer, condition) {
    /**
     * Toggles the visibility of a layer on or off based on some true/false condition
     * Note: Leaflet disgracefully returns an error when the layer specified for
     * L.map.addLayer or L.map.removeLayer is null or undefined. This function
     * makes the proper checks and does nothing if the layer is invalid.
     * @param {L.Layer} layer The layer to toggle on or off
     * @param {Boolean} condition Condition for toggling the layer on or off
     */
    if (layer) {
      if (condition && !this.map.hasLayer(layer)) {
        this.map.addLayer(layer);
      } else if (!condition && this.map.hasLayer(layer)) {
        this.map.removeLayer(layer);
      }
    }
  }
};
