from src.executor.dependency_graph import expand_operator_graph
# from src.executor.executor import run_graph
from src.executor.executor_cc import run_graph
from src.executor.executor_utils import is_json
# from executor.graph_vis import draw_dag
import json

def executor_entry(db_name, config) -> None:
    
    print(db_name)
    print(config)
    G, paper_ids = expand_operator_graph(config)

    # Visualize
    # draw_dag(G, plan_id)

    # print("Graph visualization complete. Exiting for review.")

    # # Execute
    outputs = run_graph(db_name, G)

    final_keys = config.get("outputs", [])
    final_results = {}

    for key in final_keys:
        if key.endswith("[*]"):
            base = key[:-3]
            for k, v in outputs.items():
                if k.startswith(base + "__"):  # e.g., extract_goal__0
                    final_results[k] = v
        else:
            if key in outputs:
                final_results[key] = outputs[key]

    # print("\n Final Outputs:")
    results = []
    for k, v in final_results.items():
        # print(f"\n {k}:\n{v}")
        results.append(str(v))
    
    return "\n".join(results)