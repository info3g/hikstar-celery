import axios from "axios";

export const searchMethods = {
  isWidgetPage() {
    return mapStyle === "widget";
  },
  getQueryString(query) {
    return Object.keys(query)
      .map(key => key + "=" + query[key])
      .join("&");
  },
  getIconName(itemType) {
    switch (itemType) {
      case "mountain":
        return "sommet.png";
      case "municipality":
        return "ville.png";
      case "network":
        return "reseau.png";
      case "location":
        return "sentier.png";
      case "trail":
        return "sentier.png";
      case "region":
        return "region_touristique.png";
    }
    return "";
  },
  getSuggestionIcon(itemType) {
    return `/static/img/icons/autocomplete/${this.getIconName(itemType)}`;
  },
  fetchSuggestions() {
    const url = `${API_URL}search/`;
    const query = {
      search_term: this.searchTerm.split(" ").join("+"),
      include: "location_id,name,object_type,type"
    };
    if (this.isWidgetPage()) {
      if (widgetLocations) { query['locations'] = widgetLocations; }
    }
    const queryString = this.getQueryString(query);
    axios.get(`${url}?${queryString}`).then(response => {
      this.suggestions = response.data;
    });
  }
};
