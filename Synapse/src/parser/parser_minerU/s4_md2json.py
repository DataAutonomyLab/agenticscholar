import re
import json
import argparse
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Dict, Any

# Assuming these are custom modules you have
from src.parser.parser_minerU.util_chunking import create_chunks
from src.parser.parser_minerU.util_chunking import Section
from src.parser.parser_minerU.util_chunking import add_references_to_data
from src.synapse_utils import get_data_path

# --- Configuration ---

CONFIG = {
    # "parsed_papers_dir": Path("data/parsed_papers"),
    # "json_dir": Path("data/json"),
    "chunking_model": "BAAI/bge-base-en-v1.5",
    "chunk_size": 250,
    "chunk_overlap": 50,
    "similarity_threshold": 0.45,
    "chunking_method": 'semantic',
}

# Use the more robust regex with a negative lookahead.
# This correctly captures "# 1 Title" but ignores "# 1. Title" or "# 1.1 Title"
# to avoid ambiguity with list items or sub-subsections.
SECTION_REGEX_SIMPLE = re.compile(r"^(#{1,6})\s+(\d+)\s+(?![\.\d])(.*)$")

# This regex correctly handles hierarchical sections like "1.1" and "1.1.2".
SECTION_REGEX_HIERARCHICAL = re.compile(r"^(#{1,6})\s+(\d+(\.\d+)*)\s+(.*)$")

def _init_section(paper_id: str, section_id: str, line: str) -> Section:
    """Initializes a new Section object."""
    return Section(
        paper_id=paper_id,
        section_id=section_id.strip(),
        section_title=line.strip(),
    )

def parse_markdown_sections(paper_id: str, md_path: str, hierarchical: bool) -> List[Section]:
    """
    Parses a Markdown file into a list of Section objects.

    Args:
        paper_id: The unique identifier for the paper.
        md_path: The path to the markdown file.
        hierarchical: If True, uses regex that supports nested sections (e.g., "1.1").

    Returns:
        A list of Section objects.
    """
    regex = SECTION_REGEX_HIERARCHICAL if hierarchical else SECTION_REGEX_SIMPLE
    sections: List[Section] = []
    current_section: Section | None = None

    with md_path.open("r", encoding="utf-8") as f:
        for line in f:
            match = regex.match(line.strip())
            if match:
                if current_section:
                    sections.append(current_section)
                
                groups = match.groups()
                section_id = groups[1]
                current_section = _init_section(paper_id, section_id, line)
            elif current_section:
                current_section.section_content += line
    
    if current_section:
        sections.append(current_section)
        
    return sections

def build_hierarchy(sections: List[Section]) -> List[Section]:
    """
    Builds parent-child relationships between sections.

    Args:
        sections: A list of Section objects.

    Returns:
        The list of sections with parent/child links populated.
    """
    id_to_section = {s.section_id: s for s in sections}
    children_map = defaultdict(list)

    for sec in sections:
        if "." in sec.section_id:
            parent_id = ".".join(sec.section_id.split(".")[:-1])
            if parent_id in id_to_section:
                sec.section_parent = parent_id
                children_map[parent_id].append(sec.section_id)

    for sec in sections:
        sec.section_children = children_map.get(sec.section_id, [])
        
    return sections

def _link_visualizations(sections: List[Section], vis_data: Dict[str, Any]) -> List[Section]:
    """Links extracted figure/table references to their data."""
    key_map = {'Fig.': 'Figure', 'Tab.': 'Table', 'Fig': 'Figure', 'Tab': 'Table'}
    
    for sec in sections:
        added_ids = set()
        for ref_id in sec.figure_table_references:
            # Try direct match first
            if ref_id in vis_data and ref_id not in added_ids:
                sec.vis_elements.append(vis_data[ref_id])
                added_ids.add(ref_id)
                continue
            
            # Try normalizing the key (e.g., "Fig." -> "Figure")
            parts = ref_id.split(" ", 1)
            if len(parts) == 2:
                prefix, number = parts
                new_key = f"{key_map.get(prefix, prefix)} {number}"
                if new_key in vis_data and new_key not in added_ids:
                    sec.vis_elements.append(vis_data[new_key])
                    added_ids.add(new_key)
                    
    return sections


def convert_markdown_to_json(
    user_id: str,
    kb_name: str,
    paper_name: str,
    hierarchical: bool = False,
    chunking: bool = False,
    link_visuals: bool = False
):
    """
    Main pipeline to convert a markdown file to a structured JSON file.
    
    Args:
        paper_name: The identifier for the paper (e.g., "face").
        md_suffix: The suffix for the markdown file (e.g., "mai").
        output_filename: The name of the output JSON file.
        hierarchical: Whether to parse nested section IDs (e.g., 1.1, 1.1.2).
        chunking: Whether to perform semantic chunking on the content.
        link_visuals: Whether to link figure/table references.
    """
    # md_path = Path(f"{get_data_path()}/{user_id}/{kb_name}/minerU/{paper_name}/{paper_name}_v2.md")
    md_path = get_data_path() + '/' + user_id + '/' + kb_name + '/minerU/' + paper_name + '/' + paper_name + '_v2.md'
    # json_path = Path(f"{get_data_path()}/{user_id}/{kb_name}/minerU/{paper_name}/{paper_name}_structured.json")
    json_path = get_data_path() + '/' + user_id + '/' + kb_name + '/minerU/' + paper_name + '/' + paper_name + '_structured.json'
    
    print(f"Parsing sections from {md_path}...")
    sections = parse_markdown_sections(paper_name, md_path, hierarchical)
    
    if hierarchical:
        print("Building hierarchy...")
        sections = build_hierarchy(sections)

    if chunking:
        print("Creating chunks...")
        sections = create_chunks(
            data=sections, # Assuming create_chunks is adapted for List[Section]
            model=CONFIG["chunking_model"],
            chunk_size=CONFIG["chunk_size"],
            chunk_overlap=CONFIG["chunk_overlap"],
            similarity_threshold=CONFIG["similarity_threshold"],
            method=CONFIG["chunking_method"]
        )
    
    if link_visuals:
        print("Extracting and linking visual references...")
        sections = add_references_to_data(sections)
        
        # vis_json_path = Path(f"{get_data_path()}/{user_id}/{kb_name}/minerU/{paper_name}/{paper_name}_vis.json")
        vis_json_path = get_data_path() + '/' + user_id + '/' + kb_name + '/minerU/' + paper_name + '/' + paper_name + '_vis.json'
        if vis_json_path.exists():
            with vis_json_path.open("r", encoding="utf-8") as f:
                vis_data = json.load(f)
            sections = _link_visualizations(sections, vis_data)
        else:
            print(f"Warning: Visualization file not found at {vis_json_path}")

    # Convert list of dataclass objects to list of dicts for JSON serialization
    output_data = [asdict(s) for s in sections]
    
    print(f"Saving structured data to {json_path}...")
    # CONFIG["json_dir"].mkdir(exist_ok=True)
    with json_path.open("w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
        
    print("Processing complete.")