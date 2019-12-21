import math

from collections import defaultdict


def path_modifier(path):
    length = 0.0 if path.lgth is None or math.isnan(path.lgth) else path.lgth
    return {"id": path.pk, "length": length}


def get_key_optimizer():
    next_id = iter(range(1, 1000000))
    mapping = defaultdict(lambda: next(next_id))
    return lambda x: mapping[x]


def graph_edges_nodes(qs):
    """
    return a graph on the form:
    nodes {
        coord_point_a {
            coord_point_b: edge_id
        }
    }
    edges {
        edge_id: {
            nodes: [point_a, point_b, ...]
            ** extra settings (length etc.)
        }
    }


    coord_point are tuple of float
    """

    key_modifier = get_key_optimizer()
    value_modifier = path_modifier

    edges = defaultdict(dict)
    nodes = defaultdict(dict)

    for path in qs:
        coords = path.shape_2d.coords
        start_point, end_point = coords[0], coords[-1]
        k_start_point, k_end_point = key_modifier(start_point), key_modifier(end_point)

        v_path = value_modifier(path)
        v_path["nodes_id"] = [k_start_point, k_end_point]
        edge_id = v_path["id"]

        nodes[k_start_point][k_end_point] = edge_id
        nodes[k_end_point][k_start_point] = edge_id
        edges[edge_id] = v_path

    return {"edges": dict(edges), "nodes": dict(nodes)}
