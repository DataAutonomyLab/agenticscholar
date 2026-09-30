import re
import json
import numpy as np
import nltk
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import os
from dataclasses import dataclass, field
from typing import List, Dict, Any

# --- Dataclasses ---
@dataclass
class Section:
    """Represents a structured section of the parsed document."""
    paper_id: str
    section_id: str
    section_title: str
    section_content: str = ""
    section_parent: str = ""
    section_tags: List[str] = field(default_factory=list)
    section_children: List[str] = field(default_factory=list)
    chunk_id: int = -1
    figure_table_references: List[str] = field(default_factory=list)
    vis_elements: List[Dict[str, Any]] = field(default_factory=list)
    embedding: List[float] = field(default_factory=list) # Added for embeddings
    summary: str = "" # Added for summaries

# --- Utility Functions ---

def make_json_serializable(data):
    """Recursively converts NumPy types and dataclass instances to native Python types for JSON serialization."""
    if isinstance(data, dict):
        return {key: make_json_serializable(value) for key, value in data.items()}
    if isinstance(data, (list, tuple)):
        return [make_json_serializable(item) for item in data]
    if isinstance(data, np.ndarray):
        return data.tolist()
    if isinstance(data, (np.number, np.bool_)):
        return data.item()
    if isinstance(data, Section):
        return {
            "paper_id": data.paper_id,
            "section_id": data.section_id,
            "section_title": data.section_title,
            "section_content": data.section_content,
            "section_parent": data.section_parent,
            "section_children": data.section_children,
            "chunk_id": data.chunk_id,
            "figure_table_references": data.figure_table_references,
            "vis_elements": data.vis_elements,
            "embedding": data.embedding,
            "summary": data.summary,
        }
    return data

# --- Chunking Implementations ---

def fixed_size_chunking(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    """Splits text into fixed-size chunks with a specified overlap."""
    if chunk_overlap >= chunk_size:
        raise ValueError("Overlap must be smaller than chunk size.")

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - chunk_overlap
    return [c for c in chunks if c.strip()]

def recursive_chunking(text: str, chunk_size: int, chunk_overlap: int, separators: list[str] = None) -> list[str]:
    """
    Recursively splits text by a list of separators to maintain semantic units.
    A simplified from-scratch implementation.
    """
    if separators is None:
        separators = ["\n\n", "\n", ". ", " ", ""]

    if not text:
        return []

    # Find the best separator that exists in the text
    separator = next((s for s in separators if s in text), separators[-1])

    # Base case: if the text is small enough or no good separator is found
    if len(text) <= chunk_size or not separator:
        if len(text) > chunk_size * 1.5: # Handle cases where a long text has no separators
             return fixed_size_chunking(text, chunk_size, chunk_overlap)
        return [text]

    # Split the text and recursively chunk the parts
    chunks = []
    splits = text.split(separator)
    current_chunk = ""
    for part in splits:
        if not part:
            continue
        # If adding the next part fits, do so
        if len(current_chunk) + len(part) + len(separator) <= chunk_size:
            current_chunk += part + separator
        else:
            # Otherwise, finalize the current chunk and start a new one
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
            current_chunk = part + separator
            
    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks

def semantic_chunking(text: str, model_name, similarity_threshold: float = 0.45) -> list[str]:
    """Splits text based on semantic similarity of sentences."""

    try:
        model = SentenceTransformer(model_name, device='mps') # Default to MPS
        print("Model loaded successfully.")
    except Exception as e:
        print(f"Error loading Sentence Transformer model: {e}")
        print("Please ensure 'sentence-transformers' and its dependencies are installed.")
        print("And that the model name is correct.")
        return []
    
    try:
        sentences = nltk.sent_tokenize(text.strip())
    except LookupError:
        print("NLTK 'punkt' tokenizer not found. Downloading...")
        nltk.download('punkt')
        sentences = nltk.sent_tokenize(text.strip())
        
    if not sentences:
        return []

    embeddings = model.encode(sentences, show_progress_bar=False)
    if len(embeddings) < 2:
        return [" ".join(sentences)]

    # Calculate similarity between adjacent sentences
    similarities = cosine_similarity(embeddings[:-1], embeddings[1:]).diagonal()
    
    chunks = []
    current_chunk_start = 0
    for i, sim in enumerate(similarities):
        if sim < similarity_threshold:
            chunks.append(" ".join(sentences[current_chunk_start : i + 1]))
            current_chunk_start = i + 1
    
    # Add the final chunk
    chunks.append(" ".join(sentences[current_chunk_start:]))
    
    return [c.strip() for c in chunks if c.strip()]

# --- Data Processing Pipeline ---

def create_chunks(data: List[Section], method: str, chunk_size: int, chunk_overlap: int, model=None, similarity_threshold=0.45) -> List[Section]:
    """Applies a specified chunking method to a list of data dictionaries."""
    chunked_data = []
    chunk_id_counter = 0
    
    for item in data:
        text = item.section_content
        if not text or len(text.strip()) < 5:
            continue
        
        if method == 'fixed':
            chunks = fixed_size_chunking(text, chunk_size, chunk_overlap)
        elif method == 'recursive':
            chunks = recursive_chunking(text, chunk_size, chunk_overlap)
        elif method == 'semantic':
            if model is None:
                raise ValueError("A model must be provided for semantic chunking.")
            chunks = semantic_chunking(text, model, similarity_threshold)
        else:
            raise ValueError(f"Unknown chunking method: {method}")
        
        for chunk_text in chunks:
            new_chunk = Section(
                paper_id=item.paper_id,
                section_id=item.section_id,
                section_title=item.section_title,
                section_content=chunk_text,
                section_parent=item.section_parent,
                section_children=item.section_children,
                chunk_id=chunk_id_counter,
                figure_table_references=item.figure_table_references,
                vis_elements=item.vis_elements,
                embedding=item.embedding, # Preserve existing embedding if any
                summary=item.summary, # Preserve existing summary if any
                section_tags=item.section_tags
            )
            chunked_data.append(new_chunk)
            chunk_id_counter += 1
            
    return chunked_data

def extract_figure_table_references(text: str) -> list[str]:
    """Extracts unique figure and table references from text."""
    pattern = r'\b(Figure|Fig\.?|Table|Tab\.?)\s+([0-9]+[a-zA-Z]?)'
    matches = re.finditer(pattern, text, re.IGNORECASE)
    # Use a set to store unique references, preserving original capitalization from the first find
    references = {match.group(0) for match in matches}
    return sorted(list(references))

def add_references_to_data(data: List[Section]) -> List[Section]:
    """Adds a list of figure/table references to each item in the data."""
    for item in data:
        item.figure_table_references = extract_figure_table_references(item.section_content)
    return data

# --- Embedding and Search ---

def create_embeddings(data: List[Section], model) -> tuple[List[Section], np.ndarray]:
    """Generates embeddings for the content of each data item."""
    # Filter out items with no content to avoid errors
    valid_data = [item for item in data if item.section_content.strip()]
    contents = [item.section_content for item in valid_data]
    
    if not contents:
        return [], np.array([])

    embeddings = model.encode(contents, show_progress_bar=True)
    
    # Add embeddings back to the original items
    for item, embedding in zip(valid_data, embeddings):
        item.embedding = embedding.tolist() # Store as list for JSON
        
    return valid_data, np.array(embeddings)

def search(query_embedding: np.ndarray, index_embeddings: np.ndarray, k: int = 5, threshold: float = None) -> list[tuple[int, float]]:
    """Performs similarity search and returns indices and scores."""
    if query_embedding.ndim == 1:
        query_embedding = query_embedding.reshape(1, -1)

    similarities = cosine_similarity(query_embedding, index_embeddings).flatten()
    
    if threshold is not None:
        indices = np.where(similarities > threshold)[0]
    else:
        # Get top-k, ensuring we don't request more than available
        count = min(k, len(similarities))
        indices = np.argsort(similarities)[-count:][::-1]

    return [(int(i), float(similarities[i])) for i in indices]

# --- Generative AI Functions ---

def generate_summaries(data: List[Section], client) -> List[Section]:
    """Generates a summary for the content of each data item."""
    prompt_template = "Summarize the following text concisely:\n\n#text#\n\nSummary:"
    for i, item in enumerate(data):
        print(f"Generating summary for chunk {i+1}/{len(data)}...")
        try:
            response = client.generate_content(prompt_template.replace('#text#', item.section_content))
            item.summary = response.text
        except Exception as e:
            print(f"Error generating summary for chunk {i+1}: {e}")
            item.summary = "Error during summary generation."
    return data