import os

from magic_pdf.data.data_reader_writer import FileBasedDataWriter, FileBasedDataReader
from magic_pdf.data.dataset import PymuDocDataset
from magic_pdf.model.doc_analyze_by_custom_model import doc_analyze
from magic_pdf.config.enums import SupportedPdfParseMethod
from src.synapse_utils import *

def pdf2md_minerU(user_id, kb_name, paper_name):
    """
    Convert PDF to Markdown using the PymuDocDataset and custom model.
    This function reads a PDF file, processes it, and generates markdown content
    along with various outputs like images, layout, spans, and JSON files.
    """
    name_without_suff = paper_name
    pdf_file_name = paper_name + ".pdf"  # assuming paper_name is the name of the pdf file without suffix

    # prepare env
    DataDir = get_data_path()
    # local_image_dir, local_md_dir = f'{DataDir}/{user_id}/{kb_name}/minerU/{paper_name}/images', f'{DataDir}/{user_id}/{kb_name}/minerU/{paper_name}'
    local_image_dir = DataDir + '/' + user_id + '/' + kb_name + '/minerU/' + paper_name + '/images'
    local_md_dir = DataDir + '/' + user_id + '/' + kb_name + '/minerU/' + paper_name
    image_dir = str(os.path.basename(local_image_dir))

    os.makedirs(local_image_dir, exist_ok=True)

    image_writer, md_writer = FileBasedDataWriter(local_image_dir), FileBasedDataWriter(
        local_md_dir
    )

    # read bytes
    reader1 = FileBasedDataReader("")
    # pdf_path = os.path.join(f'{DataDir}/{user_id}/{kb_name}/pdf', pdf_file_name)
    pdf_path = DataDir + '/' + user_id + '/' + kb_name + '/pdf/' + pdf_file_name
    pdf_bytes = reader1.read(pdf_path)  # read the pdf content

    # proc
    ## Create Dataset Instance
    ds = PymuDocDataset(pdf_bytes)

    ## inference
    if ds.classify() == SupportedPdfParseMethod.OCR:
        print("Detected OCR mode for PDF parsing.")
        infer_result = ds.apply(doc_analyze, ocr=True)

        ## pipeline
        pipe_result = infer_result.pipe_ocr_mode(image_writer)

    else:
        print("Detected non-OCR mode for PDF parsing.")
        infer_result = ds.apply(doc_analyze, ocr=False)

        ## pipeline
        pipe_result = infer_result.pipe_txt_mode(image_writer)

    ### draw model result on each page
    infer_result.draw_model(os.path.join(local_md_dir, f"{name_without_suff}_model.pdf"))

    ### get model inference result
    model_inference_result = infer_result.get_infer_res()

    ### draw layout result on each page
    pipe_result.draw_layout(os.path.join(local_md_dir, f"{name_without_suff}_layout.pdf"))

    ### draw spans result on each page
    pipe_result.draw_span(os.path.join(local_md_dir, f"{name_without_suff}_spans.pdf"))

    ### get markdown content
    md_content = pipe_result.get_markdown(image_dir)

    ### dump markdown
    pipe_result.dump_md(md_writer, f"{name_without_suff}.md", image_dir) # the markdown genereated by minerU

    ### get content list content
    content_list_content = pipe_result.get_content_list(image_dir)

    ### dump content list
    pipe_result.dump_content_list(md_writer, f"{name_without_suff}_content_list.json", image_dir)

    ### get middle json
    middle_json_content = pipe_result.get_middle_json()

    ### dump middle json
    pipe_result.dump_middle_json(md_writer, f'{name_without_suff}_middle.json')