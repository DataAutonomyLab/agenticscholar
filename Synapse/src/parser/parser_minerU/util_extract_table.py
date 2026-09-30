import re
import argparse
from pathlib import Path
from typing import List, Dict, Set, Any

# --- Module-Level Constants ---
TABLE_CAPTION_REGEX = re.compile(r"^\s*Table\s+(\d+)\s*:(.*)", re.IGNORECASE)
# Define how many lines to search downwards/upwards from caption/table tags
# This limit is applied when initially searching for a <table> or </table> tag
# relative to a caption.
SEARCH_LIMIT = 15

# --- Helper Functions for HTML Tag Finding ---

def find_html_table_end(lines: List[str], start_index: int) -> int:
    """
    Finds the index of the line containing </table> searching downwards from start_index.
    This search is NOT limited by SEARCH_LIMIT, assuming a table once started, must end.
    """
    for i in range(start_index, len(lines)):
        line_cleaned = lines[i].strip().rstrip('`') # Handle potential backticks
        if '</table>' in line_cleaned:
            return i
    return -1 # Not found

def find_html_table_start_backtracking(lines: List[str], end_index: int, search_limit: int = SEARCH_LIMIT) -> int:
    """
    Finds the index of the line containing <table> searching upwards from end_index.
    Considers a limited search window.
    """
    start_search_window = max(0, end_index - search_limit)
    for i in range(end_index, start_search_window - 1, -1):
         line_stripped = lines[i].strip()
         line_cleaned = line_stripped.lstrip('`') # Handle potential backticks
         if line_cleaned.startswith('<table'):
             return i
    return -1 # Not found within the search window

# --- Table Extraction Strategies ---

def extract_tables_caption_first(
    lines: List[str],
    caption_details: List[Dict[str, Any]],
    processed_indices: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Strategy 1: Finds tables where the caption appears BEFORE the HTML table content.
    Looks downwards from the caption for a <table> tag within SEARCH_LIMIT.

    Args:
        lines: List of lines from the Markdown document.
        caption_details: List of dictionaries, each containing info about a found caption.
        processed_indices: A dictionary to track already processed captions and content ranges.

    Returns:
        A list of dictionaries, each representing a found table block with its
        caption_info, content_str, content_start, and content_end indices.
    """
    tables_found: List[Dict[str, Any]] = []
    last_known_table_end_s1 = processed_indices.get("caption_first_last_table_end", -1)

    for caption_info in caption_details:
        current_caption_index = caption_info["index"]
        if current_caption_index in processed_indices.get("processed_captions", set()):
            continue

        table_start_index = -1
        # Search for <table> tag starting from the line after the caption
        # and also after the end of the last table found by this strategy.
        search_start_for_table_tag = max(current_caption_index + 1, last_known_table_end_s1 + 1)
        search_end_limit_for_table_tag = min(search_start_for_table_tag + SEARCH_LIMIT, len(lines))

        for i in range(search_start_for_table_tag, search_end_limit_for_table_tag):
            line_stripped = lines[i].strip()
            if not line_stripped: continue
            line_cleaned = line_stripped.lstrip('`')
            if line_cleaned.startswith('<table'):
                table_start_index = i
                break
        
        if table_start_index != -1:
            # Once <table> is found, search for </table> until end of document
            table_end_index = find_html_table_end(lines, table_start_index)
            if table_end_index != -1:
                 # Ensure this content range hasn't been processed by another strategy
                is_already_processed = any(
                    r_start <= table_end_index and r_end >= table_start_index
                    for r_start, r_end in processed_indices.get("processed_content_ranges", set())
                )
                if is_already_processed:
                    continue

                content_lines = lines[table_start_index : table_end_index + 1]
                tables_found.append({
                    "caption_info": caption_info,
                    "content_str": "\n".join(content_lines),
                    "content_start": table_start_index,
                    "content_end": table_end_index
                })
                processed_indices.setdefault("processed_captions", set()).add(current_caption_index)
                processed_indices.setdefault("processed_content_ranges", set()).add((table_start_index, table_end_index))
                last_known_table_end_s1 = table_end_index

    processed_indices["caption_first_last_table_end"] = last_known_table_end_s1
    return tables_found


def extract_tables_caption_last(
    lines: List[str],
    caption_details: List[Dict[str, Any]],
    processed_indices: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Strategy 2: Finds tables where the caption appears AFTER the HTML table content.
    Looks upwards from the caption for </table> (within SEARCH_LIMIT),
    then further up for <table> (within a potentially wider SEARCH_LIMIT).

    Args:
        lines: List of lines from the Markdown document.
        caption_details: List of dictionaries, each containing info about a found caption.
        processed_indices: A dictionary to track already processed captions and content ranges.

    Returns:
        A list of dictionaries for found table blocks.
    """
    tables_found: List[Dict[str, Any]] = []

    for caption_info in caption_details:
        current_caption_index = caption_info["index"]
        if current_caption_index in processed_indices.get("processed_captions", set()):
            continue

        potential_table_end_index = -1
        # 1. Search upwards from caption for </table> within SEARCH_LIMIT
        search_start_for_end_tag = current_caption_index - 1
        search_limit_for_end_tag = max(0, search_start_for_end_tag - SEARCH_LIMIT)

        for i in range(search_start_for_end_tag, search_limit_for_end_tag - 1, -1):
             line_stripped = lines[i].strip()
             if not line_stripped: continue
             line_cleaned = line_stripped.rstrip('`')
             if '</table>' in line_cleaned:
                 potential_table_end_index = i
                 break
        
        if potential_table_end_index != -1:
            # Check if this potential end index falls within an already processed content range
            is_range_processed = any(
                r_start <= potential_table_end_index <= r_end
                for r_start, r_end in processed_indices.get("processed_content_ranges", set())
            )
            if is_range_processed:
                continue

            # 2. If </table> found, search upwards from there for <table>
            # Allow a potentially larger search for the start tag if needed
            table_start_index = find_html_table_start_backtracking(lines, potential_table_end_index, search_limit=SEARCH_LIMIT * 2)

            if table_start_index != -1:
                table_end_index = potential_table_end_index
                # Final check to ensure this precise range (start to end) isn't already claimed
                # This handles cases where a sub-part of a larger processed block might be re-evaluated
                is_exact_range_processed = any(
                    max(r_start, table_start_index) <= min(r_end, table_end_index)
                    for r_start, r_end in processed_indices.get("processed_content_ranges", set())
                )
                if is_exact_range_processed:
                    continue
                
                content_lines = lines[table_start_index : table_end_index + 1]
                tables_found.append({
                    "caption_info": caption_info,
                    "content_str": "\n".join(content_lines),
                    "content_start": table_start_index,
                    "content_end": table_end_index
                })
                processed_indices.setdefault("processed_captions", set()).add(current_caption_index)
                processed_indices.setdefault("processed_content_ranges", set()).add((table_start_index, table_end_index))
    return tables_found

# --- Orchestration Logic ---

def extract_all_table_blocks(lines: List[str]) -> List[Dict[str, Any]]:
    """
    Orchestrates the extraction of table blocks by finding all captions and then
    applying two strategies (caption before content, caption after content)
    to associate captions with their HTML table content.

    Args:
        markdown_content: A string containing the full Markdown text.

    Returns:
        A list of dictionaries, where each dictionary represents an extracted
        table block, sorted by the original caption line number. Each dictionary contains:
            'table_number': The number of the table (e.g., "1").
            'caption_text': The text of the caption.
            'content_html': The extracted HTML table content lines, joined by newlines.
            'full_caption_line': The original full line of the caption.
            'content_start_line': The 0-based index of the start of the HTML content.
            'content_end_line': The 0-based index of the end of the HTML content.
            'caption_line_index': The 0-based index of the caption line.
    """
    # lines: List[str] = markdown_content.splitlines()
    all_extracted_items: List[Dict[str, Any]] = []

    # --- Pass 1: Identify all table captions ---
    caption_details: List[Dict[str, Any]] = []
    for i, line in enumerate(lines):
        match = TABLE_CAPTION_REGEX.match(line)
        if match:
            caption_details.append({
                "index": i,
                "line_text": line, # Original full line
                "number": match.group(1),
                "text": match.group(2).strip()
            })
    
    if not caption_details:
        return [] # No captions found, so no tables to extract

    # --- Shared state for tracking processed elements ---
    # This dictionary is passed to and modified by the strategy functions.
    shared_processed_data: Dict[str, Any] = {
        "caption_first_last_table_end": -1, # Tracks end of last table for caption_first strategy
        "processed_captions": set(),        # Set of caption indices already linked to a table
        "processed_content_ranges": set()   # Set of (start, end) tuples for content already linked
    }

    # --- Run Strategy 1 (Caption before Table Content) ---
    s1_results = extract_tables_caption_first(lines, caption_details, shared_processed_data)
    all_extracted_items.extend(s1_results)

    # --- Run Strategy 2 (Caption after Table Content) ---
    # Strategy 2 will use the updated shared_processed_data from Strategy 1
    s2_results = extract_tables_caption_last(lines, caption_details, shared_processed_data)
    all_extracted_items.extend(s2_results)

    # --- Sort and Format Final Results ---
    # Sort all found items by their original caption line index
    all_extracted_items.sort(key=lambda x: x["caption_info"]["index"])

    final_table_blocks: List[Dict[str, Any]] = []
    for item in all_extracted_items:
        final_table_blocks.append({
            "table_number": item["caption_info"]["number"],
            "caption_text": item["caption_info"]["text"],
            "content_html": item["content_str"],
            "full_caption_line": item["caption_info"]["line_text"],
            "content_start_line": item["content_start"],
            "content_end_line": item["content_end"],
            "caption_line_index": item["caption_info"]["index"]
        })

    return final_table_blocks