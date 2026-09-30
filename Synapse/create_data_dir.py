from pathlib import Path
import shutil

def setup_directories():
    base_dir = Path.cwd()

    # (1) Create data/test-user/test-kb/pdf
    pdf_dir = base_dir / "data" / "test-user" / "test-kb" / "pdf"
    pdf_dir.mkdir(parents=True, exist_ok=True)
    print(f"Created: {pdf_dir}")

    # (2) Create data/db
    db_dir = base_dir / "data" / "db"
    db_dir.mkdir(parents=True, exist_ok=True)
    print(f"Created: {db_dir}")

    # (3) Copy resource/docker-compose.yaml into data/db
    src_file = base_dir / "resources" / "docker-compose.yaml"
    dst_file = db_dir / "docker-compose.yaml"

    if src_file.exists():
        shutil.copy(src_file, dst_file)
        print(f"Copied {src_file} -> {dst_file}")
    else:
        print(f"Source file not found: {src_file}")

if __name__ == "__main__":
    setup_directories()