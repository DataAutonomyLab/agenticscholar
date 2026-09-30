from enum import Enum
from typing import Any, Dict, List
from src.executor_multistep.executor.plan_step import ExecutorType, ResearchStep, StepExecutor, StepResult, try_cross_paper_experiment, try_experiment,  try_dummy
from src.prompts.base import run_structured_prompt
from src.prompts.summarizer import summarize_common_settings, summarize_methods_pros_cons, summarize_missing_settings, summarize_parameter_impact, summarize_problem_def_diff


class SummarizeType(Enum):
    COMMON_SETTINGS = {
        "name": "summarize_common_settings",
        "description": "Summarizes common datasets, metrics, and baselines across multiple papers.",
        "mode": "global",
        "handler": try_cross_paper_experiment
    }
    MISSING_SETTINGS ={
        "name": "summarize_missing_settings",
        "description": "Summarizes unique or inconsistent experimental setups across papers.",
        "mode": "global",
        "handler": try_cross_paper_experiment
    } 
    PARAMETER_IMPACT = {
        "name": "summarize_parameter_impact",
        "description": "Summarizes how parameter variations influence results across experiments.",
        "mode": "local",
        "handler": try_experiment
    }
    PROBLEM_DEF_DIFF = {
        "name": "summarize_problem_def_diff",
        "description": "Summarizes key differences in problem definitions among multiple papers.",
        "mode": "global",
        "handler": try_cross_paper_experiment
    }
    METHODS_PROS_CONS = {
        "name": "summarize_methods_pros_cons",
        "description": "Summarizes advantages and disadvantages of different methods.",
        "mode": "global",
        "handler": try_cross_paper_experiment
    }
    DEFAULT = {
        "name": "default",
        "description": "Produces a general summary focusing on the specified aspect of the provided content.",
        "mode": "local | global",
        "handler": try_dummy
    }

    @classmethod
    def from_str(cls, s: str) -> "SummarizeType | None":
        value_to_member = {member.value["name"]: member for member in cls}
        return value_to_member.get(s)
    
def summarize_content(content: str, description: str, length: str) -> str:
    return run_structured_prompt(
        template_name = "summarize_content.yaml",
        variables= {
            "content": content,
            "summary_focus": description,
            "summary_length": length
        },
        is_reserch=True
    )

class SummarizeStepExecutor(StepExecutor):
    """Executor for summarization steps"""
    
    summarize_type: SummarizeType

    def __init__(self, db_name: str, step: ResearchStep, target_paper: str):
        super().__init__(db_name, step, target_paper)
        self.executor_type = ExecutorType.SUMMARIZE
        type_str = step.handler_type if step.handler_type is not None else "default"
        self.summarize_type = SummarizeType.from_str(type_str)
        if self.summarize_type is None:
            print(f"No SummarizeStepExecutor registered for type {type_str}, fallback to default") 
            self.summarize_type = SummarizeType.DEFAULT

    def execute(self, context: Dict[str, Any]) -> StepResult:
        inputs = self.get_inputs(context)
        if self.summarize_type == SummarizeType.DEFAULT:
            # content = self.get_content(context)
            result = summarize_content(str(inputs), 
                                        self.step.description, 
                                        self.step.parameters.get('length', 'medium'))
        else:
            result = self.execute_internal(inputs)

        return StepResult(
            step_id=self.step.id,
            success=True,
            result=result
        )
            
    def execute_internal(self, inputs: List) -> str:
        map_func = {
            SummarizeType.COMMON_SETTINGS: summarize_common_settings,
            SummarizeType.MISSING_SETTINGS: summarize_missing_settings,
            SummarizeType.PARAMETER_IMPACT: summarize_parameter_impact,
            SummarizeType.PROBLEM_DEF_DIFF: summarize_problem_def_diff,
            SummarizeType.METHODS_PROS_CONS: summarize_methods_pros_cons,
        }
        handler = map_func[self.summarize_type]
        return handler(*inputs)

    # def get_content(self, context: Dict[str, Any]):
    #     # Get content either from retrieval or previous steps
    #     if self.step.dependencies:
    #         # Use results from previous steps
    #         content_parts = []
    #         for dep_id in self.step.dependencies:
    #             if dep_id in context:
    #                 content_parts.append(str(context[dep_id]))
    #         combined_content = "\n\n".join(content_parts)
    #     else:
    #         # Retrieve from sections
    #         content = self.retrieve_sections(
    #             self.step.target_papers, 
    #             self.step.target_sections
    #         )
    #         combined_content = "\n".join(content)
    #     return combined_content