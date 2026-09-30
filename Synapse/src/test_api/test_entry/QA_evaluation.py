import os
import json
from tqdm import tqdm
from src.executor_qa_lc.large_context_qa import PaperContentLoader, PaperContent
from src.synapse_utils import *
from pathlib import Path
from src.prompts.base import run_structured_prompt 

def get_user_and_kb_name(key: str):
    user_id = f"test{key}-user"
    kb_name = f"test{key}-kb"
    return user_id, kb_name


def queryLLM(user_query, papers, result):
    
    
    combined_content = ""
    paper_info = []
    
    i = 0
    for paper in papers:
        content = paper.content
        # if len(content) > max_length_per_paper:
        #     content = content[:max_length_per_paper] + "\n[Truncated...]"
        
        combined_content += f"\n<Start of Paper {i}>\n<Paper Title> {paper.title} (ID: {paper.paper_id}) <End of Paper Title>\n"
        combined_content += '<Paper Content>' + content + "\n" + '<End of Paper Content>' + "\n" + '<End of Paper {i}>\n'
        
        paper_info.append({
            "id": paper.paper_id,
            "title": paper.title,
            "was_truncated": False
        })
    paper_list_text = "\n".join([f"- {info['title']} (ID: {info['id']})" for info in paper_info])
    out = run_structured_prompt("QA-evaluation-prompt.yaml",
                          {"user_query": user_query, 
                           "paper_list": paper_list_text, 
                           "paper_contents": combined_content, 
                           "result": result}, str_type="MARKDOWN_T", is_reserch=False, LLM_Type='Evaluation')
    return out["response"]


def QA_evaluation(topic: str, key: str, which = "our_results"):
    base_dir = PROJECT_ROOT / "src" / "test_api" / topic 
    query_json = base_dir / f"query_{topic}.json"
    save_dir = base_dir / "evaluation-output" / which
    os.makedirs(save_dir, exist_ok=True)
    our_jsonl      = base_dir / f"{topic}_our_results.jsonl"
    # planid_path   = base_dir / f"{topic}_plan_id_estimation.jsonl"
    baseline_jsonl     = base_dir / f"{topic}_baseline_results.jsonl"
    
    # 读取 query 列表
    with open(query_json, "r", encoding="utf-8") as f:
        queries = json.load(f)

    # 读取 baseline 结果
    baseline_results = {}
    with open(baseline_jsonl, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                item = json.loads(line)
                baseline_results[item["query_id"]] = item["result"]

    # 读取 our 结果
    our_results = {}
    with open(our_jsonl, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                item = json.loads(line)
                our_results[item["query_id"]] = item["result"]

    # 遍历每个 query
    
    user_id, kb_name = get_user_and_kb_name(key)
    paperLoader = PaperContentLoader(user_id, kb_name)
    
    
    for query in tqdm(queries[:50], desc="Processing queries"):
        qid = query["query_id"]
        user_query = query["user_query"]
        paper_lists = query["paper_lists"]

        if which == "baseline":
            our_result = baseline_results.get(qid, "[No baseline result]")
        else:
            our_result = our_results.get(qid, "[No our result]")
        paper_contents = paperLoader.load_multiple_papers(paper_lists)
        

        # 调用 F
        result_str = queryLLM(user_query, paper_contents, our_result)

        # 保存结果到 md 文件
        output_path = os.path.join(save_dir, f"{qid}.md")
        with open(output_path, "w", encoding="utf-8") as out_f:
            out_f.write(result_str)


if __name__ == "__main__":
    QA_evaluation('trajectory_search', 'TR', which="baseline")