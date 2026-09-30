from enum import Enum
from typing import Any, Dict, List
from src.executor_multistep.executor.plan_step import ExecutorType, ResearchStep, StepExecutor, StepResult
from src.prompts.base import run_structured_prompt
from src.prompts.summarizer import check_inconsistencies_cross_papers, check_inconsistencies_metrics
from src.executor_multistep.executor.summarize_step_executor import SummarizeType
from src.executor_multistep.executor.extract_step_executor import ExtractType
from src.executor_multistep.executor.plan_step import try_experiment, try_certain_prev_node, try_dummy, try_cross_paper_experiment



def try_check_inconsistency_cross_papers(step_map: Dict[str, ResearchStep], step: ResearchStep)-> bool:
    return try_cross_paper_experiment(step_map, step) and try_certain_prev_node(SummarizeType.COMMON_SETTINGS, step_map, step) and try_certain_prev_node(ExtractType.EXP_COMP_BASELINES, step_map, step) and try_certain_prev_node(ExtractType.EXP_SETTINGS, step_map, step)

class CheckType(Enum):
    INCONSISTENCIES_METRICS = {
        "name": "check_inconsistencies_metrics",
        "description": "Checks for discrepancies between reported metrics and their definitions.",
        "mode": "local",
        "handler": try_experiment # TODO: change the name of handler and try_
    }
    INCONSISTENCIES_CROSS_PAPERS = {
        "name": "check_inconsistencies_cross_papers",
        "description": "Checks for inconsistencies in experimental results across multiple papers.",
        "mode": "global",
        "handler": try_check_inconsistency_cross_papers,
        "input_hint": "it need three step inputs as follows:\
            1. A extract step with handler_type:extract_exp_settings\
            2. A summarize step with handler_type:summarize_common_settings \
            3. A extract step with handler_type:extract_comp_baselines \
        "
    }
    DEFAULT = {
        "name": "default",
        "description": "Compares information across papers based on specified focus or criteria.",
        "mode": "global",
        "handler": try_dummy
    }
    @classmethod
    def from_str(cls, s: str) -> "CheckType | None":
        value_to_member = {member.value["name"]: member for member in cls}
        return value_to_member.get(s)

def compare_content(content: str, description: str, criteria: str) -> str:
    return run_structured_prompt(
        template_name = "compare_content.yaml",
        variables= {
            "comparison_items": content,
            "comparison_focus": description,
            "comparison_criteria": criteria
        },
        is_reserch=True
    )

class CheckStepExecutor(StepExecutor):
    """
    Executor for compare information across multiple peer documents to identify
    and report on disagreements or inconsistencies
    """

    check_type: CheckType

    def __init__(self, db_name: str, step: ResearchStep, target_paper: str):
        super().__init__(db_name, step, target_paper)
        self.executor_type = ExecutorType.CHECK
        type_str = step.handler_type if step.handler_type is not None else "default"
        self.check_type = CheckType.from_str(type_str)
        if self.check_type is None:
            raise ValueError(f"No CheckStepExecutor registered for type {type_str}") 
        
    def execute(self, context: Dict[str, Any]) -> StepResult:
        inputs = self.get_inputs(context)
        if self.check_type == CheckType.DEFAULT:
            # comparison_items = self.get_content(context)
            result = compare_content(str(inputs),
                                        self.step.description,
                                        self.step.parameters.get('criteria', 'comprehensive'))
        else:
            result = self.execute_internal(inputs)

        return StepResult(
            step_id=self.step.id,
            success=True,
            result=result,
            metadata={"items_compared": len(inputs)}
        )
    
    def execute_internal(self, inputs: List) -> str:
        map_func = {
            CheckType.INCONSISTENCIES_CROSS_PAPERS: check_inconsistencies_cross_papers,
            CheckType.INCONSISTENCIES_METRICS: check_inconsistencies_metrics,
        }
        handler = map_func[self.check_type]
        return handler(*inputs)