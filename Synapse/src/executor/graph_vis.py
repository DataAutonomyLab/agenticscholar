# import matplotlib.pyplot as plt
# import networkx as nx

# def draw_dag(G, title="Prompt Graph"):
#     pos = nx.spring_layout(G, seed=42)
#     labels = {n: n for n in G.nodes}
#     color_map = ["lightblue" if G.nodes[n]["data"].mode == "local" else "lightgreen" for n in G.nodes]

#     plt.figure(figsize=(12, 8))
#     nx.draw(G, pos, with_labels=True, labels=labels, node_color=color_map, node_size=2000, font_size=10, font_weight="bold", edge_color="gray")
#     plt.title(title)
#     plt.show()

from pyvis.network import Network
import networkx as nx

def draw_dag(G, plan_id, title="Prompt Graph (Interactive)"):
    net = Network(notebook=True, directed=True, heading=title, height="750px", width="100%")

    # Add nodes
    default_color = "lightgrey"
    for n in G.nodes:
        node_data = G.nodes[n].get("data")
        mode = getattr(node_data, "mode", None) if node_data else None
        color = "lightblue" if mode == "local" else "lightgreen" if mode else default_color
        # Pyvis uses 'id' which must be string if node itself isn't string/int
        node_id = str(n)
        net.add_node(node_id, label=str(n), title=f"Node: {n}\nMode: {mode}", color=color, size=25) # title appears on hover

    # Add edges
    for u, v in G.edges:
        net.add_edge(str(u), str(v))

    # You can optionally add physics configuration buttons to tweak layout in the browser
    # net.show_buttons(filter_=['physics'])
    filename = f'test/outputs/{plan_id}_dag.html'
    net.show(filename)
    print(f"Interactive graph saved to {filename}")

# Example Usage (assuming G is your NetworkX DiGraph)
# draw_dag_pyvis(G)