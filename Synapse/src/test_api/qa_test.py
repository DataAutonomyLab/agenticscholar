import csv
import json
import time
from typing import Dict, List
from src.executor_multistep.executor.plan_step import ResearchJSONEncoder, ResearchPlan, ResearchStep, StepType, research_object_hook
from src.executor_multistep.multi_step_engine import ExecutionPlanBuilder, MultiStepResearchEngine
from src.executor_multistep.multi_step_optimizer import ResearchPlanCorrector, ResearchPlanGenerator, ResearchPlanInstantiation
from src.index.weaviate_instance import WeaviateIndexer, WeaviateIndexer4PlanSelection, close_client, get_embedder
from src.prompts.base import run_structured_prompt
from src.routing import select_plan
from src.routing.select_plan import PREDEFINED_PLANS_DB
from src.synapse_utils import DATA_DIR, get_plan_path, get_routing_path


def get_user_and_kb_name(key: str):
    user_id = f"test{key}-user"
    kb_name = f"test{key}-kb"
    return user_id, kb_name

def load_paper_entry(topic: str, key: str, where: str="ms"):

    base_dir = DATA_DIR / "db" / "paper_data"

    user_id, kb_name = get_user_and_kb_name(key)
    user_id_2 = user_id.split('-')[0].lower()
    kb_name_2 = kb_name.split('-')[0].lower()
    db_name = f"SYNAPSE{user_id_2}{kb_name_2}_{where}"
    print('db_name:', db_name)  
    indexer = WeaviateIndexer(db_name=db_name)
    target_dir = (
        base_dir /
        user_id /
        kb_name /
        where
    )
    for item in target_dir.iterdir():
        paper_name = item.name

        # Load sections into Weaviate index
        json_path = (
            target_dir /
            paper_name /
            f"{paper_name}_structured.json"
        )
        with open(json_path, "r", encoding="utf-8") as f:
            sections = json.load(f)
        print(f"Loading {len(sections)} sections from {json_path}")
        indexer.add_section_to_index(sections)

def load_predefined_plan_entry(topic: str, key: str):
    db_name = PREDEFINED_PLANS_DB
    print('db_name:', db_name)  
    index = WeaviateIndexer4PlanSelection(db_name=db_name)

    with open(get_routing_path() / "name2description.json", 'r', encoding='utf-8') as f:
        name2description = json.load(f)

    with open(get_routing_path() / "name2plan.json", 'r', encoding='utf-8') as f:
        name2plan = json.load(f)

    with open(get_routing_path() / "name2stepdesc.json", 'r', encoding='utf-8') as f:
        name2stepdesc = json.load(f)
    index.add_predefined_plan_description_to_index(name2description, name2plan, name2stepdesc)

def load_main(topic: str, key: str):
    # load_paper_entry(topic, key)
    load_predefined_plan_entry(topic, key)
    
def test_main(topic: str, key: str, disable_predefined_plan: bool = False, enable_execution: bool = True, enable_one_stage_plan_generation: bool = False, enable_execution_graph: bool = True):
    user_id, kb_name = get_user_and_kb_name(key)
    user_id_2 = user_id.split('-')[0].lower()
    kb_name_2 = kb_name.split('-')[0].lower()
    db_name = f"SYNAPSE{user_id_2}{kb_name_2}_ms"

    base_dir = DATA_DIR / "db" / "paper_data" / user_id 
    result_dir = DATA_DIR / "db" / "result_data" / user_id
    test_queries = base_dir / f"query_{topic}.json"

    embedder = get_embedder()
    vector = embedder.encode("Loading Embedder Model", convert_to_tensor=True).tolist()
    with open(test_queries, "r", encoding="utf-8") as f:
        queries = json.load(f)

    stats_list = []
    total_queries = len(queries)
    failed_queries = []
    for entry in queries:
        try:
            query_id = entry["query_id"]
            user_query = entry["user_query"]
            paper_lists = entry["paper_lists"]
            plan_id = entry.get("plan_id", "")
            
            print(f"\n[TEST] Query ID: {query_id}, User Query: {user_query}, Paper Lists: {paper_lists}, Plan ID: {plan_id}")
            
            query_result_dir = result_dir / str(query_id)
            query_result_dir.mkdir(parents=True, exist_ok=True)

            t0 = time.perf_counter()
            
            # select predefined_plan
            plan_id, plan_desc, select_plan_token_stat = select_plan.select_prompt_plan(user_query)
            print("[INFO]select_prompt_plan completed")
            t1 = time.perf_counter()

            # generate physical plan
            if disable_predefined_plan or plan_id == 'plan_general_question_single':
                if enable_one_stage_plan_generation:
                    research_plan = generate_full_plan(query_id, user_query, paper_lists, plan_desc)
                    t2 = time.perf_counter()
                    print("[INFO]generate_full_plan completed")
                    research_plan.visualize(query_result_dir / "physical_plan.dot")
                else:
                    # generate logical plan
                    research_plan = auto_generate_plan(query_id, user_query, paper_lists, plan_desc)
                    t2 = time.perf_counter()
                    print("[INFO]auto_generate_plan completed")
                    research_plan.visualize(query_result_dir / "logical_plan.dot")
                    # instantiate each operator
                    plan_instantiation = ResearchPlanInstantiation()
                    plan_instantiation.instantiate_plan(research_plan)
                    print("[INFO]instantiate_plan completed")
            else:
                # load predefined physical plan from yaml
                research_plan = load_predefined_plan(query_id, user_query, paper_lists, plan_id)
                t2 = time.perf_counter()
                print("[INFO]load_predefined_plan completed")
            research_plan_json = json.dumps(research_plan, cls=ResearchJSONEncoder, indent=2)

            t3 = time.perf_counter()
            research_plan.visualize(query_result_dir / "physical_plan.dot")
            
            print(research_plan_json)

            # build execution graph
            if enable_execution_graph:
                execution_plan_builder = ExecutionPlanBuilder(db_name)
                execution_graph = execution_plan_builder.build_execution_graph(research_plan)
                execution_graph.visualize(query_result_dir / "execution_graph.dot")
            print("[INFO]build_execution_graph completed")
            t4 = time.perf_counter()

            # execute graph
            execution_result = {}
            if enable_execution:
                research_engine = MultiStepResearchEngine()
                execution_result = research_engine.execute_plan(execution_graph)
                execution_graph.visualize_analyzed(execution_result["results"], query_result_dir / "execution_analyzed_graph.dot")
                print("[INFO]Multi-step research completed:")
                print(execution_result["final_synthesis"])

            t5 = time.perf_counter()
            instantiate_input_tokens = 0
            instantiate_output_tokens = 0
            execution_input_tokens = 0
            execution_output_tokens = 0

            for step in research_plan.steps:
                instantiate_input_tokens += step.statistics.get('input_tokens', 0)
                instantiate_output_tokens += step.statistics.get('output_tokens', 0)

            if enable_execution_graph:
                for node in execution_graph.nodes.values():
                    execution_input_tokens += node.metadata.get('input_tokens', 0)
                    execution_output_tokens += node.metadata.get('output_tokens', 0)

            stats = {
                "query_id": query_id,
                "total_time": t5-t0,
                "select_predefined_plan_time": t1-t0,
                "generate_plan_time": t2-t1,
                "instantiate_plan_time": t3-t2,
                "build_execution_graph_time": t4-t3,
                "execution_time": t5-t4,
                "input_tokens": select_plan_token_stat["input_tokens"] + research_plan.metadata.get("input_tokens", 0) + instantiate_input_tokens + execution_input_tokens,
                "output_tokens": select_plan_token_stat["output_tokens"] + research_plan.metadata.get("output_tokens", 0) + instantiate_output_tokens + execution_output_tokens,
                "result": execution_result.get("final_synthesis", ""),
                "research_plan": research_plan_json
            }
            stats_list.append(stats)
        
            # output into JSONL
            jsonl_path = result_dir / "query_stats.jsonl"
            with open(jsonl_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(stats, ensure_ascii=False) + "\n")

            
            # output into CSV
            csv_path = result_dir / "query_stats.csv"
            file_exists = csv_path.exists()
            with open(csv_path, "a", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=list(stats.keys()))
                if not file_exists:
                    writer.writeheader()
                writer.writerow(stats)
        except Exception as e:
            print(f"[Error] {query_id}: {e}")
            failed_queries.append(query_id)

    print(f"failure ratio: {len(failed_queries)}/{total_queries}; failed queries: {failed_queries}")

    close_client()

def auto_generate_plan(query_id: str, user_query: str, paper_list: List[str], plan_desc_shot: str) -> ResearchPlan:
    plan_generator = ResearchPlanGenerator()
    research_plan = plan_generator.generate_plan(user_query, paper_list, query_id=query_id, plan_desc_shot=plan_desc_shot)
    return research_plan

def generate_full_plan(query_id: str, query: str, paper_ids: List[str], plan_desc_shot: str) -> ResearchPlan:
    # Use LLM to analyze query and determine if multi-step is needed
    result1 = run_structured_prompt(
        template_name = "analyze_query_complexity.yaml",
        variables={
            "query": query,
            "paper_scope": paper_ids
        },
        is_reserch=True,
        str_type="JSON_T"
    )
    analysis_result = result1["response"]
    # if not analysis_result.get("requires_multi_step", False):
    #     return None  # Use regular single-step processing
    
    # Generate step-by-step plan
    result2 = run_structured_prompt(
        template_name="generate_full_plan.yaml",
        variables={
            "query": query,
            "paper_scope": paper_ids,
            "complexity_analysis": analysis_result,
            "plan_shot": plan_desc_shot if plan_desc_shot else ""
        },
        is_reserch=True,
        str_type="JSON_T"
    )
    plan_data = result2["response"]
    # Convert to ResearchPlan object
    steps = []
    
    for step_data in plan_data.get("steps", []):

        if step_data["type"] == "identify" or step_data["type"] == "categorize":
            step_data["type"] = "summarize"
        if step_data["type"] == "compare":
            step_data["type"] = "check"
        step = ResearchStep(
            id=step_data["id"],
            step_type=StepType(step_data["type"]),
            description=step_data["description"],
            target_sections=step_data.get("target_sections", []),
            target_papers=paper_ids,
            dependencies=step_data.get("dependencies", []),
            parameters=step_data.get("parameters", {}),
            mode=step_data.get("mode", "local"),
            handler_type=step_data.get("handler_type", "default")
        )

        if step.step_type == StepType.SEARCH:
            step.parameters["query"] = query
            #TODO: how to determine user_id and kb_id
            step.parameters["user_id"] = "user_id"
            step.parameters["kb_id"] = "kb_id"

        steps.append(step)

    metadata = plan_data.get("metadata", {})
    metadata["input_tokens"] = result1["input_tokens"] + result2["input_tokens"]
    metadata["output_tokens"] = result1["output_tokens"] + result2["output_tokens"]
    return ResearchPlan(
        id=str(uuid.uuid4()) if query_id is None else query_id,
        query=query,
        steps=steps,
        paper_scope=paper_ids,
        metadata=metadata
    )

def load_predefined_plan(query_id: str, user_query: str, paper_list: List[str], plan_id: str) -> ResearchPlan:
    plan_path = get_plan_path() / f"{plan_id}.yaml"

    research_plan = ResearchPlan(query_id, user_query, paper_scope=paper_list)
    research_plan.deserialize(plan_path)

    return research_plan
def specific_self_correction_test(max_correction_times: int = 5):
    query = "From the set of papers that study graph-based methods on hybrid vector search problem problem, identify the two best-performing methods on the SIFT1M dataset in terms of metric QPS. What specific algorithmic differences between these two methods most likely explain the performance gap."
    steps = [
        {
            "id": "step_1",
            "step_type": "retrieve",
            "description": "Retrieve the 'Experiment' sections from each paper in the scope to gather experimental results and performance data.",
            "handler_type": "default",
            "target_sections": ["Experiment"],
            "dependencies": [],
            "mode": "local"
         },{
             "id": "step_2",
             "step_type": "extract",
             "description": "Extract QPS performance metrics and relevant experimental details from the retrieved sections.",
             "handler_type": "extract_exp_settings_metrics",
             "target_sections": ["Experiment"],
             "dependencies": ["step_1"],
             "mode": "local"
        },{
            "id": "step_3",
            "step_type": "extract",
            "description": "Extract algorithmic details, architectures, and key features of each method from their respective 'Method' or relevant sections.",
            "handler_type": "extract_exp_settings",
            "target_sections": ["Method"],
            "dependencies": ["step_1"],
            "mode": "local"
        },{
            "id": "step_4",
            "step_type": "rank",
            "description": "Rank the methods based on their QPS performance on SIFT1M to identify the top two performing methods.",
            "handler_type": "rank_datasets",
            "target_sections": ["Experiment"],
            "dependencies": ["step_2"],
            "mode": "global"
        },{
            "id": "step_5",
            "step_type": "synthesize",
            "description": "Compare the algorithmic differences between the top two methods to identify key factors explaining the performance gap.",
            "handler_type": "synthesize_final_answer",
            "target_sections": ["Method"],
            "dependencies": ["step_3", "step_4"],
            "mode": "global"
        },{
            "id": "step_6",
            "step_type": "summarize",
            "description": "Summarize the findings, including the top-performing methods, their algorithmic differences, and the most likely reasons for the performance gap.",
            "handler_type": "summarize_methods_pros_cons",
            "target_sections": ["Experiment", "Method"],
            "dependencies": ["step_4", "step_5"],
            "mode": "global"
        }
    ]
    correction_times = 0
    need_correction = True
    while need_correction and correction_times < max_correction_times:
        result1 = run_structured_prompt(
            template_name = "error_detection.yaml",
            variables={
                "query": query,
                "research_plan": steps
            },
            is_reserch=True,
            str_type="JSON_T",
            LLM_Type="QueryDecomposition"
        )
        print(f"specific: {result1}")
        need_correction = result1["response"]["status"]
        if not need_correction:
            continue
        result2 = run_structured_prompt(
            template_name = "self_correction.yaml",
            variables={
                "query": query,
                "research_plan": steps,
                "issue_analysis": result1["response"]["info"]
            },
            is_reserch=True,
            str_type="JSON_T",
            LLM_Type="QueryDecomposition"
        )
        steps = result2["response"]["corrected_research_plan"]
        correction_times += 1
        print(f"correction_times_{correction_times}: steps")

    if correction_times > 0:
        visualize(steps, "specific.dot")

def self_correction_test(key: str, max_correction_times = 5):

    user_id, kb_name = get_user_and_kb_name(key)
    user_id_2 = user_id.split('-')[0].lower()
    kb_name_2 = kb_name.split('-')[0].lower()

    result_dir = DATA_DIR / "db" / "result_data" / user_id 
    
    file_path = result_dir / "query_stats.jsonl"

    data_array = []

    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                json_obj = json.loads(line.strip())
                data_array.append(json_obj)
            except json.JSONDecodeError as e:
                print(f"fail to parse JSON, content: {line.strip()}, error: {e}")
    for data in data_array:
        research_plan: ResearchPlan = json.loads(data["research_plan"], object_hook=research_object_hook)
        correction_times = 0
        need_correction = True
        steps = []
        for step in research_plan.steps:
            steps.append({
                        "id": step["id"],
                        "step_type": step["step_type"],
                        "description":step["description"],
                        "handler_type": step["handler_type"],
                        "target_sections": step["target_sections"],
                        "dependencies": step["dependencies"],
                        "mode": step["mode"]
            })
        while need_correction and correction_times < max_correction_times:
            result1 = run_structured_prompt(
                template_name = "error_detection.yaml",
                variables={
                    "query": research_plan.query,
                    "research_plan": steps
                },
                is_reserch=True,
                str_type="JSON_T"
                # LLM_Type="QueryDecomposition"
            )
            print(f"{research_plan.id}: {result1}")
            need_correction = result1["response"]["status"]
            if not need_correction:
                continue
            result2 = run_structured_prompt(
                template_name = "self_correction.yaml",
                variables={
                    "query": research_plan.query,
                    "research_plan": steps,
                    "issue_analysis": result1["response"]["info"]
                },
                is_reserch=True,
                str_type="JSON_T"
                # LLM_Type="QueryDecomposition"
            )
            steps = result2["response"]["corrected_research_plan"]
            correction_times += 1
            print(f"correction_times_{correction_times}: steps")

        if correction_times > 0:
            query_result_dir = result_dir / str(research_plan.id)
            visualize(steps, query_result_dir / f"physical_plan_correction_{correction_times}.dot")


def visualize(steps: List[Dict], filename: str):
    with open(filename, "w") as f:
        f.write("digraph ResearchPlan {\n")
        f.write("  node [shape=box, style=rounded, fontsize=10];\n\n")

        for step in steps:
            label_lines = [
                f"ID: {step["id"]}",
                f"Type: {step["step_type"]}",
                f"Handler: {step["handler_type"] or 'N/A'}",
                f"Mode: {step["mode"] or 'N/A'}",
                f"Sections: {','.join(step["target_sections"]) if step["target_sections"] else 'None'}",
                f"Inputs: {','.join(step["dependencies"]) if step["dependencies"] else 'None'}",
                f"Description: {step["description"] if step["description"] else 'None'}"
            ]
            label = "\\n".join(label_lines)
            f.write(f'  "{step["id"]}" [label="{label}"];\n')

        f.write("\n")

        for step in steps:
            for dep in step["dependencies"]:
                f.write(f'  "{dep}" -> "{step["id"]}";\n')

        f.write("}\n")
if __name__ == "__main__":
    # load_main('vector_search', 'VS')

    # Ablation Study 1: whether or not to select predefined plan

    # test_main('vector_search', 'VS', disable_predefined_plan=False, enable_execution=False, enable_one_stage_plan_generation=False)
    # test_main('vector_search', 'VS', disable_predefined_plan=True, enable_execution=False, enable_one_stage_plan_generation=False)
    
    # Ablation Study 2: whether or not to use one stage plan generation
    
    # test_main('vector_search', 'VS', disable_predefined_plan=True, enable_execution=False, enable_one_stage_plan_generation=True)

    # Complex Query Generation Study:

    # test_main('vector_search', 'VS', disable_predefined_plan=True, enable_execution=False, enable_one_stage_plan_generation=False, enable_execution_graph=False)
    
    # test_main('vector_search', 'VS', disable_predefined_plan=True, enable_execution=False, enable_one_stage_plan_generation=True, enable_execution_graph=False)

    # Self Correction Test

    # self_correction_test('VS')
    # specific_self_correction_test()