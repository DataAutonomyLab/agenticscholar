from pathlib import Path
from typing import List

def remove_code_fences(lines: List[str]) -> List[str]:
    """
    Removes lines that exactly match '```html' or '```' (after stripping whitespace).

    Args:
        lines: A list of strings, where each string is a line from the input.

    Returns:
        A new list of strings with the specified code fence lines removed.
        Original line endings are preserved for the lines that are kept.
    """
    output_lines: List[str] = []
    # removed_count = 0 # Uncomment if you need to track how many lines were removed
    for line in lines:
        line_stripped = line.strip()
        # Check if the stripped line exactly matches the target fences
        if line_stripped == '```html' or line_stripped == '```':
            # removed_count += 1
            continue  # Skip this line
        else:
            output_lines.append(line)  # Keep this line (with original ending)

    # if removed_count > 0:
    #     print(f"Removed {removed_count} code fence lines.")
    # else:
    #     print("No code fence lines found to remove.")
    return output_lines

# def process_file_for_fences(input_path: Path, output_path: Path) -> None:
#     """
#     Reads a file, removes code fences, and writes the result to an output file.

#     Args:
#         input_path: Path to the input file.
#         output_path: Path to save the modified content.
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

#     modified_lines = remove_code_fences(lines)

#     try:
#         output_path.parent.mkdir(parents=True, exist_ok=True) # Ensure output directory exists
#         with open(output_path, 'w', encoding='utf-8') as f:
#             f.writelines(modified_lines) # Write lines with their original endings
#         print(f"Successfully processed file. Output saved to: {output_path}")
#     except Exception as e:
#         print(f"Error writing output file {output_path}: {e}")