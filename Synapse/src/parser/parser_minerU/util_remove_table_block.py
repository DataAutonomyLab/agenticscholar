import re
import argparse
from pathlib import Path
from typing import List, Dict, Set, Any

# --- Module-Level Constants ---
TABLE_CAPTION_REGEX = re.compile(r"^\s*Table\s+(\d+)\s*:(.*)", re.IGNORECASE)
# Define how many lines to search downwards/upwards from caption/table tags
SEARCH_LIMIT = 15 # Increased slightly for potentially more spaced out content

# --- Helper Functions for HTML Tag Finding ---

def find_html_table_end(lines: List[str], start_index: int) -> int:
    """
    Finds the index of the line containing </table> searching downwards from start_index.
    Considers a limited search window defined by SEARCH_LIMIT.
    """
    # Limit search to SEARCH_LIMIT lines downwards or end of document
    end_search_window = min(start_index + SEARCH_LIMIT, len(lines))
    for i in range(start_index, end_search_window):
        line_cleaned = lines[i].strip().rstrip('`') # Handle potential backticks
        if '</table>' in line_cleaned:
            return i
    return -1 # Not found within the search window

def find_html_table_start_backtracking(lines: List[str], end_index: int) -> int:
    """
    Finds the index of the line containing <table> searching upwards from end_index.
    Considers a limited search window defined by SEARCH_LIMIT.
    """
    # Limit search to SEARCH_LIMIT lines upwards or beginning of document
    start_search_window = max(0, end_index - SEARCH_LIMIT)
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
    Looks downwards from the caption for a <table> tag.

    Args:
        lines: List of lines from the Markdown document.
        caption_details: List of dictionaries, each containing info about a found caption.
        processed_indices: A dictionary to track already processed captions and content ranges
                           to avoid redundant processing.

    Returns:
        A list of dictionaries, each representing a found table block with its
        caption_info, content_str, content_start, and content_end indices.
    """
    tables_found: List[Dict[str, Any]] = []
    # Get the end index of the last table found by this strategy to ensure we search forward
    last_known_table_end = processed_indices.get("caption_first_last_table_end", -1)

    for caption_info in caption_details:
        current_caption_index = caption_info["index"]
        # Skip if this caption has already been processed by any strategy
        if current_caption_index in processed_indices.get("processed_captions", set()):
            continue

        # Search for <table> tag starting from the line after the caption
        # and after the last table found by this strategy.
        table_start_search_from = max(current_caption_index + 1, last_known_table_end + 1)
        
        table_start_index = -1
        # Limit search window for <table>
        for i in range(table_start_search_from, min(table_start_search_from + SEARCH_LIMIT, len(lines))):
            line_stripped = lines[i].strip()
            if not line_stripped: continue # Skip empty lines
            line_cleaned = line_stripped.lstrip('`')
            if line_cleaned.startswith('<table'):
                table_start_index = i
                break
        
        if table_start_index != -1:
            table_end_index = find_html_table_end(lines, table_start_index)
            if table_end_index != -1:
                # Ensure this content range hasn't been processed by another strategy
                is_processed = any(
                    r_start <= table_end_index and r_end >= table_start_index
                    for r_start, r_end in processed_indices.get("processed_content_ranges", set())
                )
                if is_processed:
                    continue

                content_lines = lines[table_start_index : table_end_index + 1]
                tables_found.append({
                    "caption_info": caption_info,
                    "content_str": "\n".join(content_lines), # For debugging or further processing
                    "content_start": table_start_index,
                    "content_end": table_end_index
                })
                # Mark this caption and content range as processed
                processed_indices.setdefault("processed_captions", set()).add(current_caption_index)
                processed_indices.setdefault("processed_content_ranges", set()).add((table_start_index, table_end_index))
                last_known_table_end = table_end_index # Update for next search in this strategy

    processed_indices["caption_first_last_table_end"] = last_known_table_end
    return tables_found


def extract_tables_caption_last(
    lines: List[str],
    caption_details: List[Dict[str, Any]],
    processed_indices: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Strategy 2: Finds tables where the caption appears AFTER the HTML table content.
    Looks upwards from the caption for </table>, then further up for <table>.

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
        # Skip if this caption has already been processed
        if current_caption_index in processed_indices.get("processed_captions", set()):
            continue

        # Search upwards for </table>
        potential_table_end_index = -1
        # Limit search window for </table>
        for i in range(current_caption_index - 1, max(0, current_caption_index - 1 - SEARCH_LIMIT) -1, -1):
             line_stripped = lines[i].strip()
             if not line_stripped: continue
             line_cleaned = line_stripped.rstrip('`')
             if '</table>' in line_cleaned:
                 potential_table_end_index = i
                 break
        
        if potential_table_end_index != -1:
            # Check if this potential end index falls within an already processed content range
            is_processed_range = any(
                r_start <= potential_table_end_index <= r_end
                for r_start, r_end in processed_indices.get("processed_content_ranges", set())
            )
            if is_processed_range:
                continue

            table_start_index = find_html_table_start_backtracking(lines, potential_table_end_index)
            if table_start_index != -1:
                table_end_index = potential_table_end_index
                # Final check to ensure this precise range isn't already claimed
                is_processed_exact_range = any(
                    max(r_start, table_start_index) <= min(r_end, table_end_index)
                    for r_start, r_end in processed_indices.get("processed_content_ranges", set())
                )
                if is_processed_exact_range:
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

# --- Main Logic for Finding and Removing Blocks ---

def get_indices_of_table_blocks_to_remove(lines: List[str]) -> Set[int]:
    """
    Finds all table blocks (caption + content) using multiple strategies
    and returns a set of all line indices that should be removed.

    Args:
        lines: List of lines from the Markdown document.

    Returns:
        A set of integer line indices to be removed.
    """
    indices_to_remove: Set[int] = set()

    # First, find all potential table captions
    caption_details: List[Dict[str, Any]] = []
    for i, line in enumerate(lines):
        match = TABLE_CAPTION_REGEX.match(line)
        if match:
            caption_details.append({
                "index": i,
                "line_text": line.strip(), # Store for debugging
                "number": match.group(1),
                "text": match.group(2).strip()
            })
    
    if not caption_details:
        return indices_to_remove # No captions, so no tables to remove based on captions

    # Shared state to track what has been processed by either strategy
    # This helps avoid double-counting or conflicting assignments.
    shared_processed_indices: Dict[str, Any] = {
        "caption_first_last_table_end": -1, # Tracks end of last table found by caption_first strategy
        "processed_captions": set(),        # Set of caption indices already linked to a table
        "processed_content_ranges": set()   # Set of (start, end) tuples for content already linked
    }

    # Run Strategy 1 (Caption appears before Table Content)
    s1_results = extract_tables_caption_first(lines, caption_details, shared_processed_indices)
    for item in s1_results:
         indices_to_remove.add(item["caption_info"]["index"])
         for i in range(item["content_start"], item["content_end"] + 1):
             indices_to_remove.add(i)

    # Run Strategy 2 (Caption appears after Table Content)
    s2_results = extract_tables_caption_last(lines, caption_details, shared_processed_indices)
    for item in s2_results:
         indices_to_remove.add(item["caption_info"]["index"])
         for i in range(item["content_start"], item["content_end"] + 1):
             indices_to_remove.add(i)
    
    return indices_to_remove

def remove_table_elements(lines: List[str]) -> List[str]:
    """
    Removes table captions and their associated HTML content blocks from a list of Markdown lines.

    Args:
        lines: A list of strings representing the lines of the Markdown document.

    Returns:
        A new list of strings with table elements removed.
    """
    # print("Identifying table blocks to remove...")
    indices_to_remove = get_indices_of_table_blocks_to_remove(lines)

    if not indices_to_remove:
        # print("No table blocks found to remove.")
        return lines

    # print(f"Identified {len(indices_to_remove)} lines belonging to table blocks to be removed.")
    # print(f"Indices to remove: {sorted(list(indices_to_remove))}")

    output_lines: List[str] = []
    for i, line in enumerate(lines):
        if i not in indices_to_remove:
            output_lines.append(line) # Preserves original line endings
            
    return output_lines

# # --- File Processing ---

# def process_markdown_file_for_tables(input_path: Path, output_path: Path) -> None:
#     """
#     Reads a Markdown file, removes table elements (captions and HTML content),
#     and writes the result to an output file.

#     Args:
#         input_path: Path to the input Markdown file.
#         output_path: Path to save the modified Markdown content.
#     """
#     try:
#         with open(input_path, 'r', encoding='utf-8') as f:
#             lines = f.readlines() # Read lines with their endings
#     except FileNotFoundError:
#         print(f"Error: Input file not found at {input_path}")
#         return
#     except Exception as e:
#         print(f"Error reading input file {input_path}: {e}")
#         return

#     modified_lines = remove_table_elements(lines)

#     try:
#         output_path.parent.mkdir(parents=True, exist_ok=True) # Ensure output directory exists
#         with open(output_path, 'w', encoding='utf-8') as f:
#             f.writelines(modified_lines) # Write lines with their original endings
#         print(f"Successfully processed file. Output saved to: {output_path}")
#     except Exception as e:
#         print(f"Error writing output file {output_path}: {e}")