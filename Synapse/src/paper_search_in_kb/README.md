# Paper Search

## Packages

1. python==3.10.18
2. faiss==1.9.0
3. langchain-openai==0.3.23
4. PyMuPDF==1.26.0
5. sentence-transformers==4.1.0
6. transformers==4.52.4
7. numpy==1.24.0
8. scipy==1.15.3
9. rank_bm25==0.2.2
10. nltk==3.9.1

## Project Structure

The project is organized as follows:

```text
Synapse/
├── src/
│   └── paper_search_in_kb/
│       ├── s1_paper_store.py     # [Step 1] Summarize and index descriptors from paper
│       ├── s2_paper_search.py    # [Step 2] Search for relevant papers based on a query
│       ├── s3_evaluate.py        # Batch evaluation
│       └── test_data.json        # Input for batch evaluation (list of queries + ground truth)
│
└── data/
    └── <user_id>/
        └── <kb_id>/
            ├── pdf/                           # PDF papers
            │   ├── <paper_id>.pdf
            │   └── ...
            └── paper_search/
                ├── extracted_descriptors/     # LLM summarized descriptors for each paper
                │   ├── <paper_id>.json  
                │   └── ...
                ├── faiss_indexes/             # FAISS indexes for each descriptor
                │   ├── <descriptor>.index  
                │   └── ...
                └── faiss_indexes_metadata/    # Metadata for each descriptor
                    ├── <descriptor>.json
                    └── ...
```

## Before Running

- Populate the PDFs in `data/<user_id>/<kb_id>/pdf/`.
- Update the LLM API key, LLM model and embedding model in `s1_paper_store.py` and `s2_paper_search.py`.
- [For batch evaluation] Update **user_id** and **kb_id** in `s3_evaluate.py`.
