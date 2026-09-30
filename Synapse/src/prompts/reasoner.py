from src.prompts.base import run_structured_prompt


def answer_query_from_context(question, context):
    # print(query_info)    
    return run_structured_prompt("0_general_qa.yaml", {
        "question": question,
        "context": context
    }, str_type="MARKDOWN_T")