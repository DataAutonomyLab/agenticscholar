import json
import textwrap
from pathlib import Path
import faiss
import fitz  # PyMuPDF
import numpy as np
from tqdm import tqdm
from langchain.schema import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from sentence_transformers import SentenceTransformer

from src.synapse_utils import get_data_path
# from local_utils import get_data_path


# Configuration
from src.config.config import get_llm_config_for_module

local_config = get_llm_config_for_module("SearchInKB")

EMBEDDING_MODEL = "BAAI/bge-base-en-v1.5"
EMBEDDING_DIM = 768


def extract_text_from_pdf(pdf_path):
    try:
        doc = fitz.open(str(pdf_path))
    except Exception as e:
        print(f"[ERROR] Failed to open PDF: {pdf_path} ({e})")
        return ""
    
    pages_text = [
        page.get_text("text").strip()
        for page in doc
        if page.get_text("text").strip()
    ]
    doc.close()

    return "\n".join(pages_text)


def extract_descriptors_n_summaries(text):
    """ Extract descriptors and summaries from paper """
    
    # Initialize LLM
    llm = ChatOpenAI(
        model=local_config["default_model"],
        openai_api_base=local_config["base_url"],
        openai_api_key=local_config["api_key"],
        temperature=0.2
    )

    prompt = textwrap.dedent("""You are an expert at extracting structured information from academic research paper.

    Your task is to analyze the provided paper content and extract key information into a structured JSON format.

    ---
    
    Output Format: 
                             
    Return a single, well-formatted JSON object with exactly two top-level keys:
    - "metadata": bibliographic and publication details.
    - "aspects": core conceptual and technical insights from the paper.
    
    Each field must be one of the following:
    - A string (for singular fields), or
    - A list of strings (for plural fields like authors, keywords, datasets, etc.).
    
    ---
                             
    Output Schema:
    {
        "metadata": {
            "title",
            "authors",
            "affiliations",
            "keywords",
            "publication_year",
            "venue"
        },
        "aspects": {
            "field_or_topic",
            "research_problem",
            "proposed_method",
            "experimental_datasets",
            "experimental_results"
        }
    }
    Note: Fields are grouped under their respective top-level keys. This schema defines the required structure, it does not include placeholder values.
    
    ---
    
    Output Requirements:
    - The JSON must contain exactly two top-level keys: "metadata" and "aspects".
    - Do not introduce any additional structure or nesting beyond what is defined in the schema.
    - Leave any field as an empty string ("") if the information is not found in the provided content.
    - Do not include explanations, summaries, or commentary.
    - Do not wrap the output in markdown, code blocks, or any additional formatting.
    - Preserve as much technical and factual detail as possible from the source content.
                             
    Begin processing the input content now.
    """).strip()

    response = llm([
        SystemMessage(content=prompt),
        HumanMessage(content=text)
    ])

    try:
        descriptors = json.loads(response.content)
        descriptors.setdefault("metadata", {})
        descriptors.setdefault("aspects", {})
        return descriptors
    except json.JSONDecodeError:
        print(f"[ERROR] LLM returned invalid JSON:\n{response.content}")
        return None


def generate_embeddings(paper_descriptors):
    """ Generate embeddings for all descriptors """

    model = SentenceTransformer(EMBEDDING_MODEL)
    embeddings = {}
    embedding_metadata = {}
    paper_id = paper_descriptors["id"]

    # Process both metadata and aspects
    for descriptor_type in ["metadata", "aspects"]:
        descriptor_data = paper_descriptors.get(descriptor_type, {})
        
        for descriptor_name, value in descriptor_data.items():
            if not value:
                continue
            
            # Convert to text
            if isinstance(value, list):
                text = ", ".join(str(v) for v in value if v)
            else:
                text = str(value)
            
            if not text:
                print(f"Empty value for {descriptor_type} -> {descriptor_name}")
                continue

            try:
                # Generate embedding
                embedding = model.encode(text, normalize_embeddings=True)
                embeddings[descriptor_name] = embedding
            
                # Store embedding metadata (different from paper metadata)
                embedding_metadata[descriptor_name] = {
                    "paper_id": paper_id,
                    "descriptor_type": descriptor_type,
                    "descriptor_name": descriptor_name,
                    "value": text
                }
            except Exception as e:
                print(f"[ERROR] Failed to embed {descriptor_type} -> {descriptor_name} ({e})")

    return embeddings, embedding_metadata

    
def update_faiss_indexes(user_id, kb_id, paper_id, embeddings, embedding_metadata):
    """ Update all FAISS indexes with new embeddings """

    base_path = Path(get_data_path()) / user_id / kb_id / "paper_search"
    index_dir = base_path / "faiss_indexes"
    metadata_dir = base_path / "faiss_indexes_metadata"

    index_dir.mkdir(parents=True, exist_ok=True)
    metadata_dir.mkdir(parents=True, exist_ok=True)

    for descriptor_name, embedding in tqdm(embeddings.items(), desc="Updating FAISS indexes"):
        index_file = index_dir / f"{descriptor_name}.index"
        embedding_metadata_file = metadata_dir / f"{descriptor_name}_metadata.json"

        # Load or create new index
        if index_file.exists():
            index = faiss.read_index(str(index_file))
        else:
            index = faiss.IndexFlatIP(EMBEDDING_DIM)

        # Load existing metadata
        if embedding_metadata_file.exists():
            with open(embedding_metadata_file, "r") as f:
                existing_embedding_metadata = json.load(f)
        else:
            existing_embedding_metadata = []

        # Remove existing entry for this paper & keep only other papers' entries
        keep_embedding_metadata = []
        keep_ids = []
        for i, embed_meta in enumerate(existing_embedding_metadata):
            if embed_meta["paper_id"] != paper_id:
                keep_embedding_metadata.append(embed_meta)
                keep_ids.append(i)

        # Rebuild index if needed
        if keep_ids and len(keep_ids) < len(existing_embedding_metadata):
            # Rebuild with kept vectors only
            kept_vectors = [index.reconstruct(i) for i in keep_ids]
            index = faiss.IndexFlatIP(EMBEDDING_DIM)
            if kept_vectors:
                vectors_array = np.array(kept_vectors).astype("float32")
                faiss.normalize_L2(vectors_array)
                index.add(vectors_array)
        elif not keep_ids:
            index = faiss.IndexFlatIP(EMBEDDING_DIM)

        # Add new embedding and its metadata
        vector = np.array([embedding]).astype("float32")
        faiss.normalize_L2(vector)
        index.add(vector)
        keep_embedding_metadata.append(embedding_metadata[descriptor_name])

        # Save updated index and embedding metadata
        faiss.write_index(index, str(index_file))
        with open(embedding_metadata_file, "w") as f:
            json.dump(keep_embedding_metadata, f, indent=2)

        print(f"[INFO] Updated index for '{descriptor_name}' (Paper ID: {paper_id})")


# Main Entry Function
def store_paper_entry(user_id, kb_id, paper_name):
    base_path = Path(get_data_path()) / user_id / kb_id
    pdf_path = base_path / "pdf" / f"{paper_name}.pdf"
    output_path = base_path / "paper_search" / "extracted_descriptors" / f"{paper_name}.json"

    if not pdf_path.exists():
        print(f"[ERROR] PDF not found: {pdf_path}")
        return

    text = extract_text_from_pdf(pdf_path)
    if not text.strip():
        print(f"[ERROR] No text found in PDF: {pdf_path}")
        return
    print("[INFO] Text extracted from pdf")

    paper_descriptors = extract_descriptors_n_summaries(text)
    if not paper_descriptors:
        print(f"[ERROR] Failed to extract descriptors for: {pdf_path}")
        return
    paper_descriptors['id'] = str(paper_name)
    print("[INFO] Descriptors and summaries extracted from pdf text")

    # Save extracted descriptors and summaries
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(paper_descriptors, f, indent=2)
    print(f"[INFO] Saved descriptors and summaries to {output_path}")
    
    # Generate embeddings and update indexes and embedding metadata
    embeddings, embedding_metadata = generate_embeddings(paper_descriptors)
    update_faiss_indexes(user_id, kb_id, str(paper_name), embeddings, embedding_metadata)
    print(f"[INFO] Storing complete for: {paper_name}")
