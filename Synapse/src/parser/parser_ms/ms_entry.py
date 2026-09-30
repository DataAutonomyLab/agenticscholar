from src.parser.parser_ms.s1_pdf2md import parse_pdf_to_markdown
from src.parser.parser_ms.s2_md2json import convert_markdown_to_json
from src.parser.parser_minerU.s5_assign_tag import assign_tag
def ms_entry(user_id: str, kb_name: str, paper_name: str) -> None:
    """
    Entry point for processing a paper using the MinerU parser.
    
    Args:
        user_id: The unique identifier for the user.
        kb_name: The name of the knowledge base.
        paper_name: The name of the paper to be processed.
    """
    # # Step 1: Convert PDF to Markdown
    import time 
    
    s = time.time()
    print(f"Processing paper '{paper_name}' for user '{user_id}' in knowledge base '{kb_name}'")
    parse_pdf_to_markdown(user_id, kb_name, paper_name)
    # # return
    # # # Step 2: Process images and convert them to HTML tables
    # image2table(user_id, kb_name, paper_name)


    # # # Step 3: Extract figures and tables from the Markdown file
    # generate_visual_elements_json(user_id, kb_name, paper_name)

    # Step 4: Convert Markdown to JSON
    convert_markdown_to_json(user_id, kb_name, paper_name, hierarchical=False, chunking=False)

    # Step 5: Assign tags to sections
    assign_tag(user_id, kb_name, paper_name)
    e = time.time()
    print(f"Processing completed in {e - s:.2f} seconds for paper '{paper_name}'")
    

# ms_entry('1', '1', 'FLAT')
