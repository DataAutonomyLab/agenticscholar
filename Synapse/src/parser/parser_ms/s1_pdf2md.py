import os
import json
import base64
import re
from pathlib import Path
import click
from mistralai import Mistral
from mistralai import DocumentURLChunk
from src.synapse_utils import *
from src.config.config import get_llm_config_for_module

'''
There are several steps in parsing a file:
1. Read a pdf and call mistral model to convert it into markown.
2. Read the markdown file and chunk it based on section headers.
'''

# --- Helper Functions ---
def get_text_before_references(markdown_text: str) -> str:
    """Removes the content from the "REFERENCES" section onwards in a Markdown string."""
    match = re.search(r"^#{1,6}\s*REFERENCES\s*$", markdown_text, re.MULTILINE | re.IGNORECASE)
    if not match:
        return markdown_text
    return markdown_text[:match.start()].rstrip()

def parse_pdf_to_markdown(user_id, kb_name, paper_name):
    """
    Parse a PDF file and convert it to markdown using the Mistral model.
    
    Args:
        paper_id (str): The identifier for the paper. It is unique for each paper in the repo.
        file_path (str): The path to the PDF file.
        repo_dir (str): The directory where the parsed results file will be saved.
    
    Returns: 
       
        
    """

    # Read the PDF file
    local_config = get_llm_config_for_module("Pdf2Md")
    pdf_file_name = paper_name + ".pdf"
    DataDir = get_data_path()
    
    # local_image_dir, local_md_dir = f'{DataDir}/{user_id}/{kb_name}/ms/{paper_name}/images', f'{DataDir}/{user_id}/{kb_name}/ms/{paper_name}'
    local_image_dir = DataDir / user_id / kb_name / 'ms' / paper_name / 'images'
    local_md_dir = DataDir / user_id / kb_name / 'ms' / paper_name
    os.makedirs(local_image_dir, exist_ok=True)
    
    pdf_file = DataDir / user_id / kb_name / 'pdf' / pdf_file_name
    # Path(os.path.join(f'{DataDir}/{user_id}/{kb_name}/pdf', pdf_file_name))
    Mistralai_API_Key = local_config["api_key"]
    client = Mistral(api_key=Mistralai_API_Key)
    uploaded_file = None

    model = local_config["default_model"]

    # Convert the PDF file to markdown using Mistral
    try:

        click.echo(f"Uploading file {pdf_file.name}...", err=True)
        uploaded_file = client.files.upload(
            file={
                "file_name": pdf_file.stem,
                "content": pdf_file.read_bytes(),
            },
            purpose="ocr",
        )

        signed_url = client.files.get_signed_url(file_id=uploaded_file.id, expiry=1)

        click.echo(f"Processing with OCR model: {model}...", err=True)
        pdf_response = client.ocr.process(
            document=DocumentURLChunk(document_url=signed_url.url),
            model=model,
            include_image_base64=True,
        )

        response_dict = json.loads(pdf_response.model_dump_json())

        # Process Images
        image_map = {}
        # image_dir = Path(output_dir)
        image_count = 0

        for page in response_dict.get("pages", []):
            # pass
            for img in page.get("images", []):
                if "id" in img and "image_base64" in img:
                    image_data = img["image_base64"]
                    # Strip the prefix if it exists
                    if image_data.startswith("data:image/"):
                        image_data = image_data.split(",", 1)[1]
                    image_filename = img["id"]
                    image_path = local_image_dir / image_filename
                    print(f"Saving image {image_filename} to {image_path}")
                    with open(image_path, "wb") as img_file:
                        img_file.write(base64.b64decode(image_data))
                    # Map image_id to relative path for referencing in markdown/html
                    image_map[image_filename] = image_filename
                    image_count += 1
        # click.echo(f"Extracted {image_count} images to {image_dir}", err=True)
        # Process Text
        # Concatenate markdown content from all pages
        markdown_contents = [
            page.get("markdown", "") for page in response_dict.get("pages", [])
        ]
        markdown_text = "\n\n".join(markdown_contents)

        # Handle image references in markdown if needed
        for img_id, img_src in image_map.items():
            # Replace any markdown image references with the correct path/data URI
            markdown_text = re.sub(
                r"!\[(.*?)\]\(" + re.escape(img_id) + r"\)",
                r"![\1](" + img_src + r")",
                markdown_text,
            )
        # Save the markdown content to a file
        output_file = local_md_dir / f'{paper_name}.md'
        output_file.write_text(markdown_text)
        
        # try:
        original_text = output_file.read_text(encoding='utf-8')

        # 2. Remove references section IN-MEMORY
        print("Removing references section... avoid processing the appendix")
        text_no_refs = get_text_before_references(original_text)
        output_file.write_text(text_no_refs)


    except Exception as e:
        # os.rmdir(os.path.join(repo_dir, f'{paper_id}_mai'))
        raise click.ClickException(f"Error: {e}")
    finally:
        # delete the directory we created
       
        try:
            if uploaded_file:
                # delete the uploaded file from Mistral
                client.files.delete(file_id=uploaded_file.id)
                
        except Exception as e:
                click.echo(f"Error deleting uploaded file: {e}")
# test
# import sys
# user_id= '1'
# kb_name='1'
# paper_name = 'FLAT'
# parse_pdf_to_markdown(user_id, kb_name, paper_name)
# parse_pdf_to_markdown("uae")
