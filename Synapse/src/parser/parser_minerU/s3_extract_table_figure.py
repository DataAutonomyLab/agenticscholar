import json
import argparse
from pathlib import Path
from typing import List, Dict, Any

from src.parser.parser_minerU.util_extract_figure import extract_figure_blocks
from src.parser.parser_minerU.util_extract_table import extract_all_table_blocks
from src.parser.parser_minerU.util_remove_figure_block import remove_figure_elements
from src.parser.parser_minerU.util_remove_table_block import remove_table_elements
from src.parser.parser_minerU.util_remove_html_block import remove_code_fences
from src.synapse_utils import get_data_path


def generate_visual_elements_json(user_id, kb_name, paper_name) -> None:
    """
    Processes a Markdown file to extract figure and table information,
    removes these elements from the Markdown file (overwriting it),
    and saves the extracted information into a JSON file.

    Args:
        paper_id: The unique identifier for the paper.
        markdown_filepath_str: The string path to the input Markdown file.
    """
    # markdown_filepath_str = f"{get_data_path()}/{user_id}/{kb_name}/minerU/{paper_name}/{paper_name}_v1.md"
    markdown_filepath = get_data_path() + '/' + user_id + '/' + kb_name + '/minerU/' + paper_name + '/' + paper_name + '_v1.md'
    # markdown_filepath = Path(markdown_filepath_str)
    # output_json_dir = Path("data/parsed_papers") # Base directory for the output JSON
    # output_json_path = f"{get_data_path()}/{user_id}/{kb_name}/minerU/{paper_name}/{paper_name}_vis.json"
    output_json_path = get_data_path() + '/' + user_id + '/' + kb_name + '/minerU/' + paper_name + '/' + paper_name + '_vis.json'

    if not markdown_filepath.is_file():
        print(f"Error: Markdown file not found at {markdown_filepath}")
        return

    print(f"Extracting figures and tables from: {markdown_filepath.name}")
    try:
        with open(markdown_filepath, "r", encoding="utf-8") as f:
            md_lines = f.readlines()
        # These functions are expected to take a Path object or string path
        figures = extract_figure_blocks(md_lines)
        tables = extract_all_table_blocks(md_lines)
    except Exception as e:
        print(f"Error during extraction: {e}")
        return

    print(f"Modifying Markdown file: {markdown_filepath.name}")
    try:
        with open(markdown_filepath, "r", encoding="utf-8") as f:
            md_lines = f.readlines()

        # These functions are expected to take a list of lines and return a list of lines
        md_lines = remove_table_elements(md_lines)
        md_lines = remove_figure_elements(md_lines)
        md_lines = remove_code_fences(md_lines) # Assuming this also takes List[str]

        # Overwrite the original markdown file with the modified content
        # Consider writing to a new file to avoid accidental data loss if that's preferred.
        # markdown_filepath_str2 = f"{get_data_path()}/{user_id}/{kb_name}/minerU/{paper_name}/{paper_name}_v2.md"
        # markdown_filepath2 = Path(markdown_filepath_str2)
        markdown_filepath2 = get_data_path() + '/' + user_id + '/' + kb_name + '/minerU/' + paper_name + '/' + paper_name + '_v2.md'
        with open(markdown_filepath2, "w", encoding="utf-8") as f:
            f.writelines(md_lines)
        print(f"Markdown file {markdown_filepath2.name} has been updated.")

    except Exception as e:
        print(f"Error processing or writing Markdown file: {e}")
        return

    # Prepare data for JSON output
    vis_elements: Dict[str, Dict[str, Any]] = {}
    for figure in figures:
        # Ensure keys exist in the figure dictionary, providing defaults if not
        figure_number = figure.get('figure_number', 'UnknownFigure')
        fig_obj = {
            "caption": figure.get("full_caption_line", "N/A"),
            "content": figure.get("content_text", "") # Assuming 'content_text' from previous script
        }
        vis_elements[f'Figure {figure_number}'] = fig_obj
    
    print(f"Extracted {len(figures)} figures and {len(tables)} tables.")
    for table in tables:
        # Ensure keys exist in the table dictionary
        table_number = table.get('table_number', 'UnknownTable')
        table_obj = {
            "caption": table.get("full_caption_line", "N/A"),
            "content": table.get("content_html", "") # Assuming 'content_html' from previous script
        }
        vis_elements[f'Table {table_number}'] = table_obj

    
    
    print(f"Saving extracted visual elements to: {output_json_path}")
    try:
        # output_json_dir.mkdir(parents=True, exist_ok=True) # Ensure directory exists
        with open(output_json_path, "w", encoding="utf-8") as f:
            json.dump(vis_elements, f, indent=4, ensure_ascii=False)
        print("JSON file created successfully.")
    except Exception as e:
        print(f"Error writing JSON file: {e}")