import json
import re
import argparse
from pathlib import Path
from typing import List, Dict, Any, Union
from src.synapse_utils import get_data_path

import os 
from google import genai
from google.genai import types
import time

import src.config.config as config


TABLE_CONVERSION_PROMPT = """
Convert the table in the image into a simple, clean HTML table.
- Return only the HTML table code, with no extra styling, in a single line.
- Represent powers of 10 using the caret (`^`) format (e.g., `3.2*10^2`, `10^-3`).
"""

FIGURE_CONVERSION_PROMPT = """
**Task: Convert the provided image into a minimal HTML table.**

1.  **Identify Content:** Determine if the image contains a table, bar chart, line chart, scatter plot, radar chart, pie chart, or box plot.
2.  **Handle Unsupported Content:** If the image contains none of the supported types, respond with the exact string: `NO`.
3.  **Process Supported Content:**
    - Convert all supported figures into HTML tables.
    - If there are multiple sub-figures (e.g., (a), (b)), generate a separate HTML table for each.
    - Return only the HTML table code, concatenated into a single line.
    - Standardize numbers with powers of 10 using the caret (`^`) format (e.g., `3.2*10^2`).
"""



# --- Helper Functions ---
def get_text_before_references(markdown_text: str) -> str:
    """Removes the content from the "REFERENCES" section onwards in a Markdown string."""
    match = re.search(r"^#{1,6}\s*REFERENCES\s*$", markdown_text, re.MULTILINE | re.IGNORECASE)
    if not match:
        return markdown_text
    return markdown_text[:match.start()].rstrip()

def extract_html_table(html_content: str) -> str:
    """Extracts the first complete <table>...</table> block from HTML content."""
    match = re.search(r"<table.*?>.*?</table>", html_content, re.DOTALL | re.IGNORECASE)
    return match.group(0) if match else ""

    
def convert_image_to_html(image_path: Path, prompt: str) -> str:
    """Converts an image to HTML, retrying up to 3 times on transient errors."""
    if not os.path.isfile(image_path):
        print(f"Warning: Image not found at {image_path}")
        return ""

    print(f"  > Converting image: {image_path}")
    
    # Define the maximum number of attempts
    max_attempts = 3

    local_config = config.get_llm_config_for_module("Image2Table")
    assert local_config["provider"] == "gemini", "Image2Table module must use Google GenAI provider"
    # --- THE RETRY LOOP ---
    for attempt in range(max_attempts):
        try:
            with open(image_path, 'rb') as f:
                img_bytes = f.read()

            client = genai.Client(api_key=local_config["api_key"])
            image_part = types.Part.from_bytes(data=img_bytes, mime_type='image/jpeg')

            response = client.models.generate_content(
                model=local_config["default_model"],
                contents=[image_part, prompt]
            )

            # 1. Success Condition: If we get a valid response, return it and exit.
            if response and response.candidates:
                print(f"  > Success on attempt {attempt + 1}.")
                return response.text.replace("\n", "")

            # 2. Permanent Failure: If blocked, stop retrying immediately.
            if response and response.prompt_feedback and response.prompt_feedback.block_reason:
                print(f"  > Request permanently blocked on attempt {attempt + 1}. Reason: {response.prompt_feedback.block_reason.name}. No further retries.")
                break # Exit the loop, don't retry

            # 3. Transient Failure: If response is empty for other reasons, log it and the loop will continue.
            print(f"  > WARNING: Attempt {attempt + 1} failed with an empty response.")

        except Exception as e:
            # Handle exceptions like network errors
            print(f"  > WARNING: Attempt {attempt + 1} failed with an exception: {e}")

        # 4. Wait before the next attempt (but not after the last one)
        if attempt < max_attempts - 1:
            print(f"  > Retrying in 2 seconds...")
            time.sleep(2)

    # 5. Final Failure: If the loop finishes without success
    print(f"  > All {max_attempts} attempts failed for image {image_path}.")
    return ""


def remove_references_section(file_path: Path):
    """Reads a Markdown file, removes the REFERENCES section, and overwrites the file."""
    if not file_path.is_file():
        print(f"Error: File not found at {file_path}")
        return

    try:
        text = file_path.read_text(encoding='utf-8')
        # Use regex to find the "REFERENCES" header and truncate the text
        match = re.search(r"^#{1,6}\s*REFERENCES\s*$", text, re.MULTILINE | re.IGNORECASE)
        if match:
            text = text[:match.start()].rstrip()
            file_path.write_text(text, encoding='utf-8')
            print(f"Removed REFERENCES section from {file_path.name}")
    except Exception as e:
        print(f"Error processing {file_path.name}: {e}")


# --- Core In-Memory Processing Functions ---

def process_figures_in_memory(paper_dir: Path, lines: List[str], paper_name: str) -> List[str]:
    """
    Finds all figures in a list of Markdown lines and replaces them with HTML tables.
    Operates entirely in-memory.
    """
    print("Processing figures...")
    processed_lines = []
    for line in lines:
        match = re.search(r"!\[\]\((.*?)\)", line)
        if match:
            img_relative_path = match.group(1)
            # img_full_path = f'{paper_dir}/{img_relative_path}'
            img_full_path = paper_dir / img_relative_path
            
            html_table = convert_image_to_html(img_full_path, FIGURE_CONVERSION_PROMPT)
            
            if html_table != "NO":
                processed_lines.append(extract_html_table(html_table))
            else:
                processed_lines.append(line) # Keep original if unsupported
        else:
            processed_lines.append(line)
    return processed_lines

def process_tables_in_memory(paper_dir: Path, lines: List[str], content_list_path: Path, paper_name: str) -> List[str]:
    """
    Replaces placeholder HTML tables in a list of Markdown lines with actual content.
    Operates entirely in-memory.
    """
    print("Processing tables...")
    try:
        with content_list_path.open('r', encoding='utf-8') as f:
            content_list = json.load(f)
    except FileNotFoundError:
        print(f"Error: Could not find content list file: {content_list_path}")
        return lines # Return original lines if data is missing

    table_triggers = {}
    for item in content_list:
        if "table_caption" not in item:
            continue
        caption = item.get('table_caption', [])
        footnote = item.get('table_footnote', [])
        img_path = item.get('img_path')

        if not img_path:
            continue

        trigger_text = ""
        if not caption and footnote and footnote[0].lower().startswith("tab"):
            trigger_text = footnote[0]
        elif caption:
            trigger_text = caption[0]
        
        if trigger_text:
            key = trigger_text.replace(" ", "")
            if key not in table_triggers:
                table_triggers[key] = []
            table_triggers[key].append(img_path)

    processed_lines = []
    html_placeholders = {i for i, line in enumerate(lines) if "<html>" in line}
    
    for i, line in enumerate(lines):
        if i in html_placeholders:
            continue

        trigger_key = line.strip().replace(" ", "")
        if trigger_key in table_triggers:
            processed_lines.append(line)
            image_paths = table_triggers[trigger_key]
            for img_path in image_paths:
                # img_full_path = f'{paper_dir}/{img_path}'
                img_full_path = paper_dir / img_path
                html_table = convert_image_to_html(img_full_path, TABLE_CONVERSION_PROMPT)
                processed_lines.append(extract_html_table(html_table))
            del table_triggers[trigger_key]
        else:
            processed_lines.append(line)
            
    return processed_lines

# --- Main Execution Block ---

def image2table(user_id, kb_name, paper_name):
    # if not CONFIG["google_api_key"] or CONFIG["google_api_key"] == "YOUR_API_KEY_HERE":
    #     print("Error: Google API key is not set. Please set the GOOGLE_API_KEY environment variable.")
    #     raise ValueError("Google API key is not set.")
    
    # paper_dir = f'{get_data_path()}/{user_id}/{kb_name}/minerU/{paper_name}'
    paper_dir = get_data_path() / user_id / kb_name / "minerU" / paper_name
    
    # Define file paths
    # md_original_path = Path(f"{paper_dir}/{paper_name}.md")
    # md_final_path = Path(f"{paper_dir}/{paper_name}_v1.md")
    # content_list_path = Path(f"{paper_dir}/{paper_name}_content_list.json")
    md_original_path = paper_dir / f"{paper_name}.md"
    md_final_path = paper_dir / f"{paper_name}_v1.md"
    content_list_path = paper_dir / f"{paper_name}_content_list.json"
    
    # --- In-Memory Pipeline ---
    # 1. Read file from disk ONCE
    print(f"Reading original file: {md_original_path}")
    try:
        original_text = md_original_path.read_text(encoding='utf-8')
    except FileNotFoundError:
        print(f"Error: Original Markdown file not found at {md_original_path}")
        return

    # 2. Remove references section IN-MEMORY
    print("Removing references section... avoid processing the appendix")
    text_no_refs = get_text_before_references(original_text)
    
    # 3. Process all figures IN-MEMORY
    lines_no_figures = process_figures_in_memory(paper_dir, text_no_refs.splitlines(), paper_name)
    
    # 4. Process all placeholder tables IN-MEMORY
    final_lines = process_tables_in_memory(paper_dir, lines_no_figures, content_list_path, paper_name)
    
    # 5. Write final result to disk ONCE
    print(f"Writing final processed file to: {md_final_path}")
    try:
        md_final_path.write_text("\n".join(final_lines), encoding='utf-8')
    except Exception as e:
        print(f"Error writing final file: {e}")
        return

    print(f"\n✅ Processing complete. Final output at: {md_final_path}")