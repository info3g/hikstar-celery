import axios from "axios";
import { MapHikster } from "@/map/data.js";

axios.defaults.xsrfHeaderName = "X-CSRFToken";
axios.defaults.withCredentials = true;

export const poiMethods = {
  getVisiblePois() {
    let poiIds = [];
    for (const category of this.poiCategories) {
      const checked = category.types
        .filter(item => item.show)
        .map(item => item.id);
      poiIds = [...poiIds, ...checked];
    }
    return poiIds.join();
  },

  showPois(geojson) {
    this.pointOfInterestLayer = L.geoJson(geojson, {
      pointToLayer: (feature, latlng) => {
        const poiType = feature.properties.type_id
          ? feature.properties.type_id
          : 0;

        return L.marker(latlng, {
          icon: L.icon({
            iconSize: [41, 41],
            iconAnchor: [20, 41], // Tip of the icon (geographical location) relative to it's top left corner
            iconUrl: "/static/img/markers/Icones_Hikster_" + poiType + ".svg"
          })
        });
      }
    });
    this.pointOfInterestLayer.on("click", this.onPointOfInterestClick);

    if (this.isAdminPoiListPage && this.isAdminPoiListPage()) {
      this.pointOfInterestLayer.on("mouseover", e => {
        const poiId = e.layer.feature.properties.pk;
        this.selectedPoiInMap = poiId;
        this.scrollToPoi(poiId);
      });

      this.pointOfInterestLayer.on("mouseout", e => {
        this.selectedPoiInMap = null;
      });
    }
    this._toggleLayer(this.poiClusterGroup);

    this.poiClusterGroup = L.markerClusterGroup({
      maxClusterRadius: 50,
      spiderLegPolylineOptions: {
        weight: 1.5,
        color: "#7ec450",
        opacity: 1
      },
      spiderfyDistanceMultiplier: 2,
      zoomToBoundsOnClick: false,
      showCoverageOnHover: false,
      spiderifyOnMaxZoom: false, // [YB 2016-11-14: Handle the spiderfy ourselves, at all zoom levels on clusterclick]
      iconCreateFunction: cluster => {
        return L.icon({
          iconSize: [41, 41],
          iconAnchor: [20, 41], // Tip of the icon (geographical location) relative to it's top left corner
          iconUrl: "/static/img/markers/Icones_Hikster_cluster.svg"
        });
      }
    });

    this.poiClusterGroup.on("clusterclick", a => {
      a.layer.spiderfy();
    });

    // Bulk add all the POI to the cluster layer
    this.poiClusterGroup.addLayers(this.pointOfInterestLayer.getLayers());

    this.map.addLayer(this.poiClusterGroup);

    //[YB 2016-08-10: Warning: When using the Tangram map, for an unknown reason, the marker clusters won't display after a pan or a zoom. This is a workaround to force the clusters to display. This is not a fix, it's a workaround. It may break in future MarkerClusters versions.]
    setTimeout(() => {
      this.poiClusterGroup._moveEnd();
    }, 0);
  },

  updatePOIClusters() {
    if (this.map.getZoom() >= 11) {
      let poiVisibility = this.getVisiblePois();
      let query = L.esri.query({
        url:
          this.mapServer +
          this.mapService +
          "/MapServer/" +
          MapHikster.LAYER_POI,
        useCors: false
      });
      query.within(this.map.getBounds());
      if (!Object.is(poiVisibility, null)) {
        query.where("type_id IN (" + poiVisibility + ")");
      }
      query.run((error, featureCollection, response) => {
        this.showPois(featureCollection);
      });
    } else {
      this._toggleLayer(this.poiClusterGroup, false);
    }
  },

  onPointOfInterestClick(e) {
    const feature = e.layer.feature;
    const objectId = feature.properties.objectid || feature.properties.pk;
    // Request to get all the POI info from the API (including adress, contact, etc..)
    const url = `${API_URL}point-of-interests/${objectId}/?expand=type,address,contact`;
    axios
      .get(url, {
        responseType: "json",
        timeout: 20000
      })
      .then(response => {
        let poi = response.data;
        let poiId = poi.poi_id;
        let premium = poi.hasOwnProperty("premium") ? poi.premium : false;
        let name = poi.name ? poi.name : "";
        let category = poi.category ? poi.category : 0;
        let description = poi.description ? poi.description : null;
        let type = poi.type && poi.type.name ? poi.type.name : null;
        let position_quality = poi.hasOwnProperty("position_quality")
          ? poi.position_quality
          : null;

        // [YB 2016/06/02: For now I won't handle multiple addresses.
        // If there is really a request for it in the future we can implement it at that point]
        let address = poi.address;
        let address_first_line =
          address && (address.street_name || address.apartment) ? true : null;
        let address_second_line = address && address.po_box ? true : null;
        let address_third_line =
          address && (address.city || address.province || address.postal_code)
            ? true
            : null;

        let poiLink = `
          <a
            class="link network"
            href="/poi/${poiId}"
            target="_blank"
          >${seeDetails}</a>
        `;
        if (IN_IFRAME) {
          poiLink = `
          <a
            class="link network"
            href="/map-widget/poi/${poiId}/?${WIDGET_PARAMS}"
            onclick="openDetailFrame(this.href); return false;"
          >${seeDetails}</a>
        `;

        }

        // Generate contacts content
        let contacts =
          poi.contact && poi.contact.length > 0 ? poi.contact : null;
        let contactsContent = "";
        if (!Object.is(contacts, null)) {
          contactsContent = "<div class='contacts'>";
          for (let contact of contacts) {
            switch (contact.type) {
              case "telephone":
                contactsContent +=
                  "<a class='contact' href='tel:" +
                  contact.value.replace(/[ -]/g, ".") +
                  "'><div class='icon phone'></div>" +
                  contact.value +
                  "</a>";
                break;
              case "email":
                contactsContent +=
                  "<a class='contact' href='mailto:" +
                  contact.value +
                  "'><div class='icon email'></div>" +
                  contact.value +
                  "</a>";
                break;
              case "site":
                contactsContent += `
                  <a class="contact" href="${contact.value}">${
                  contact.value
                }</a>
                `;
            }
          }
          contactsContent += "</div>";
        }

        let popup = L.popup({
          offset: new L.point(0, -36)
        }).setLatLng(e.latlng);

        popup.setContent(
          "<div class='lf-popup poi'>" +
            "<div class='header'>" +
            (Object.is(type, null)
              ? ""
              : "<div class='type'>" + type + "</div>") +
            "<div class='text'>" +
            name +
            "</div>" +
            "</div>" +
            "<div class='content'>" +
            (Object.is(description, null)
              ? ""
              : "<div class='description'>" + description + "</div>") +
            // (premium
            //   ? "<a id='poi-" +
            //     poiId +
            //     "' class='link poi' href='" +
            //     window.location.origin +
            //     "/point-of-interests/" +
            //     poiId +
            //     "/' target='_blank'>Voir le détail</a>"
            //   : "") +
            (Object.is(address, null)
              ? ""
              : "<div class='address'>" +
                (Object.is(address_first_line, null)
                  ? ""
                  : "<div>" +
                    (Object.is(address.street_name, null)
                      ? ""
                      : address.street_name) +
                    (Object.is(address.apartment, null)
                      ? ""
                      : ", app. " + address.apartment) +
                    "</div>") +
                (Object.is(address_second_line, null)
                  ? ""
                  : "<div>" +
                    (Object.is(address.po_box, null) ? "" : address.po_box) +
                    "</div>") +
                (Object.is(address_third_line, null)
                  ? ""
                  : "<div>" +
                    (Object.is(address.city, null) ? "" : address.city) +
                    (Object.is(address.province, null)
                      ? ""
                      : " (" + address.province + ")") +
                    (Object.is(address.postal_code, null)
                      ? ""
                      : " " + address.postal_code) +
                    "</div>") +
                "</div>") +
            contactsContent +
            "<div>" +
            poiLink +
            "</div>"
        );

        this.map.addLayer(popup);
      });
  }
};
