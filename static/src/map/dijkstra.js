const Geotrek = {};

Geotrek.TopologyHelper = (function() {
  /**
   * This static function takes a list of Dijkstra results, and returns
   * a serialized topology, as expected by form widget, as well as a
   * multiline geometry for highlight the result.
   */
  function buildSubTopology(paths, polylines, ll_start, ll_end, offset) {
    var polyline_start = polylines[0],
      polyline_end = polylines[polylines.length - 1],
      single_path = paths.length == 1,
      cleanup = true,
      positions = {};

    if (!polyline_start || !polyline_end) {
      console.error("Could not compute distances without polylines.");
      return null; // TODO: clean-up before give-up ?
    }

    var pk_start = L.GeometryUtil.locateOnLine(
        polyline_start._map,
        polyline_start,
        ll_start
      ),
      pk_end = L.GeometryUtil.locateOnLine(
        polyline_end._map,
        polyline_end,
        ll_end
      );

    console.debug(
      "Start on layer " +
        polyline_start.feature.properties.pk +
        " " +
        pk_start +
        " " +
        ll_start.toString()
    );
    console.debug(
      "End on layer " +
        polyline_end.feature.properties.pk +
        " " +
        pk_end +
        " " +
        ll_end.toString()
    );

    if (single_path) {
      var path_pk = paths[0],
        lls = polyline_start.getLatLngs();

      const single_path_loop = lls[0].equals(lls[lls.length - 1]);
      if (single_path_loop) cleanup = false;

      if (single_path_loop && Math.abs(pk_end - pk_start) > 0.5) {
        /*
         *        A
         *     //=|---+
         *   +//      |   It is shorter to go through
         *    \\      |   extremeties than the whole loop
         *     \\=|---+
         *        B
         */
        if (pk_end - pk_start > 0.5) {
          paths = [path_pk, path_pk];
          positions[0] = [pk_start, 0.0];
          positions[1] = [1.0, pk_end];
        } else if (pk_end - pk_start < -0.5) {
          paths = [path_pk, path_pk];
          positions[0] = [pk_end, 0.0];
          positions[1] = [1.0, pk_start];
        }
      } else {
        /*        A     B
         *   +----|=====|---->
         *
         *        B     A
         *   +----|=====|---->
         */
        paths = $.unique(paths);
        positions[0] = [pk_start, pk_end];
      }
    } else if (paths.length == 3 && polyline_start == polyline_end) {
      var start_lls = polylines[0].getLatLngs(),
        mid_lls = polylines[1].getLatLngs();
      cleanup = false;
      if (pk_start < pk_end) {
        positions[0] = [pk_start, 0.0];
        if (start_lls[0].equals(mid_lls[0])) positions[1] = [0.0, 1.0];
        else positions[1] = [1.0, 0.0];
        positions[2] = [1.0, pk_end];
      } else {
        positions[0] = [pk_start, 1.0];
        if (start_lls[0].equals(mid_lls[0])) positions[1] = [1.0, 0.0];
        else positions[1] = [0.0, 1.0];
        positions[2] = [0.0, pk_end];
      }
    } else {
      /*
       * Add first portion of line
       */
      var start_lls = polyline_start.getLatLngs(),
        first_end = start_lls[start_lls.length - 1],
        start_on_loop = start_lls[0].equals(first_end);

      if (L.GeometryUtil.startsAtExtremity(polyline_start, polylines[1])) {
        var next_lls = polylines[1].getLatLngs(),
          next_end = next_lls[next_lls.length - 1],
          share_end = first_end.equals(next_end),
          two_paths_loop = first_end.equals(next_lls[0]);
        if (
          (start_on_loop && pk_start > 0.5) ||
          (share_end && pk_start + pk_end >= 1) ||
          (two_paths_loop && pk_start - pk_end > 0)
        ) {
          /*
           *       A
           *    /--|===+    B
           *  +/       \\+==|---
           *   \       /
           *    \-----+
           *
           *        A               B
           *   +----|------><-------|----
           *
           *   +----|=====|><=======|----
           *
           */
          positions[0] = [pk_start, 1.0];
        } else {
          /*
           *        A               B
           *   <----|------++-------|----
           *
           *   <----|=====|++=======|----
           *
           */
          positions[0] = [pk_start, 0.0];
        }
      } else {
        /*
         *        A               B
         *   +----|------>+-------|----
         *
         *   +----|=====|>+=======|----
         *
         */
        positions[0] = [pk_start, 1.0];
      }

      /*
       * Add all intermediary lines
       */
      for (var i = 1; i < polylines.length - 1; i++) {
        var previous = polylines[i - 1],
          polyline = polylines[i];
        if (L.GeometryUtil.startsAtExtremity(polyline, previous)) {
          positions[i] = [0.0, 1.0];
        } else {
          positions[i] = [1.0, 0.0];
        }
      }

      /*
       * Add last portion of line
       */
      var end_lls = polyline_end.getLatLngs(),
        last_end = end_lls[end_lls.length - 1],
        end_on_loop = end_lls[0].equals(last_end);

      if (
        L.GeometryUtil.startsAtExtremity(
          polyline_end,
          polylines[polylines.length - 2]
        )
      ) {
        var previous_lls = polylines[polylines.length - 2].getLatLngs(),
          previous_end = previous_lls[previous_lls.length - 1],
          share_end = last_end.equals(previous_end),
          two_paths_loop = last_end.equals(previous_lls[0]);
        if (
          (end_on_loop && pk_end > 0.5) ||
          (share_end && pk_start + pk_end >= 1) ||
          (two_paths_loop && pk_start - pk_end <= 0)
        ) {
          /*
           *              B
           *     A    //==|-+
           *  ---|==+//     |
           *         \      |
           *          \-----+
           *
           *        A               B
           *   -----|------><-------|----+
           *
           *   -----|======>|+======>---->
           */
          positions[polylines.length - 1] = [1.0, pk_end];
        } else {
          /*
           *        A               B
           *   -----|------++-------|---->
           *
           *   -----|======+|=======>---->
           */
          positions[polylines.length - 1] = [0.0, pk_end];
        }
      } else {
        /*
         *        A               B
         *   -----|------+<-------|----+
         *
         *   -----|=====|+<=======|----+
         */
        positions[polylines.length - 1] = [1.0, pk_end];
      }
    }

    // Clean-up :
    // We basically remove all points where position is [x,x]
    // This can happen at extremity points...

    if (cleanup) {
      var cleanpaths = [],
        cleanpositions = {};
      for (var i = 0; i < paths.length; i++) {
        var path = paths[i];
        if (i in positions) {
          if (
            positions[i][0] != positions[i][1] &&
            cleanpaths.indexOf(path) == -1
          ) {
            cleanpaths.push(path);
            cleanpositions[i] = positions[i];
          }
        } else {
          cleanpaths.push(path);
        }
      }
      paths = cleanpaths;
      positions = cleanpositions;
    }

    // Safety warning.
    if (paths.length === 0)
      console.error(
        "Empty topology. Expect problems. (" +
          JSON.stringify({ positions: positions, paths: paths }) +
          ")"
      );

    return {
      offset: offset, // Float for offset
      positions: positions, // Positions on paths
      paths: paths // List of pks
    };
  }

  /**
   * @param topology {Object} with ``offset``, ``positions`` and ``paths`` as returned by buildSubTopology()
   * @param idToLayer {function} callback to obtain layer from id
   * @returns L.Polyline
   */
  function buildGeometryFromTopology(topology, idToLayer) {
    var latlngs = [];
    for (var i = 0; i < topology.paths.length; i++) {
      var path = topology.paths[i],
        positions = topology.positions[i],
        polyline = idToLayer(path);
      if (positions) {
        const points = L.GeometryUtil.extract(
          polyline._map,
          polyline,
          positions[0],
          positions[1]
        );
        latlngs.push(points.map(i => [i.lat, i.lng]));
      } else {
        console.warn(
          "Topology problem: " +
            i +
            " not in " +
            JSON.stringify(topology.positions)
        );
      }
    }
    return L.polyline(latlngs);
  }

  /**
   * @param idToLayer : callback to obtain a layer object from a pk/id.
   * @param data : computed_path
   */
  function buildTopologyFromComputedPath(idToLayer, data) {
    if (!data.computed_paths) {
      return {
        layer: null,
        serialized: null
      };
    }

    var computed_paths = data["computed_paths"],
      edges = data["new_edges"],
      offset = 0.0, // TODO: input for offset
      data = [],
      layer = L.featureGroup();

    console.debug("----");
    console.debug("Topology has " + computed_paths.length + " sub-topologies.");

    for (var i = 0; i < computed_paths.length; i++) {
      const cpath = computed_paths[i];
      const paths = [];
      const polylines = [];
      // const paths = edges[i][0].map(edge => edge.id);
      // const polylines = edges[i][0].map(edge => idToLayer(edge.id));

      for (const item of edges[i]) {
        for (const edge of item) {
            paths.push(edge.id);
            polylines.push(idToLayer(edge.id));
        }
      }

      const topo = buildSubTopology(
        paths,
        polylines,
        cpath.from_pop.ll,
        cpath.to_pop.ll,
        offset
      );
      if (topo === null) break;

      data.push(topo);
      console.debug("subtopo[" + i + "] : " + JSON.stringify(topo));

      // Geometry for each sub-topology
      const group_layer = buildGeometryFromTopology(topo, idToLayer);
      group_layer.from_pop = cpath.from_pop;
      group_layer.to_pop = cpath.to_pop;
      group_layer.step_idx = i;
      layer.addLayer(group_layer);
    }
    console.debug("----");

    return {
      layer: layer,
      serialized: data
    };
  }

  return {
    buildTopologyFromComputedPath: buildTopologyFromComputedPath
  };
})();

Geotrek.getNextId = (function() {
  var next_id = 100000;
  return function() {
    return next_id++;
  };
})();

// pol: point on polyline
Geotrek.PointOnPolyline = function(options) {
  this.origLatLng = options.origLatLng;
  this.marker = options.marker;
  this.ll = options.ll;
  this.polyline = options.polyline;
  this.path_length = options.path_length;
  this.percent_distance = options.percent_distance;
};

Geotrek.PointOnPolyline.prototype.isValid = function() {
  return this.ll && this.polyline;
};

// Alter the graph: adding two edges and one node (the polyline gets break in two parts by the point)
// The polyline MUST be an edge of the graph.
Geotrek.PointOnPolyline.prototype.addToGraph = function(graph) {
  if (!this.isValid()) return null;

  var self = this;

  var edge = graph.edges[this.polyline.feature.properties.pk],
    first_node_id = edge.nodes_id[0],
    last_node_id = edge.nodes_id[1];

  // To which nodes dist start_point/end_point corresponds ?
  // The edge.nodes_id are ordered, it corresponds to polylines: coords[0] and coords[coords.length - 1]
  var dist_start_point = this.percent_distance * this.path_length,
    dist_end_point = (1 - this.percent_distance) * this.path_length;
  var new_node_id = Geotrek.getNextId();

  var edge1 = {
    id: Geotrek.getNextId(),
    length: dist_start_point,
    nodes_id: [first_node_id, new_node_id]
  };
  var edge2 = {
    id: Geotrek.getNextId(),
    length: dist_end_point,
    nodes_id: [new_node_id, last_node_id]
  };

  var first_node = {},
    last_node = {},
    new_node = {};
  first_node[new_node_id] = new_node[first_node_id] = edge1.id;
  last_node[new_node_id] = new_node[last_node_id] = edge2.id;

  // <Alter Graph>
  var new_edges = {};
  new_edges[edge1.id] = graph.edges[edge1.id] = edge1;
  new_edges[edge2.id] = graph.edges[edge2.id] = edge2;

  graph.nodes[new_node_id] = new_node;
  $.extend(graph.nodes[first_node_id], first_node);
  $.extend(graph.nodes[last_node_id], last_node);
  // </Alter Graph>

  function rmFromGraph() {
    delete graph.edges[edge1.id];
    delete graph.edges[edge2.id];

    delete graph.nodes[new_node_id];
    delete graph.nodes[first_node_id][new_node_id];
    delete graph.nodes[last_node_id][new_node_id];
  }

  return {
    self: self,
    new_node_id: new_node_id,
    new_edges: new_edges,
    dist_start_point: dist_start_point,
    dist_end_point: dist_end_point,
    initial_edge: edge,
    rmFromGraph: rmFromGraph
  };
};

Geotrek.Dijkstra = (function() {
  // TODO: doc
  function get_shortest_path_from_graph(
    graph,
    from_ids,
    to_ids,
    exclude_from_to
  ) {
    // coerce int to string
    from_ids = from_ids.map(k => "" + k);
    to_ids = to_ids.map(k => "" + k);

    var graph_nodes = graph.nodes;
    var graph_edges = graph.edges;

    function getPairWeightNode(node_id) {
      var l = [];
      $.each(graph_nodes[node_id], function(node_dest_id, edge_id) {
        // Warning - weight is in fact edge.length in our data
        l.push({ node_id: node_dest_id, weight: graph_edges[edge_id].length });
      });
      return l;
    }

    function is_source(node_id) {
      return from_ids.indexOf(node_id) != -1;
    }
    function is_destination(node_id) {
      return to_ids.indexOf(node_id) != -1;
    }

    var djk = {};

    // weight is smallest so far: take it whatever happens
    from_ids.forEach(function(node_id) {
      djk[node_id] = { prev: null, node: node_id, weight: 0, visited: false };
    });

    // return the ID of an unvisited node that has the less weight (less djk weight)
    // TODO: performance -> shoud not contain visited node, should be sorted by weight
    function djk_get_next_id() {
      var nodes_id = Object.keys(djk);
      var mini_weight = Number.MAX_VALUE;
      var mini_id = null;
      var node_djk = null;
      var weight = null;

      for (var k = 0; k < nodes_id.length; k++) {
        var node_id = nodes_id[k];
        node_djk = djk[node_id];
        weight = node_djk.weight;

        // if already visited - skip
        if (node_djk.visited === true) continue;

        // Weight can't get lower - take it
        if (weight == 0) return node_id;

        // Otherwise try to find the minimum
        if (weight < mini_weight) {
          mini_id = node_id;
          mini_weight = weight;
        }
      }
      return mini_id;
    }

    var djk_current_node, current_node_id;

    while (true) {
      // Get the next node to visit
      djk_current_node = djk_get_next_id();

      // Last node exhausted - we didn't find a path
      if (djk_current_node === null) return null;

      // The node exist
      var current_djk_node = djk[djk_current_node];
      // Mark as visited (won't be chosen)
      current_djk_node.visited = true;
      // we could del it out of djk

      current_node_id = current_djk_node.node;

      // Last point
      if (is_destination(current_node_id)) break;

      // refactor to get next
      var pairs_weight_node = getPairWeightNode(current_node_id);

      // if current_djk_node.weight > ... BREAK
      for (var i = 0; i < pairs_weight_node.length; i++) {
        var edge_weight = pairs_weight_node[i].weight;
        var next_node_id = pairs_weight_node[i].node_id;

        var next_weight = current_djk_node.weight + edge_weight;

        var djk_next_node = djk[next_node_id];

        // push new node or update it
        if (djk_next_node) {
          // update node ?
          if (djk_next_node.visited === true) continue;

          // If its weight is inferior, this node has a better previous edge already
          // Do not update it
          if (djk_next_node.weight < next_weight) continue;

          djk_next_node.weight = next_weight;
          djk_next_node.prev = current_djk_node;
        } else {
          // push node
          djk[next_node_id] = {
            prev: current_djk_node,
            node: next_node_id,
            weight: next_weight,
            visited: false
          };
        }
      }
    }

    var path = [];
    // Extract path
    // current_djk_node is the destination
    var final_weight = current_djk_node.weight;
    var tmp = current_djk_node;
    while (!is_source(tmp.node)) {
      path.push(tmp.node);
      tmp = tmp.prev;
    }

    if (exclude_from_to) {
      path.shift(); // remove last node
    } else {
      path.push(tmp.node); // push first node
    }

    // miss first and last step
    path.reverse();

    var i,
      j,
      full_path = [];
    for (i = 0; i < path.length - 1; i++) {
      var node_1 = path[i],
        node_2 = path[i + 1];
      var edge = graph_edges[graph_nodes[node_1][node_2]];

      // start end and edge are just ids
      full_path.push({
        start: node_1,
        end: node_2,
        edge: edge,
        weight: edge.length
      });
    }

    return {
      path: full_path,
      weight: final_weight
    };
  }

  return {
    get_shortest_path_from_graph: get_shortest_path_from_graph
  };
})();

// Computed_paths:
//
// Returns:
//   Array of {
//       path : Array of { start: Node_id, end: Node_id, edge: Edge, weight: Int (edge.length) }
//       weight: Int
//   }
//
Geotrek.shortestPath = (function() {
  function computePaths(graph, steps) {
    /*
     *  Returns list of paths, and null if not found.
     */
    var paths = [];
    for (var j = 0; j < steps.length - 1; j++) {
      var path = computeTwoStepsPath(graph, steps[j], steps[j + 1]);
      if (!path) return null;

      path.from_pop = steps[j];
      path.to_pop = steps[j + 1];
      paths.push(path);
    }
    return paths;
  }

  function computeTwoStepsPath(graph, from_pop, to_pop) {
    // alter graph
    var from_pop_opt = from_pop.addToGraph(graph),
      to_pop_opt = to_pop.addToGraph(graph);

    var from_nodes = [from_pop_opt.new_node_id],
      to_nodes = [to_pop_opt.new_node_id];

    // weighted_path: {
    //   path : Array of { start: Node_id, end: Node_id, edge: Edge, weight: Int (edge.length) }
    //   weight: Int
    // }

    var weighted_path = Geotrek.Dijkstra.get_shortest_path_from_graph(
      graph,
      from_nodes,
      to_nodes
    );

    // restore graph
    from_pop_opt.rmFromGraph();
    to_pop_opt.rmFromGraph();

    if (!weighted_path) return null;

    // Some path component may use an edge that does not belong to the graph
    // (a transient edge that was created from a transient point - a marker).
    // In this case, the path component gets a new `real_edge' attribute
    // which is the edge that the virtual edge is part of.
    var pops_opt = [from_pop_opt, to_pop_opt];
    $.each(weighted_path.path, function(i, path_component) {
      var edge_id = path_component.edge.id;
      // Those PointOnPolylines knows the virtual edge and the initial one
      for (var i = 0; i < pops_opt.length; i++) {
        var pop_opt = pops_opt[i],
          edge = pop_opt.new_edges[edge_id];
        if (edge !== undefined) {
          path_component.real_edge = pop_opt.initial_edge;
          break;
        }
      }
    });
    return weighted_path;
  }

  return computePaths;
})();

export default Geotrek;
