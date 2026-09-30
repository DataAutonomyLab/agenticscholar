import re
from pathlib import Path
from typing import List, Dict, Set

# Module-level constant for the compiled regular expression
CAPTION_REGEX = re.compile(r"^\s*Figure\s+(\d+)\s*:(.*)", re.IGNORECASE)

def find_figure_blocks_indices(lines: List[str]) -> List[Dict[str, int]]:
    """
    Identifies figure blocks (caption and associated content lines) in a list of Markdown lines.

    A figure block's content is defined as the contiguous block of non-empty lines
    immediately preceding its caption, bounded by the previous figure caption
    or the beginning of the document.

    Args:
        lines: A list of strings, where each string is a line from the Markdown document.

    Returns:
        A list of dictionaries. Each dictionary represents a detected figure block
        and contains:
            'caption_index': The line index of the figure caption.
            'content_start': The starting line index of the content associated with the figure.
                             -1 if no content block is found.
            'content_end': The ending line index of the content associated with the figure.
                           -1 if no content block is found.
    """
    figure_blocks: List[Dict[str, int]] = []
    
    # First pass: find all caption lines and their indices
    caption_line_indices: List[int] = []
    for i, line in enumerate(lines):
        if CAPTION_REGEX.match(line):
            caption_line_indices.append(i)

    if not caption_line_indices:
        return [] # No captions found

    previous_caption_index = -1

    # Second pass: determine content indices for each caption
    for current_caption_index in caption_line_indices:
        content_start = -1
        content_end = -1

        # Search for the end of the content block (last non-blank line before current caption)
        # The search range is from the line just above the current caption
        # down to the line just after the previous caption.
        for i in range(current_caption_index - 1, previous_caption_index, -1):
            if lines[i].strip(): # Found a non-blank line
                content_end = i
                break
        
        if content_end != -1:
            # If a content_end was found, search for the start of this content block.
            # The block starts from content_end and goes upwards until a blank line
            # or the line after the previous caption is encountered.
            content_start = content_end # Initialize start with the end
            for i in range(content_end - 1, previous_caption_index, -1):
                if not lines[i].strip(): # Found a blank line
                    content_start = i + 1 # Content starts on the line after the blank line
                    break
                content_start = i # This line is part of the content block
            # If the loop finished without hitting a blank line, content_start
            # correctly points to previous_caption_index + 1 (or 0 if it was the first caption).
        
        figure_blocks.append({
            "caption_index": current_caption_index,
            "content_start": content_start,
            "content_end": content_end
        })

        previous_caption_index = current_caption_index

    return figure_blocks

def remove_figure_elements(lines: List[str]) -> List[str]:
    """
    Removes figure captions and their associated content blocks from a list of Markdown lines.

    Args:
        lines: A list of strings representing the lines of the Markdown document.

    Returns:
        A new list of strings with figure elements removed.
    """
    blocks_to_remove = find_figure_blocks_indices(lines)
    
    if not blocks_to_remove:
        # print("No figure blocks found to remove.")
        return lines # Return original lines if no figures are found

    indices_to_remove: Set[int] = set()
    for block in blocks_to_remove:
        # Add caption line index
        indices_to_remove.add(block["caption_index"])
        
        # Add content line indices if a valid content block was found
        if block["content_start"] != -1 and block["content_end"] != -1:
            for i in range(block["content_start"], block["content_end"] + 1):
                indices_to_remove.add(i)
    
    # print(f"Identified {len(indices_to_remove)} lines belonging to {len(blocks_to_remove)} figure blocks to be removed.")
    # print(f"Indices to remove: {sorted(list(indices_to_remove))}")

    # Create a new list containing only the lines that are not marked for removal
    output_lines: List[str] = []
    for i, line in enumerate(lines):
        if i not in indices_to_remove:
            output_lines.append(line) # Preserves original line endings
            
    return output_lines

# def process_markdown_file(input_path: Path, output_path: Path) -> None:
#     """
#     Reads a Markdown file, removes figure elements, and writes the result to an output file.

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

#     modified_lines = remove_figure_elements(lines)

#     try:
#         with open(output_path, 'w', encoding='utf-8') as f:
#             f.writelines(modified_lines) # Write lines with their original endings
#         print(f"Successfully processed file. Output saved to: {output_path}")
#     except Exception as e:
#         print(f"Error writing output file {output_path}: {e}")