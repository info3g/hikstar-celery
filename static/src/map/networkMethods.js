import { MapHikster } from "./data.js";

//==============================================================================
//=============================== NETWORK ======================================
//==============================================================================
export const networkMethods = {
  selectNetwork: function(trailsJSON) {
    const trailsLayer = L.geoJson();
    trailsLayer.layerType = "Network";
    for (const trail of trailsJSON.features) {
      trailsLayer.addLayer(this.geoJSONToTrailLayer(trail));
    }
    this.selectTrails({
      trailLayers: trailsLayer.getLayers(),
      popup: false,
      zoomType: MapHikster.ZOOM_FITBOUNDS
    });
    //this.popupNetwork({ network: network });
  },

  popupNetwork: function(params) {
    let network = params.network.data;
    let name = network.name;
    let network_length = network.hasOwnProperty("network_length")
      ? network.network_length >= 1000
        ? Math.round((network.network_length / 1000) * 100) / 100 + " km"
        : Math.round(network.network_length * 10) / 10 + " m"
      : null;

    let maxLatlng = L.latLng(0, 0);
    for (let selectionLayer of this.selectionLayers.getLayers()) {
      let latlng = this.getTrailHighestCoord(selectionLayer);
      if (latlng.lat > maxLatlng.lat) {
        maxLatlng = latlng;
      }
    }

    let popup = L.popup({ offset: new L.point(0, 0) }).setLatLng(maxLatlng);

    let content =
      "<div class='lf-popup'>" +
      "<div class='header'><div class='text'>" +
      name +
      "</div></div>" +
      "<div class='content'>" +
      (Object.is(network_length, null)
        ? ""
        : "<div>" + network_length + "</div>") +
      "</div>" +
      (Object.is(network, null)
        ? ""
        : "<div id='details-" +
          network.location_id +
          "' class='details'>" +
          seeDetails +
          "</div>") +
      "</div>";

    popup.setContent(content);
    this.selectionLayers.addLayer(popup);

    // Create the click handler for the Details link
    if (Object.is(network, null) === false) {
      document.querySelector("#details-" + network.location_id).onclick = e => {
        let id = e.target.id.replace("details-", "");
        store.dispatch(push("/location/" + id));
      };
    }
  },

  highlightNetwork: function(network) {
    this.highlightLayers.clearLayers();

    axios
      .get(API_ROOT + "/locations/" + network.location_id + "/trails", {
        responseType: "json",
        timeout: 20000
      })
      .then(response => {
        this.highlightTrails({
          trailLayers: this.trailsToGeoJSON(response.data).getLayers(),
          popup: false
        });
      });
  }
};
