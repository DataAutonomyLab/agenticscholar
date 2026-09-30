import re
import argparse
from pathlib import Path
from typing import List, Dict, Any

# Module-level constant for the compiled regular expression
FIGURE_CAPTION_REGEX = re.compile(r"^\s*Figure\s+(\d+)\s*:(.*)", re.IGNORECASE)

def extract_figure_blocks(lines: List[str]) -> List[Dict[str, Any]]:
    """
    Extracts figure blocks (content + caption) from Markdown text.

    A figure's content is identified as the contiguous block of non-empty lines
    immediately preceding its "Figure X: ..." caption. The search for content
    is bounded by the previous figure's caption or the beginning of the document.

    Args:
        markdown_content: A string containing the Markdown text.

    Returns:
        A list of dictionaries, where each dictionary represents a figure and has:
            'figure_number': The number of the figure (e.g., "1").
            'caption_text': The text of the caption.
            'content_text': The extracted content lines associated with the figure,
                            joined by newlines. Empty if no content is found.
            'full_caption_line': The original full line of the caption.
            'content_start_line': The 0-based index of the start of the content block.
                                 -1 if no content.
            'content_end_line': The 0-based index of the end of the content block.
                               -1 if no content.
            'caption_line_index': The 0-based index of the caption line.
        Returns an empty list if no figures are found.
    """
    extracted_figures: List[Dict[str, Any]] = []
    # lines: List[str] = markdown_content.splitlines()

    # --- Pass 1: Identify all figure captions and their line indices ---
    caption_details: List[Dict[str, Any]] = []
    for i, line in enumerate(lines):
        match = FIGURE_CAPTION_REGEX.match(line)
        if match:
            figure_number: str = match.group(1)
            caption_text: str = match.group(2).strip()
            caption_details.append({
                "index": i,
                "line_text": line, # Original full line
                "number": figure_number,
                "text": caption_text
            })

    if not caption_details:
        return [] # No captions found, so no figures to extract

    # --- Pass 2: For each caption, backtrack to find its associated content ---
    previous_caption_line_index = -1 # Boundary for backtracking

    for caption_info in caption_details:
        current_caption_line_index: int = caption_info["index"]
        content_lines_for_figure: List[str] = []
        content_start_idx: int = -1
        content_end_idx: int = -1

        # 1. Find the end of the content block (last non-blank line before current caption)
        # Search window: from line above current caption down to line after previous caption.
        potential_content_end_line = -1
        for i in range(current_caption_line_index - 1, previous_caption_line_index, -1):
            if lines[i].strip(): # Found a non-blank line
                potential_content_end_line = i
                break
        
        if potential_content_end_line != -1:
            content_end_idx = potential_content_end_line
            # 2. Find the start of this contiguous content block
            # Search window: from potential_content_end_line up to line after previous caption.
            content_start_idx = potential_content_end_line # Assume single line content initially
            for i in range(potential_content_end_line - 1, previous_caption_line_index, -1):
                if not lines[i].strip(): # Blank line marks the start of content (on next line)
                    content_start_idx = i + 1
                    break
                content_start_idx = i # This line is part of the content block
            
            # Extract content if a valid block was identified
            if content_start_idx <= content_end_idx : # Ensure start is not after end
                 content_lines_for_figure = lines[content_start_idx : content_end_idx + 1]

        extracted_figures.append({
            "figure_number": caption_info["number"],
            "caption_text": caption_info["text"],
            "content_text": "\n".join(content_lines_for_figure),
            "full_caption_line": caption_info["line_text"],
            "content_start_line": content_start_idx,
            "content_end_line": content_end_idx,
            "caption_line_index": current_caption_line_index
        })

        previous_caption_line_index = current_caption_line_index # Update boundary for next figure

    return extracted_figures