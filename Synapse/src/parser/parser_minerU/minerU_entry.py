from src.parser.parser_minerU.s1_pdf2md import pdf2md_minerU
from src.parser.parser_minerU.s2_image2table import image2table
from src.parser.parser_minerU.s3_extract_table_figure import generate_visual_elements_json
from src.parser.parser_minerU.s4_md2json import convert_markdown_to_json
from src.parser.parser_minerU.s5_assign_tag import assign_tag
def minerU_entry(user_id: str, kb_name: str, paper_name: str) -> None:
    """
    Entry point for processing a paper using the MinerU parser.
    
    Args:
        user_id: The unique identifier for the user.
        kb_name: The name of the knowledge base.
        paper_name: The name of the paper to be processed.
    """
    # # Step 1: Convert PDF to Markdown
    print(f"Processing paper '{paper_name}' for user '{user_id}' in knowledge base '{kb_name}'")
    pdf2md_minerU(user_id, kb_name, paper_name)
    # return
    # # Step 2: Process images and convert them to HTML tables
    s = time.time()
    image2table(user_id, kb_name, paper_name)
    e = time.time()
    print(f"Image processing completed in {e - s:.2f} seconds for paper '{paper_name}'")


    # # Step 3: Extract figures and tables from the Markdown file
    generate_visual_elements_json(user_id, kb_name, paper_name)

    # Step 4: Convert Markdown to JSON
    convert_markdown_to_json(user_id, kb_name, paper_name, hierarchical=True, chunking=False, link_visuals=True)

    # Step 5: Assign tags to sections
    assign_tag(user_id, kb_name, paper_name, where="minerU")

# import time
# s = time.time()
# minerU_entry('1', '1', 'FLAT')
# e = time.time()
# print(f"Processing completed in {e - s:.2f} seconds for paper 'FLAT'")