import importlib
import yaml
import networkx as nx
# from index.index_registry import get_paper_ids_for_scope

class GraphNode:
    def __init__(self, node_id, node_dict):
        self.id = node_id
        self.type = node_dict.get("type")
        self.mode = node_dict.get("mode")
        self.handler = node_dict.get("handler")
        self.inputs = node_dict.get("inputs", [])
        self.retrieval_strategy = node_dict.get("retrieval_strategy", "tag")
        self.paper_id = node_dict.get("paper_id")
        self.operator_id = node_dict.get("operator_id")
        self.db_name = node_dict.get("db_name", "paper_sections")

    def is_local(self):
        return self.mode == "local"

    def is_global(self):
        return self.mode == "global"

def load_handler(dotted_path):
    module_path, func_name = dotted_path.rsplit(".", 1)
    module = importlib.import_module(module_path)
    return getattr(module, func_name)

def expand_operator_graph(config):
    papers = config["task_scope"]["query"].split(",")
    print(f"Expanding operator graph with papers: {papers}")
    G = nx.DiGraph()
    node_map = {}

    for node in config["nodes"]:
        base_id = node["id"]
        if node.get("mode") == "local":
            node_map[base_id] = []
            for pid in papers:
                new_id = f"{base_id}__{pid}"
                new_node = node.copy()
                new_node.update({
                    "id": new_id,
                    "paper_id": pid,
                    "operator_id": base_id
                })
                G.add_node(new_id, data=GraphNode(new_id, new_node))
                node_map[base_id].append(new_id)
        else:
            G.add_node(base_id, data=GraphNode(base_id, node))
            node_map[base_id] = [base_id]

    edges = config.get("edges", [])

    if not edges:
        print("Warning: No edges defined in the configuration. Proceeding without edges.")
        # Return an empty graph or handle as needed
        return G, papers
    for edge in edges:
        from_id = edge["from"]
        to_id = edge["to"]
        if "[*]" in from_id:
            logical_id = from_id.replace("[*]", "")
            for fid in node_map.get(logical_id, []):
                G.add_edge(fid, to_id)
        elif "[*]" in to_id:
            logical_id = to_id.replace("[*]", "")
            for tid in node_map.get(logical_id, []):
                G.add_edge(from_id, tid)
        else:
            G.add_edge(from_id, to_id)

    return G, papers