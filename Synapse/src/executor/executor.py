import logging
from src.index.weaviate_instance import WeaviateIndexer
from src.executor.dependency_graph import load_handler
import networkx as nx
import time
import tiktoken

logging.basicConfig(level=logging.INFO)

SEARCH_VERSION = "v2"
ALPHA = 0.3

def count_tokens(text: str, model_name: str = "gpt-4") -> int:
    """
    Counts the number of tokens in a text string using the tokenizer for a specific model.

    Args:
        text: The string to count tokens for.
        model_name: The name of the model to use for tokenization (e.g., "gpt-4", "gpt-3.5-turbo").

    Returns:
        The total number of tokens in the string.
    """
    try:
        # Get the encoding for the specified model.
        # This will download the tokenizer definition on its first run.
        encoding = tiktoken.encoding_for_model(model_name)
    except KeyError:
        print(f"Warning: Model '{model_name}' not found. Using 'cl100k_base' encoding as a default.")
        # 'cl100k_base' is the encoding used by the gpt-4 and gpt-3.5-turbo family
        encoding = tiktoken.get_encoding("cl100k_base")

    # Encode the text into a list of token integers
    tokens = encoding.encode(text)

    # Return the length of the list
    return len(tokens)

class StateManager:
    def __init__(self, db_name):
        self.indexer = WeaviateIndexer(db_name=db_name)
        self.data = {}

    def set_output(self, node_id, value):
        self.data[node_id] = value

    def get_output(self, node_id):
        return self.data.get(node_id)

    def get_outputs_by_operator(self, operator_id):
        return {k: v for k, v in self.data.items() if k.startswith(operator_id + "__")}

def resolve_inputs(node, state_mgr):
    resolved = []
    query_text = None
    tags = []

    for key in node.inputs:
        if key.startswith("output["):
            node_key = key[8:-2]

            if node_key.endswith("[*]"):
                print(f"Wildcard output detected: {node_key}")
                base_id = node_key[:-3]
                outputs = state_mgr.get_outputs_by_operator(base_id)
                resolved.append(list(outputs.values()))

            else:
                print(f"Resolving output for key: {node_key}")
                resolved.append(state_mgr.get_output(node_key))

        elif key.startswith("retrieval_query["):
            query_text = key[16:-1]  # Get the text inside retrieval_query["..."]

        elif key.startswith("section["):
            tag = key[8:-1]
            tags.append(tag)
        else:
            raise ValueError(f"Unknown input key: {key}")

    if node.is_local():
        s_ = time.time()
        print(f"Local node detected: {node.id}, {query_text}, {tags}, {node.paper_id}")
        search_result = state_mgr.indexer.search_weaviatev2(
            query_text=query_text,
            paper_id=node.paper_id,
            tags=tags if tags else None,
            db_name=getattr(node, "db_name", "paper_sections"),
            alpha=ALPHA
        )
        print('Query text:', query_text)
        if query_text:
            resolved.append(query_text)
        v= '\n'.join(['Paper ID:{' + meta.properties['paper_id'] + '} ## ' + 'Title:' + meta.properties['section_title'] + ' ## Tables and Figures (if have):' + str(meta.properties['vis_elements']) + ' ## Text:' + meta.properties['section_text'] for meta in search_result])
        resolved.append(v)
        e_ = time.time()
        print(f"Local node search time: {e_ - s_:.2f} seconds")
    return resolved


def run_graph(db_name, G):
    state_mgr = StateManager(db_name)
    for node_id in list(nx.topological_sort(G)):
        node = G.nodes[node_id]["data"]
        handler = load_handler(node.handler)

        logging.info(f"[START] Node: {node.id}")
        # FLAG = False # node.is_local() ### for testing
        # if FLAG:
        s_ = time.time()
        inputs = resolve_inputs(node, state_mgr)
        result = handler(*inputs)                        
        e_ = time.time()
        logging.info(f"Time taken for node {node.id}: {e_ - s_:.2f} seconds")
                    
        logging.info(f"[END] Node: {node.id}")
        print(f"Node {node.id} completed with total tokens: {count_tokens(str(result))}")
        state_mgr.set_output(node.id, result)

    return state_mgr.data
