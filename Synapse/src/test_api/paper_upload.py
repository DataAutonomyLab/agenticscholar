from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse
import sys
from src.load_entry import load_entry
from src.synapse_utils import get_data_path
import os
from pathlib import Path
import warnings
warnings.filterwarnings("ignore", message="builtin type swigvarlink has no __module__ attribute")

KEY = 'IR'
user_id = f"test{KEY}-user"
kb_name = f"test{KEY}-kb"
where = "ms"
    
def upload_one(paper_name) -> tuple[str, bool, str]:
    """
    Upload a single PDF by calling load_entry with the paper's stem (name without .pdf).
    Returns (paper_name, success, error_message_if_any)
    """
    
    try:
        load_entry(user_id, kb_name, paper_name, where)
        return (paper_name, True, "")
    except Exception as e:
        return (paper_name, False, str(e))

def main():
    parser = argparse.ArgumentParser(
        description="Upload a single paper (by name) or all PDFs in a directory."
    )
    
    parser.add_argument("--workers", type=int, default=8, help="Parallel workers for directory mode (default: 8)")
    parser.add_argument("--paper_name", type=str, default="N/A", help="Name of the paper to upload (without .pdf)")
    args = parser.parse_args()
    
    if args.paper_name != "N/A":
        # Single paper mode
        paper_name = args.paper_name
        print(f"Uploading single paper: {paper_name}")
        success = upload_one(paper_name)
        if success[1]:
            print(f"[SUCCESS] Uploaded paper: {paper_name}")
        else:
            print(f"[FAILED] Uploading paper {paper_name} failed with error: {success[2]}")
    else:
        pdf_dir = get_data_path() / user_id / kb_name / "pdf"
        pdf_files = []
        for entry in os.scandir(pdf_dir):
            if entry.is_file() and entry.name.lower().endswith(".pdf"):
                pdf_files.append(Path(entry.name))
        if not pdf_files:
            print(f"No PDF files found in directory: {pdf_dir}")
            sys.exit(1)
            
        print(f"Uploading all PDFs in directory: {pdf_dir} with {args.workers} workers")
        successes = 0
        failures = 0
        errors: list[str] = []

        print([p.stem for p in pdf_files])
        # return
        # with ThreadPoolExecutor(max_workers=args.workers) as ex:
        #     futures = [ex.submit(upload_one, p.stem) for p in pdf_files]
        #     for fut in as_completed(futures):
        #         paper_name, ok, err = fut.result()
        #         if ok:
        #             successes += 1
        #             print(f"[OK] {paper_name}")
        #         else:
        #             failures += 1
        #             errors.append(f"{paper_name}: {err}")
        #             print(f"[FAIL] {paper_name} -> {err}")
        for p in pdf_files:
            paper_name = p.stem
            result = upload_one(paper_name)
            if result[1]:
                successes += 1
                print(f"[OK] {paper_name}")
            else:
                failures += 1
                errors.append(f"{paper_name}: {result[2]}")
                print(f"[FAIL] {paper_name} -> {result[2]}")
        print(f"\nDone. Success: {successes}, Failures: {failures}")
        if failures:
            print("Errors:")
            for line in errors:
                print("  -", line)
        return

if __name__ == "__main__":
    main()