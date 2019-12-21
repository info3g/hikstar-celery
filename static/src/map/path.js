export const pathMethods = {
  showPathGeom(layer) {
    // This piece of code was moved from formfield.js, its place is here,
    // not around control instantiation. Of course this is not very elegant.
    const self = this;
    if (!this.markPath)
      this.markPath = (() => {
        let current_path_layer = null;
        return {
          updateGeom: function(new_path_layer) {
            const prev_path_layer = current_path_layer;
            current_path_layer = new_path_layer;

            if (prev_path_layer) {
              self.map.removeLayer(prev_path_layer);
            }

            if (new_path_layer) {
              self.map.addLayer(new_path_layer);
              new_path_layer.setStyle({
                color: "yellow",
                weight: 5,
                opacity: 0.8
              });
              new_path_layer.eachLayer((l) => {
                if (typeof l.setText == "function") {
                  l.setText(">  ", {
                    repeat: true,
                    attributes: { fill: "#FF5E00" }
                  });
                }
              });
              self.pathLayer = new_path_layer;
            }
          }
        };
      })();
    this.markPath.updateGeom(layer);
  },
  onComputedPaths(data) {
    const topology = this.geotrek.TopologyHelper.buildTopologyFromComputedPath(
      this.idToLayer,
      data
    );
    this.topology = topology;
    this.showPathGeom(topology.layer);
    // this.fire("computed_topology", { topology: topology.serialized });
  }
};
