from collections import deque
from enum import Enum
from typing import Dict, List, Optional
import uuid
from src.executor_multistep.executor.check_step_executor import CheckType
from src.executor_multistep.executor.extract_step_executor import ExtractType
from src.executor_multistep.executor.plan_step import ResearchPlan, ResearchStep, StepType
from src.executor_multistep.executor.rank_step_executor import RankType
from src.executor_multistep.executor.summarize_step_executor import SummarizeType
from src.executor_multistep.executor.synthesize_step_executor import SynthesizeType
from src.executor_multistep.executor.verify_step_executor import VerifyType
from src.prompts.base import run_structured_prompt
import concurrent.futures

STEP_TYPE_MAP = {
    StepType.EXTRACT: {
        "prompt_template": "instantiate_research_step.yaml",
        "handler_enum": ExtractType
    },
    StepType.SUMMARIZE: {
        "prompt_template": "instantiate_research_step.yaml",
        "handler_enum": SummarizeType
    },
    StepType.CHECK: {
        "prompt_template": "instantiate_research_step.yaml",
        "handler_enum": CheckType
    },
    StepType.RANK: {
        "prompt_template": "instantiate_research_step.yaml",
        "handler_enum": RankType
    },
    StepType.SYNTHESIZE: {
        "prompt_template": "instantiate_research_step.yaml",
        "handler_enum": SynthesizeType
    },
    StepType.VERIFY: {
        "prompt_template": "instantiate_research_step.yaml",
        "handler_enum": VerifyType
    }
}


class ResearchPlanGenerator:
    """Generates research steps from user queries"""
    
    def __init__(self):
        pass
    
    def generate_plan(self, query: str, paper_ids: List[str], query_id: Optional[str] = None, plan_desc_shot: Optional[str] = None) -> Optional[ResearchPlan]:
        """Generate a research plan for a complex query"""
        
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
        print(f"analysis_result: {analysis_result}")
        # Generate step-by-step plan
        result2 = run_structured_prompt(
            template_name="generate_research_plan.yaml",
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
            if step_data["type"] not in ["retrieve", "extract", "summarize", "rank", "check", "verify", "synthesize"]:
                print(f"{query_id} error type:{step_data["type"]}")
            if step_data["type"] == "identify" or step_data["type"] == "categorize" or step_data["type"] == "compile" or step_data["type"] == "standardize" or step_data["type"] == "normalize" or step_data["type"] == "organize":
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
                parameters=step_data.get("parameters", {})
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
  
class PlannerInfo:

    step_map: Dict[str, ResearchStep]
    research_plan: ResearchPlan

    def __init__(self, research_plan: ResearchPlan):
        self.step_map = {step.id: step for step in research_plan.steps}
        self.research_plan = research_plan

class ResearchPlanInstantiation:
    """Instantiate research steps from user queries"""
    
    def __init__(self, max_workers: int =  5):
        self.max_workers = max_workers
    
    def instantiate_plan(self, research_plan: ResearchPlan):
        """Instantiate a research plan for a complex query"""
        if research_plan is None:
            return
        
        planner_info = PlannerInfo(research_plan)
        step_indegree = {step.id: len(step.dependencies) for step in research_plan.steps}
        ready_queue = deque([sid for sid, deg in step_indegree.items() if deg == 0])

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as optimizer:
            futures: Dict[concurrent.futures.Future, str] = {}

            while ready_queue or futures:
                while ready_queue: # submit all zero in-degree node task
                    step_id = ready_queue.popleft()
                    fut = optimizer.submit(self.instantiate_internal, planner_info, step_id)  
                    futures[fut] = step_id
                    print(f"[Instantiate] Submitted {step_id}")

                # wait
                done, _ = concurrent.futures.wait(futures.keys(), return_when=concurrent.futures.FIRST_COMPLETED)

                # handle finished optimize
                for fut in done:
                    step_id = futures.pop(fut)
                    try:
                        res = fut.result()
                        # results[node_id] = res
                        
                    except Exception as e:
                        print(f"[ERROR] {step_id}: {e}")

                    # decrease successors' in-degrees
                    for step in research_plan.steps:
                        succ = False
                        for dep in step.dependencies:
                            if dep == step_id:
                                succ = True
                                break
                        if not succ:
                            continue
                        step_indegree[step.id] -= 1
                        if step_indegree[step.id] == 0:
                            ready_queue.append(step.id)

    def instantiate_internal(self, planner_info: PlannerInfo, step_id: str):

        query = planner_info.research_plan.query
        step = planner_info.step_map[step_id]
        if step.step_type not in STEP_TYPE_MAP.keys():
            step.mode = "local"
            step.handler_type = "default"
            step.inputs = step.dependencies
            return
        
        usable_type_list = self.collect_usable_type(planner_info.step_map, step)
        if len(usable_type_list) == 0:
            step.mode = self.choose_mode_type(planner_info, "local", step)
            step.handler_type = "default"
            step.inputs = step.dependencies
            return
        elif len(usable_type_list) == 1:
            step.handler_type = usable_type_list[0]["name"]
            
            step.mode = self.choose_mode_type(planner_info, usable_type_list[0]["mode"], step)
            step.inputs = step.dependencies if len(step.dependencies) > 0 else []
            return

        result = run_structured_prompt(
            template_name=STEP_TYPE_MAP[step.step_type]["prompt_template"],
            variables={
                "query": query,
                "current_step_info": step,
                "type_scope": usable_type_list,
                "prev_step_info": self.collect_prev_step_info(planner_info, step)
            },
            is_reserch=True,
            str_type="JSON_T"
        )
        chosen_operator = result["response"]

        step.handler_type = chosen_operator["name"]
        step.mode = self.choose_mode_type(planner_info, chosen_operator["mode"], step)
        step.inputs = chosen_operator["inputs"]
        if isinstance(step.inputs, str):
            step.inputs = [step.inputs]

        step.statistics["input_tokens"] = result["input_tokens"]
        step.statistics["output_tokens"] = result["output_tokens"]
        print(f"[DONE] {step_id}, choose operator:{chosen_operator}")

    def collect_prev_step_info(self, planner_info: PlannerInfo, step: ResearchStep)->List[ResearchStep]:
        prev_step_list = []
        for prev_step_id in step.dependencies:
            prev_step = planner_info.step_map[prev_step_id]
            prev_step_list.append(prev_step)
        return prev_step_list


    def collect_usable_type(self, step_map: Dict[str, ResearchStep], step: ResearchStep) -> List[Dict]:
        usable_list = []
        enum_type: Enum = STEP_TYPE_MAP[step.step_type]["handler_enum"]
        for member in enum_type:
            try_func: function = member.value["handler"]
            if not try_func(step_map, step):
                continue

            item = {
                "name": member.value["name"],
                "description": member.value["description"],
                "mode": member.value["mode"],
            }

            if "input_hint" in member.value:
                item["input_hint"] = member.value["input_hint"]

            usable_list.append(item)
        
        return usable_list
    def choose_mode_type(self, planner_info: PlannerInfo, input_mode: str, step: ResearchStep) -> str:
        exist_global_depency_node = False
        for prev_step_id in step.dependencies:
            prev_step = planner_info.step_map[prev_step_id]
            if prev_step.mode == "global":
                exist_global_depency_node = True
                break
        
        if exist_global_depency_node:
            return "global"
        else:
            if input_mode != "local | global":
                return input_mode
            else:
                return "local"

class ResearchPlanCorrector:
    """Validation research steps from user queries"""
    
    def __init__(self):
        pass

    def error_detect(self, research_plan: ResearchPlan):
        # {
        #     "error":,
        #     "info":{
        #         "StepTypeError": [],
        #         "StepDescriptionError": [],
        #         "StepOutputError": [],
        #         "StepModeError": [],
        #         "StepOrderError": []
        #     }
        # }
        # self.detect_type_error(self, research_plan)
        # self.detect_mode_error(self, research_plan)
        result1 = run_structured_prompt(
            template_name = "self_correction.yaml",
            variables={
                "research_plan": research_plan
            },
            is_reserch=True,
            str_type="JSON_T"
        )
        return result1
    
    # def detect_type_error(self, research_plan: ResearchPlan):
    #     for step in research_plan.steps:
    #         if step.step_type