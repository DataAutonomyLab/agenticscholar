from src.parser.parser_minerU.minerU_entry import minerU_entry # Import the MinerU entry function
from src.parser.parser_ms.ms_entry import ms_entry # Import the MS entry function
from src.paper_search_in_kb import s1_paper_store
from src.index.weaviate_instance import WeaviateIndexer

from src.synapse_utils import *

import json
from pathlib import Path

def load_entry(user_id: str, kb_name: str, paper_name: str, where: str="ms") -> None:
    """
    Entry point for loading a paper into the knowledge base using the MinerU parser.

    Args:
        user_id: The unique identifier for the user.
        kb_name: The name of the knowledge base.
        paper_name: The name of the paper to be processed.
    """
    # Process the paper using the MinerU parser
    if where == "minerU":
        minerU_entry(user_id, kb_name, paper_name)
    else:
        ms_entry(user_id, kb_name, paper_name)

    # Initialize Weaviate indexer
    # return
    user_id_2 = user_id.split('-')[0].lower()
    kb_name_2 = kb_name.split('-')[0].lower()
    db_name = f"SYNAPSE{user_id_2}{kb_name_2}_{where}"
    print('db_name:', db_name)  
    indexer = WeaviateIndexer(db_name=db_name)

    # Load sections into Weaviate index
    json_path = (
        get_data_path() /
        user_id /
        kb_name /
        where /
        paper_name /
        f"{paper_name}_structured.json"
    )
    with open(json_path, "r", encoding="utf-8") as f:
        sections = json.load(f)
    print(f"Loaded {len(sections)} sections from {json_path}")
    indexer.add_section_to_index(sections)
    
    # make the new paper be searchable
    # s1_paper_store.store_paper_entry(user_id, kb_name, paper_name)


# load_entry("91f2dbae-6e6f-47c0-ae90-ea68f436c874", "69d2de8f-5176-4697-afee-c7770ab594d5", "flat")