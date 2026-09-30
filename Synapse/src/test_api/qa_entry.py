# from src.synapse_utils import *
from src.executor.executor_entry import executor_entry
import yaml
from src.routing import select_plan
from src.executor_qa_lc.large_context_qa import LargeContextQAEngine
from src.executor_multistep.multi_step_engine import ExecutionPlanBuilder, MultiStepResearchEngine
from src.executor_multistep.multi_step_optimizer import ResearchPlanGenerator, ResearchPlanInstantiation
import argparse  # Import argparse for command-line arguments


import json
from pathlib import Path
import time
from src.synapse_utils import *

# user query (NL); plan_id (in-system); paper_lists
# -> GPT: user user_query + paper_lists
# KEY = 'TF'
# user_id = f"test{KEY}-user"
# kb_name = f"test{KEY}-kb"

def get_user_and_kb_name(key: str):
    user_id = f"test{key}-user"
    kb_name = f"test{key}-kb"
    return user_id, kb_name
    
def multi_step_qa(key, query, paper_lists, where="ms"):
    user_id, kb_name = get_user_and_kb_name(key)
    user_id_2 = user_id.split('-')[0].lower()
    kb_name_2 = kb_name.split('-')[0].lower()
    db_name = f"SYNAPSE{user_id_2}{kb_name_2}_{where}"
    
    # initialize some process class
    plan_generator = ResearchPlanGenerator()
    plan_instantiation = ResearchPlanInstantiation()
    execution_plan_builder = ExecutionPlanBuilder(db_name)
    research_engine = MultiStepResearchEngine(db_name)

    # process the plan
    research_plan = plan_generator.generate_plan(query, paper_lists)
    if research_plan:
        print("Generated Research Plan:")
        print(research_plan)
        research_plan.visualize("research_plan_before.dot")

        plan_instantiation.instantiate_plan(research_plan)
        research_plan.visualize("research_plan_after.dot")
        research_plan.serialize()

        execution_graph = execution_plan_builder.build_execution_graph(research_plan)

        print("Generate ExecutionGraph:")
        execution_graph.visualize()
        return True, research_plan
    
    #     execution_result = research_engine.execute_plan(execution_graph)
    #     # print("Multi-step research completed:")
    #     # print(execution_result["final_synthesis"])
    #     return True, execution_result["final_synthesis"]
    else:
        # print("Query doesn't require multi-step processing")
        return False, ""

def our_qa_plan_id(key, plan_id, paper_lists, user_query="", where="ms"):
    plan_path = get_plan_path() / f"{plan_id}.yaml"
    # user_id = "test-user"
    # kb_name = "test-kb"
    user_id, kb_name = get_user_and_kb_name(key)
    user_id_2 = user_id.split('-')[0].lower()
    kb_name_2 = kb_name.split('-')[0].lower()
    db_name = f"SYNAPSE{user_id_2}{kb_name_2}_{where}"
    # print('db_name:', db_name)

    # if plan_id == 'plan_general_question_single':
    suc, result = multi_step_qa(key, user_query, paper_lists, where)
        # if suc:
    print("[Info] Using multi-step QA result for general question.")
    return result
        
    # if suc = False, or plan_id is not general question, we use the plan_id    
    # with open(plan_path, "r") as f:
    #     workflow = yaml.safe_load(f)
    # new_query = ','.join(paper_lists)
    # workflow["task_scope"]["query"] = new_query
    # for node in workflow.get("nodes", []):
    #     if plan_id == "plan_general_question_single":
    #         if node["id"] == "synthesize_answer":
    #             node["inputs"] = [f'retrieval_query["{user_query}"]']
    #     node["db_name"] = db_name
    # result = executor_entry(db_name, workflow)
    # return result


def our_qa_wo_plan_id(key, user_query, paper_lists, enable_execute = False, where="ms"):
    plan_id, *_ = select_plan.select_prompt_plan(user_query)
    if plan_id == 'no':
        plan_id = 'plan_general_question_single' # general question plan
    result = ""
    if enable_execute:
        result = our_qa_plan_id(key, plan_id, paper_lists, user_query, where)
    return plan_id, result


def baseline_qa(key, user_query, paper_lists):
    user_id, kb_name = get_user_and_kb_name(key)
    qa_engine = LargeContextQAEngine(user_id, kb_name, "ms")

    result = qa_engine.answer_question(user_query, paper_lists)
    result_content = "\n" + result.answer
    if result.individual_answers:
        result_content += "\n\nIndividual Answers:\n"
        for pid, ans in result.individual_answers.items():
            result_content += f"Paper: {pid}\n Answer:\n {ans}\n"
    
    return result_content

def append_jsonl(path, obj):
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")
        f.flush()

def test_main(topic: str, key: str):
    
    base_dir = PROJECT_ROOT / "src" / "test_api" / topic 
    test_queries = base_dir / f"query_{topic}.json"
    # test_queries = base_dir / "query_time_series_forecasting.json"
    with open(test_queries, "r", encoding="utf-8") as f:
        queries = json.load(f)
    
    # {"query_id": 0, "user_query": "please summarize the experiment setting", "paper_lists": ["FLAT"], "plan_id":"plan_extract_experimental_settings"},
    
    our_path      = base_dir / f"{topic}_our_results.jsonl"
    planid_path   = base_dir / f"{topic}_plan_id_estimation.jsonl"
    base_path     = base_dir / f"{topic}_baseline_results.jsonl"


    enable_our = True
    enable_base = False
    enbale_planid = False
    enable_results_in_plan = False

    for entry in queries:
        # temp
        entry = queries[181]
        query_id = entry["query_id"]
        user_query = entry["user_query"]
        paper_lists = entry["paper_lists"]
        plan_id = entry.get("plan_id", "")
        
        print(f"\n[TEST] Query ID: {query_id}, User Query: {user_query}, Paper Lists: {paper_lists}, Plan ID: {plan_id}")

        if enable_our:
            _s = time.time()
            _r = our_qa_plan_id(key, plan_id, paper_lists, user_query)
            _e = time.time()
            
            r = {'query_id': query_id, 'time': _e - _s, 'result': _r}
            # print(f"[RESULT] {r}")
            # our_results.append(r)
            # append_jsonl(our_path, r)
            
        break
        
        if enbale_planid:
            
            _s = time.time()
            _plan_id, _r = our_qa_wo_plan_id(key, user_query, paper_lists, enable_execute=enable_results_in_plan)
            _e = time.time()
            
            is_same = 0
            if _plan_id == plan_id:
                is_same = 1
            
            r = {'query_id': query_id, 'plan_id_gt': plan_id, 'plan_id_est': _plan_id, 'result': _r, 'time': _e - _s, 'is_same': is_same}
            append_jsonl(planid_path, r)
        
        if enable_base:
            _s = time.time()
            _r = baseline_qa(key, user_query, paper_lists)
            _e = time.time()
            r = {'query_id': query_id, 'time': _e - _s, 'result': _r}
            append_jsonl(base_path, r)
        
if __name__ == "__main__":
    # test_main('dataset_discovery')
    test_main('vector_search', 'TF')
    # test_main('entity_resolution')
    # test_main('recommendation')
    # parser = argparse.ArgumentParser(description="Run QA tests with a specified topic and key.")
    #
    # # 2. Add arguments for 'topic' and 'key'
    # parser.add_argument("topic", type=str, help="The topic to run tests on (e.g., 'dataset_discovery', 'vector_search').")
    # parser.add_argument("-k", "--key", type=str, required=True, help="A unique key for this test run (e.g., 'TF', 'EXP2').")
    #
    # args = parser.parse_args()
    # print(f"Running tests for topic: {args.topic} with key: {args.key}")
    #
    # test_main(args.topic, args.key)


# from src.index.weaviate_instance import WeaviateIndexer
# user_id_2 = user_id.split('-')[0].lower()
# kb_name_2 = kb_name.split('-')[0].lower()
# db_name = f"SYNAPSE{user_id_2}{kb_name_2}_ms"
# index = WeaviateIndexer(db_name=db_name) 
# index.delete_collection()
