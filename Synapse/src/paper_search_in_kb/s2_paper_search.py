import json
import textwrap
from pathlib import Path
from datetime import datetime

import faiss
import numpy as np
from langchain.schema import HumanMessage
from langchain_openai import ChatOpenAI
from sentence_transformers import SentenceTransformer
import re
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import nltk
from rank_bm25 import BM25Okapi

from src.synapse_utils import get_data_path
# from local_utils import get_data_path


# Configuration
from src.config.config import get_llm_config_for_module

local_config = get_llm_config_for_module("SearchInKB")


EMBEDDING_MODEL = "BAAI/bge-base-en-v1.5"
EMBEDDING_DIM = 768

# download (only once)
nltk.download('punkt')
nltk.download('punkt_tab')
nltk.download('stopwords')
STOPWORDS = set(stopwords.words('english'))


def extract_descriptors_n_years(llm, query):
    """ Extract required descriptors (including publication year) from user query to find relevant papers later """

    current_year = datetime.now().year

    prompt = textwrap.dedent(f"""You are an expert for research paper discovery.

    Your task is to analyze the following user query and identify only the most relevant paper descriptors (metadata or aspects) that should be used to retrieve the best matching papers.

    ---

    Output Format:

    Return a single, well-formatted JSON object with the following two keys:
    1. "descriptors": 
        - A list of descriptor names from the list below that should be used to match this query. 
        - Select all descriptors that are directly or semantically relevant to the user's query intent and avoid unrelated or overly generic fields. 
        - If metadata descriptors are mentioned or clearly implied, they must be selected with strict accuracy, as they are precise filtering criteria.
    2. "publication_years": 
        - Assume current year is {current_year}.
        - A list of years explicitly or implicitly mentioned in the query.
        - If a specific year is mentioned, include it as a single value in the list. 
        - If the query refers to a range (e.g., "past five years", "since 2019"), translate that into a list of integer years. 
        - You must always return a non-empty list of years if any temporal reference is present even if vague (e.g., "recent", "early", "past", etc.). 
        - If no year is mentioned or implied, return an empty list.
    
    ---

    Available descriptors:

    metadata:
    - title
    - authors
    - affiliations
    - keywords
    - publication_year
    - venue

    aspects:
    - field_or_topic
    - research_problem
    - proposed_method
    - experimental_datasets
    - experimental_results

    ---

    Output Requirements:
    - The JSON must contain exactly two keys: "descriptors" and "publication_years".
    - Do not include explanations, summaries, or commentary.
    - Do not wrap the output in markdown, code blocks, or any additional formatting.

    ---
    
    User query: "{query}"
    """).strip()

    response = llm([HumanMessage(content=prompt)])
    
    try:
        result = json.loads(response.content)
        query_descriptors = result.get("descriptors", [])
        query_years = result.get("publication_years", [])
        # account for cases where year(s) are implicitly mentioned
        if query_years and "publication_year" not in query_descriptors:
            query_descriptors.append("publication_year")
        return query_descriptors, query_years
    except json.JSONDecodeError:
        print(f"[ERROR] LLM returned invalid JSON:\n{response.content}")
        return [], []


def normalize_scores(scores):
    if scores is None or len(scores) == 0:
        return scores

    scores = np.array(scores, dtype=float)
    min_s, max_s = scores.min(), scores.max()

    if max_s == min_s:
        return [1.0 if s > 0 else 0.0 for s in scores]

    norm = (scores - min_s) / (max_s - min_s)
    return norm.tolist()


def preprocess_text(text, remove_stopwords=True):
    """
    Preprocess a single string for BM25:
    - Lowercase
    - Remove punctuation
    - Tokenize
    - (Optional) Remove stopwords
    """
    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)  # remove punctuation
    tokens = word_tokenize(text)

    if remove_stopwords:
        tokens = [token for token in tokens if token not in STOPWORDS]

    return tokens


def refine_results(llm, query, candidates, user_id, kb_id, query_descriptors):
    # Step 1: Load descriptor and its summarized content for candidates
    paper_descriptors = {pid: {} for pid in [c["paper_id"] for c in candidates]}

    for descriptor_name in query_descriptors:
        metadata_file = Path(get_data_path()) / user_id / kb_id / "paper_search" / "faiss_indexes_metadata" / f"{descriptor_name}_metadata.json"

        if not metadata_file.exists():
            continue

        try:
            with open(metadata_file, "r") as f:
                embedding_metadata = json.load(f)
        except Exception as e:
            print(f"[ERROR] Failed to load metadata file for '{descriptor_name}' ({e})")
            continue

        for meta in embedding_metadata:
            pid = meta["paper_id"]
            if pid not in paper_descriptors:
                continue

            value = meta.get("value", "")
            if isinstance(value, list):
                value = " ".join(map(str, value))
            elif not isinstance(value, str):
                value = str(value)

            paper_descriptors[pid][descriptor_name] = value

    # Step 2: Build candidate text for prompt
    candidate_entries = []
    for c in candidates:
        pid = c["paper_id"]
        descs = paper_descriptors[pid]
        desc_lines = [f"{d}: {v}" for d, v in descs.items() if v]
        summary = "\n".join(desc_lines) if desc_lines else "No descriptors available."
        candidate_entries.append(f"Paper ID: {pid}\n{summary}")
    candidate_block = "\n\n".join(candidate_entries)

    # Step 3: Build prompt
    prompt = textwrap.dedent(f"""You are an expert in academic literature search.
                             
    The user query is: "{query}"

    The user is interested in papers based on these descriptors: {", ".join(query_descriptors)}
    
    Below are the candidate papers, each with its descriptors:

    {candidate_block}

    ---

    Your task:
    1. Remove papers that are not relevant to the query. Only keep papers that are clearly relevant to the query. The goal is to maximize both precision and recall, so include all truly relevant papers and exclude any that are not relevant.
    2. Rank the remaining relevant papers by relevance (most relevant first).
    3. Output strictly in JSON list format:
    [
      {{"paper_id": <str>, "rank": <int>, "reason": "<short reason>"}},
      ...
    ]

    Output Requirements:
    - Do not include any text outside the JSON.
    - Do not include explanations, summaries, or commentary.
    - Do not wrap the output in markdown, code blocks, or any additional formatting.
    """).strip()
    # 3. For each included paper, provide a short justification ("reason").

    response = llm([HumanMessage(content=prompt)])

    try:
        result = json.loads(response.content)
        for i, r in enumerate(result, start=1):
            r["rank"] = i
        return result
    except json.JSONDecodeError:
        print(f"[ERROR] LLM returned invalid JSON:\n{response.content}")
        return []


def search_papers(user_id, kb_id, llm, query, top_k, query_descriptors, query_years):
    """ Search FAISS indexes for relevant papers """

    base_path = Path(get_data_path()) / user_id / kb_id / "paper_search"
    model = SentenceTransformer(EMBEDDING_MODEL)
    
    try:
        query_embedding = model.encode(query, normalize_embeddings=True)
        query_embedding = np.expand_dims(query_embedding, axis=0)  # (1, dim)
    except Exception as e:
        print(f"[ERROR] Failed to embed query ({e})")
        return []
    

    # --- Step 1: Year filter (exact) ---
    valid_year_paper_ids = set()
    if query_years:
        year_metadata_path = base_path / "faiss_indexes_metadata" / "publication_year_metadata.json"
        try:
            with open(year_metadata_path, "r") as f:
                year_metadata = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            print(f"[ERROR] Failed to load year metadata file from: {year_metadata_path}")
            return []

        for meta in year_metadata:
            year = int(meta["value"])
            if year in query_years:
                valid_year_paper_ids.add(meta["paper_id"])

        if not valid_year_paper_ids:
            print("[INFO] No papers match the given publication years.")
            return []
    
    # print("[DEBUG: query_descriptors]", query_descriptors)
    # print("[DEBUG: query_years]", query_years)
    # print("[DEBUG: valid_year_paper_ids]", valid_year_paper_ids)

    
    # --- Step 2: Metadata filter (BM25) ---
    metadata_descriptors = ["title", "authors", "affiliations", "keywords", "venue"]
    bm25_candidates = set()
    results_by_paper = {}  # paper_id: {descriptor_name: {"raw": score, "weighted": score}}

    for descriptor_name in query_descriptors:
        # keep only the metadata descriptors excluding year
        if descriptor_name not in metadata_descriptors:
            continue
        
        metadata_file = base_path / "faiss_indexes_metadata" / f"{descriptor_name}_metadata.json"
        if not metadata_file.exists():
            continue
        
        try:
            with open(metadata_file, "r") as f:
                embedding_metadata = json.load(f)
        except Exception as e:
            print(f"[ERROR] Failed to load metadata file for '{descriptor_name}' ({e})")
            continue
        
        # Only consider papers passing year filter
        if valid_year_paper_ids:
            embedding_metadata = [meta for meta in embedding_metadata if meta["paper_id"] in valid_year_paper_ids]
        # raw text (TODO: can pre-build to reduce computations)
        corpus = []
        for meta in embedding_metadata:
            value = meta.get("value", "")
            if isinstance(value, list):
                value = " ".join(map(str, value))  # flatten list to a single string
            elif not isinstance(value, str):
                value = str(value)
            corpus.append(value)
        
        # pre-process descriptors
        tokenized_corpus = [preprocess_text(doc) for doc in corpus]
        bm25 = BM25Okapi(tokenized_corpus)

        query_tokens = preprocess_text(query)
        raw_scores = bm25.get_scores(query_tokens)
        # print("[DEBUG: tokenized_corpus]", tokenized_corpus)
        # print("[DEBUG: query.split()]", query.split())
        # print("[DEBUG: raw_scores]", raw_scores)
        norm_scores = normalize_scores(raw_scores)

        # Retrieve top-N BM25 candidates
        top_n = min(len(raw_scores), top_k*2)
        top_indices = np.argsort(norm_scores)[::-1][:top_n]
        for idx in top_indices:
            pid = embedding_metadata[idx]["paper_id"]
            raw_score = float(raw_scores[idx])
            norm_score = float(norm_scores[idx])
            bm25_candidates.add(pid)
            if pid not in results_by_paper:
                results_by_paper[pid] = {}
            results_by_paper[pid][descriptor_name] = {
                "raw": raw_score,
                "norm": norm_score
            }
    
    valid_paper_ids = bm25_candidates if bm25_candidates else valid_year_paper_ids
    # print("[DEBUG: results_by_paper 1]", results_by_paper)
    # print("[DEBUG: valid_paper_ids]", sorted(list(valid_paper_ids)) )
    
    
    # --- Step 3: Aspect filter (FAISS cosine similarity) ---
    aspect_descriptors = ["field_or_topic", "research_problem", "proposed_method", "experimental_datasets", "experimental_results"]
    for descriptor_name in query_descriptors:
        # keep only the aspect descriptors
        if descriptor_name not in aspect_descriptors:
            continue

        metadata_file = base_path / "faiss_indexes_metadata" / f"{descriptor_name}_metadata.json"
        index_file = base_path / "faiss_indexes" / f"{descriptor_name}.index"
        if not (metadata_file.exists() and index_file.exists()):
            continue

        try:
            with open(metadata_file, "r") as f:
                embedding_metadata = json.load(f)
            index = faiss.read_index(str(index_file))
        except Exception as e:
            print(f"[ERROR] Failed to load index file for '{descriptor_name}' ({e})")
            continue

        # Top-k + threshold-based search
        sim_threshold = 0.0
        cos_sims, indices = index.search(query_embedding, min(len(embedding_metadata), top_k*2))
        norm_scores = normalize_scores(cos_sims[0].tolist())
        for idx, raw_score, norm_score in zip(indices[0], cos_sims[0], norm_scores):
            if idx < 0 or idx >= len(embedding_metadata):
                continue
            
            # apply similarity threshold
            if raw_score <= sim_threshold:
                continue

            pid = embedding_metadata[idx]["paper_id"]
            
            # Filter valid papers (year and metadata if applicable)
            if valid_paper_ids and pid not in valid_paper_ids:
                continue
            if pid not in results_by_paper:
                results_by_paper[pid] = {}
            
            results_by_paper[pid][descriptor_name] = {
                "raw": float(raw_score),
                "norm": float(norm_score)
            }
            
    # TODO: handle the case where there is only one year descriptor
    # print("[DEBUG: results_by_paper 2]", results_by_paper)

    
    # --- Step 4: Aggregate total score per paper and sort ---
    meta_weight = 0.5
    aspect_weight = 0.5
    candidates = []
    for pid, descriptor_scores in results_by_paper.items():
        meta_scores = [ds["norm"] for desc, ds in descriptor_scores.items() if desc in metadata_descriptors]
        aspect_scores = [ds["norm"] for desc, ds in descriptor_scores.items() if desc in aspect_descriptors]

        avg_meta = sum(meta_scores) / len(meta_scores) if meta_scores else 0.0
        avg_aspect = sum(aspect_scores) / len(aspect_scores) if aspect_scores else 0.0

        total_weighted_score = (meta_weight * avg_meta) + (aspect_weight * avg_aspect)

        candidates.append({
            "paper_id": pid,
            "total_score": total_weighted_score,
            "descriptor_scores": descriptor_scores
        })
    candidates.sort(key=lambda x: -x["total_score"])

    
    # --- Step 5: Refine results with LLM ---
    max_k = min(len(results_by_paper), top_k)
    final_results = refine_results(llm, query, candidates[:max_k], user_id, kb_id, query_descriptors)


    # --- Step 6: Add similarity search into to LLM refinement results ---
    candidate_lookup = {c["paper_id"]: c for c in candidates}
    merged_results = []
    for r in final_results:
        pid = r["paper_id"]
        if pid in candidate_lookup:
            merged_results.append({
                "paper_id": pid,
                "rank": r["rank"],
                "reason": r["reason"],
                "total_score": candidate_lookup[pid]["total_score"],
                "descriptor_scores": candidate_lookup[pid]["descriptor_scores"]
            })
    return merged_results


# Main Entry Point
def search_papers_entry(user_id, kb_id, query, top_k=10):
    """ Entry point: Analyse user query and search for the most relevant papers """
    
    # Initialize LLM
    llm = ChatOpenAI(
        model=local_config["default_model"],
        openai_api_base=local_config["base_url"],
        openai_api_key=local_config["api_key"],
        temperature=0.2
    )
    
    query_descriptors, query_years = extract_descriptors_n_years(llm, query)
    if not query_descriptors and not query_years:
        return [], []

    merged_results = search_papers(user_id, kb_id, llm, query, top_k, query_descriptors, query_years)
    print("\n[INFO] Search Results:")
    for r in merged_results:
        print(f"[{r['rank']}] Paper ID: {r['paper_id']} | Total Weighted Score: {r['total_score']:.4f} | LLM Reason: {r['reason']}")
        print("     Descriptor Scores:")
        for desc, scores in r["descriptor_scores"].items():
            raw = scores["raw"]
            norm = scores["norm"]
            print(f"         {desc}: raw={raw:.4f}, norm={norm:.4f}")

    paper_ids = [r['paper_id'] for r in merged_results]
    return paper_ids, merged_results


# print(search_papers_entry('a4852dad-9eac-4df6-8cac-d68f20827ee4', 'e9a95b84-9f4b-47f1-b016-7b2adfcf77b9', 'Which paper builds upon deepdb?'))
