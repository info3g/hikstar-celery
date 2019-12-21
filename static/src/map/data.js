export const MapHikster = {
  LIGHT_GREEN: "#5e9c35", // RGB 94,156,53
  DARK_GREEN: "#4e822c", // RGB 78,130,44
  BLACK_GREEN: "#345D26", // RGB 52,93,38
  GREY: "#8e8e8e", // RGB 142, 142, 142
  RED: "#ff0000",
  BLUE: "#3388ff",
  WHITE: "#ffffff",
  CLAIRE_LIGHT_GREEN: "#ace268", // RGB 172,226,104
  ORANGE: "#f18f01", // RGB 241,143,1

  // MAP SERVICE LAYERS
  LAYER_POI: 0,
  LAYER_TRAIL_SECTION: 1, // No longer used here but still in map service for AppCo,
  LAYER_INCOMPLETE_TRAIL_SECTION: 2, // No longer used here but still in map service for AppCo,
  LAYER_NETWORK: 3,
  LAYER_REGION: 4,
  LAYER_TRAIL: 5,
  LAYER_INCOMPLETE_TRAIL: 6,

  ZOOM_FITBOUNDS: 0,
  ZOOM_FLYTO: 1
};

export const Sport = {
  RANDONNEE: 1,
  RAQUETTE: 2,
  RANDONNEE_HIVERNALE: 3,
  VELO_DE_MONTAGNE: 4,
  FATBIKE: 5,
  VELO: 6,
  SKI_DE_FOND: 7,
  EQUITATION: 8,
  ALL: 100
};

export const mapData = {
  geoJSON: null,
  baseMapConfig: {
    center: [50.13466432216696, -72.72949218750001],
    zoom: 6,
    zoomControl: false,
    zoomAnimation: true,
    minZoom: 3,
    maxZoom: 17
  },
  poiCategories: [
    {
      types: []
    }
  ],
  sport: null,
  refreshAllTheThings: null,
  map: null,
  layerSelection: [],
  incompleteMarkers: null,
  incompleteClusters: null,
  networkLayer: null,
  regionFeatureLayer: null,
  timer: null,
  trailClientLayer: null,
  trailPopup: null,
  mapServer: "",
  mapService: "",
  tileLayers: [],
  latestRegionMouseOver: null,

  resultLayers: null,
  selectionLayers: null,
  highlightLayers: null,
  attribution: "",

  // Trail difficulty
  formattedDifficulty: {
    1: "Débutant",
    2: "Modéré",
    3: "Intermédiaire",
    4: "Soutenu",
    5: "Exigeant"
  },

  config: {
    basemap: "Topographic",
    elevation: false,
    scale: true,
    delormeBasemap: true,
    scrollWheelZoom: true,
    showRegionLayer: false
  },

  // Point of interest layer + symbols
  poiVisibility: true,
  pointOfInterestLayer: null,
  poiClusterGroup: null,

  defaultTrailStyle: {
    color: MapHikster.BLACK_GREEN,
    weight: 3,
    opacity: 1
  },
  resultTrailStyle: {
    color: MapHikster.BLACK_GREEN,
    weight: 3,
    opacity: 1
  },
  selectedTrailStyle: {
    color: MapHikster.BLACK_GREEN,
    weight: 3,
    opacity: 1
  },
  highlightHaloTrailStyle: {
    color: MapHikster.ORANGE,
    weight: 7,
    opacity: 1
  },
  selectHaloTrailStyle: {
    color: MapHikster.ORANGE,
    weight: 7,
    opacity: 1
  },
  selectHaloTrailStyleHidden: {
    color: MapHikster.WHITE,
    weight: 7,
    opacity: 0
  },
  resultHaloTrailStyle: {
    color: MapHikster.CLAIRE_LIGHT_GREEN,
    weight: 7,
    opacity: 1
  },

  // Fill is required for mouseover/mouseout to work properly, even if fill transparent
  regionPolygonStyle: {
    color: "#fff",
    weight: 1,
    opacity: 1.0,
    fill: true,
    fillColor: "#fff",
    fillOpacity: 0.0
  },
  highlightRegionPolygonStyle: {
    color: "#fff",
    weight: 1,
    opacity: 1.0,
    fill: true,
    fillColor: "#fff",
    fillOpacity: 0.6
  },

  incompleteIcon50: L.icon({
    iconSize: [9, 10],
    iconAnchor: [4, 10],
    iconUrl: "/static/img/markers/incomplete_pin_50.png"
  }),
  incompleteIcon50Hover: L.icon({
    iconSize: [9, 10],
    iconAnchor: [4, 10],
    iconUrl: "/static/img/markers/incomplete_pin_50_hover.png"
  }),
  incompleteIcon100: L.icon({
    iconSize: [5, 5],
    iconAnchor: [2, 2],
    iconUrl: "/static/img/markers/incomplete_pin_100.png"
  }),
  incompleteIcon100Hover: L.icon({
    iconSize: [5, 5],
    iconAnchor: [2, 2],
    iconUrl: "/static/img/markers/incomplete_pin_100_hover.png"
  })
};
