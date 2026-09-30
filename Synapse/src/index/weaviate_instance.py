from weaviate import connect_to_local
from weaviate.config import AdditionalConfig, Timeout 
from weaviate.classes.query import Filter
from weaviate.classes.config import Property, DataType
import weaviate.util
from sentence_transformers import SentenceTransformer

import os

DEFAULT_MODEL = os.getenv("EMBED_MODEL", "BAAI/bge-base-en-v1.5")
WEAVIATE_PORT = int(os.getenv("WEAVIATE_PORT", "8080"))
WEAVIATE_HOST = os.getenv("WEAVIATE_HOST", "localhost")
WEAVIATE_TIMEOUT = int(os.getenv("WEAVIATE_TIMEOUT", "10"))

_embedder = None
def get_embedder(model_name=DEFAULT_MODEL):
    global _embedder
    if _embedder is None:
        _embedder = SentenceTransformer(model_name)
    return _embedder

_client = None
def get_client():
    global _client
    if _client is None:
        _client = connect_to_local(
            port=WEAVIATE_PORT,
            skip_init_checks=True,
            additional_config=AdditionalConfig(timeout=Timeout(init=WEAVIATE_TIMEOUT))
        )
    return _client

def close_client():
    global _client
    if _client:
        _client.close()

class WeaviateIndexer:
    def __init__(self, db_name="ResearchSection"):
        self.db_name = db_name
        self.client = get_client()
        self.embedder = get_embedder()
        self.ensure_schema()

    def delete_collection(self):
        if self.client.collections.exists(self.db_name):
            self.client.collections.delete(self.db_name)
    
    def ensure_schema(self):
        print(f"Ensuring schema for {self.db_name}...")
        if not self.client.collections.exists(self.db_name):
            self.client.collections.create(
                name=self.db_name,
                properties=[
                    Property(name="paper_id", data_type=DataType.TEXT),
                    Property(name="section_id", data_type=DataType.TEXT),
                    Property(name="section_title", data_type=DataType.TEXT),
                    Property(name="section_text", data_type=DataType.TEXT),
                    Property(name="section_parent", data_type=DataType.TEXT),
                    Property(name="summary", data_type=DataType.TEXT),
                    Property(name="section_children", data_type=DataType.TEXT_ARRAY),
                    Property(name="section_tags", data_type=DataType.TEXT_ARRAY),
                    Property(name="chunk_id", data_type=DataType.INT),
                    Property(name="figure_table_references", data_type=DataType.TEXT_ARRAY),
                    Property(name="vis_elements", data_type=DataType.OBJECT_ARRAY,
                             nested_properties=[
                                 Property(name='caption', data_type=DataType.TEXT),
                                 Property(name='content', data_type=DataType.TEXT)
                             ]) 
                ],
                vectorizer_config=None  # Because we're using custom vectors
            )
    
    def add_section_to_index(self, sections, is_update=False):
        self.ensure_schema()
        collection = self.client.collections.get(self.db_name)

        for section in sections:
            section_id = f"{section['paper_id']}:{section['section_id']}:{section['chunk_id']}"
            document_text = section.get("section_content")
            print('section_id:', section_id)
            if not document_text:
                continue
            vector = self.embedder.encode(document_text, convert_to_tensor=True).tolist()
            data = {
                "paper_id": section["paper_id"],
                "section_id": section["section_id"],
                "section_title": section["section_title"],
                "section_text": section.get("section_content"),
                "section_parent": section.get("section_parent"),
                "summary": section.get("summary"),
                "section_children": section.get("section_children"),
                "section_tags": section["section_tags"],
                "chunk_id": section.get("chunk_id"),
                "figure_table_references": section.get("figure_table_references"),
                "vis_elements": section.get("vis_elements")
            }

            filter_section_id = Filter.by_property("section_id").equal(section["section_id"])
            filter_paper_id = Filter.by_property("paper_id").equal(section["paper_id"])
            filter_chunk_id = Filter.by_property("chunk_id").equal(section["chunk_id"])

            # Combine filters using logical AND
            combined_filter = Filter.all_of([filter_section_id, filter_paper_id, filter_chunk_id])

            # Use the combined filter in your query
            existing_object = collection.query.fetch_objects(
                filters=combined_filter,
                limit=1
            )

            # If object exists, update it, otherwise insert
            if existing_object.objects:
                if is_update:
                    existing_uuid = existing_object.objects[0].uuid
                    # print(f"Updating existing object with ID: {existing_uuid}")
                    collection.data.update(
                        uuid=existing_uuid,
                        properties=data,
                        vector=vector
                    )
            else:
                collection.data.insert(
                    uuid=weaviate.util.generate_uuid5(section_id),
                    properties=data,
                    vector=vector
                )

    def search_weaviatev2(self,
        query_text: str,
        paper_id: str = None,
        tags: list[str] = None,
        n_results: int = 5,
        db_name: str = "ResearchSection",
        alpha: float = 0.5
    ) -> list:
        """
        Search the index using hybrid search (vector + keyword).
        """
        try:
            collection = self.client.collections.get(db_name)
        except Exception as e:
            print(f"Error getting collection '{db_name}': {e}")
            # Handle error appropriately, maybe return empty list or raise
            return []

        # Build metadata filters
        filters = []
        if paper_id:
            filters.append(Filter.by_property("paper_id").equal(paper_id))
        # tags = ['Experiment']
        if tags:
            print(tags)
            # Ensure tags is a list, even if only one tag is provided
            if isinstance(tags, str):
                tags = [tags]
            if isinstance(tags, list) and len(tags) > 0:
                # Check if the property 'section_tags' exists and is configured for filtering
                # This assumes 'section_tags' is indexed appropriately in Weaviate schema
                filters.append(Filter.by_property("section_tags").contains_any(tags))
            elif tags:
                print(f"Warning: 'tags' parameter provided but is not a list or is empty: {tags}")


        combined_filter = None
        if len(filters) == 1:
            combined_filter = filters[0]
        elif len(filters) > 1:
            combined_filter = Filter.all_of(filters)

        # If no query text, perform a filtered fetch (or decide on desired behavior)
        if not query_text:
            print("No query text provided, performing filtered fetch.")
            try:
                print(f"Fetching objects with filters: {combined_filter} and limit: {n_results}")
                results = collection.query.fetch_objects(
                    filters=combined_filter,
                    limit=n_results
                )
                return results.objects
            except Exception as e:
                print(f"Error during fetch_objects: {e}")
                return []


        # --- Start Hybrid Search Logic ---
        try:
            # Generate vector for the vector search part
            vector = self.embedder.encode(query_text, convert_to_tensor=False).tolist() # Use convert_to_tensor=False if embedder expects list

            # Perform hybrid search
            results = collection.query.hybrid(
                query=query_text,       # For keyword (BM25) search
                vector=vector,          # For vector search
                limit=n_results,
                alpha=alpha,            # Balance between keyword and vector (0=keyword, 1=vector)
                filters=combined_filter # Apply metadata filters
            )
            return results.objects

        except Exception as e:
            print(f"Error during hybrid search: {e}")
            # Handle exceptions during embedding or search
            return []
        
class WeaviateIndexer4PlanSelection(WeaviateIndexer):
    def __init__(self, db_name="ResearchSection"):
        super().__init__(db_name)

    def ensure_schema(self):
        # ensure schema
        if not self.client.collections.exists(self.db_name):
            self.client.collections.create(
                name=self.db_name,
                properties=[
                    Property(name="plan_id", data_type=DataType.TEXT),
                    Property(name="description", data_type=DataType.TEXT),
                    Property(name="plan_name", data_type=DataType.TEXT)
                ],
                vectorizer_config=None  # Because we're using custom vectors
            )

    def add_predefined_plan_description_to_index(self, plan_name2description: dict, plan_name2plan: dict, plan_name2stepdesc: dict):
        """
        plan_name2description example:
        {
            "extract_experiment_settings": "extracts/summarizes experimental settings from academic papers, including datasets, metrics, baselines, configurations, and so on. *NOTE*: not include any experimental results. ",
            "extract_experiment_setups": "extract/summarizes **ONLY** the experimental environment and key parameters settings from academic papers"
        }
        plan_name2plan example:
        {
            "extract_experiment_settings": "plan_extract_experimental_settings",
            "extract_experiment_setups": "plan_extract_experimental_setup"
        }
        plan_name2stepdesc example:
        {
            "extract_experiment_settings": "1.Retrieves the Experiment section from each paper.2.Extracts experimental settings from academic papers, including datasets, metrics, baselines, configurations, and so on.",
            "extract_experiment_setups": "1.Retrieves the Experiment section from each paper.2.Extracts only the experimental environment and key parameters settings."
        }
        """
        self.ensure_schema()
        # get collection
        collection = self.client.collections.get(self.db_name)

        # insert plan into index
        for plan_id, plan_desc in plan_name2description.items():
            data = {
                "plan_id": plan_id,
                "plan_name": plan_name2plan[plan_id],
                "description": plan_desc,
                "step_description": plan_name2stepdesc[plan_id]
            }
            # embed the description
            vector = self.embedder.encode(plan_desc, convert_to_tensor=True).tolist()
            collection.data.insert(
                uuid=weaviate.util.generate_uuid5(plan_id),
                properties=data,
                vector=vector
            )

    def add_one_plan_description_to_index(self, plan_id: str, plan_description: str, plan_name: str, plan_stepdesc: str):
        self.ensure_schema()
        # get collection
        collection = self.client.collections.get(self.db_name)
        data = {
            "plan_id": plan_id,
            "plan_name": plan_name,
            "description": plan_description,
            "step_description": plan_stepdesc
        }
        # embed the description
        vector = self.embedder.encode(plan_description, convert_to_tensor=True).tolist()
        collection.data.insert(
            uuid=weaviate.util.generate_uuid5(plan_id),
            properties=data,
            vector=vector
        )

    def search_candidate_plan(self, query_text: str, n_results: int = 5):

        try:
            collection = self.client.collections.get(self.db_name)
        except Exception as e:
            print(f"Error getting collection '{self.db_name}': {e}")
            # Handle error appropriately, maybe return empty list or raise
            return []

        # --- Start Semantic Search Logic ---
        try:
            # Generate vector for the vector search part
            vector = self.embedder.encode(query_text, convert_to_tensor=False).tolist() # Use convert_to_tensor=False if embedder expects list

            # Perform hybrid search
            results = collection.query.near_vector(
                near_vector=vector,          # For vector search
                limit=n_results,
            )
            return results.objects

        except Exception as e:
            print(f"Error during hybrid search: {e}")
            # Handle exceptions during embedding or search
            return []