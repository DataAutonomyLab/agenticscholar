from enum import Enum
from typing import Any, Dict, List
from src.executor_multistep.executor.plan_step import ExecutorType, ResearchStep, StepExecutor, StepResult
from src.prompts.summarizer import rank_datasets, rank_exp_results_cross_papers, rank_variants
from src.executor_multistep.executor.summarize_step_executor import SummarizeType
from src.executor_multistep.executor.extract_step_executor import ExtractType
from src.executor_multistep.executor.plan_step import try_cross_paper_experiment, try_certain_prev_node, try_experiment

def try_rank_exp_results_cross_papers(step_map: Dict[str, ResearchStep], step: ResearchStep)-> bool:
    return try_cross_paper_experiment(step_map, step) and try_certain_prev_node(SummarizeType.COMMON_SETTINGS, step_map, step) and try_certain_prev_node(ExtractType.EXP_COMP_BASELINES, step_map, step) and try_certain_prev_node(ExtractType.EXP_SETTINGS, step_map, step)

class RankType(Enum):
    DATASETS = {
        "name": "rank_datasets",
        "description": "ranking datasets used in the proposed method based on experimental results.",
        "mode": "global",
        "handler": try_cross_paper_experiment
    }
    VARIANTS = {
        "name": "default", # rank_variants
        "description": "ranking variants of the proposed method based on experimental results.",
        "mode": "local",
        "handler": try_experiment
    }
    EXP_RESULTS = {
        "name": "rank_exp_results_cross_papers",
        "description": "ranking experiment results of different methods on a common dataset and a common evaluation metric.",
        "mode": "global",
        "handler": try_rank_exp_results_cross_papers,
        "input_hint": "it need three step inputs as follows:\
            1. A extract step with handler_type:extract_exp_settings\
            2. A summarize step with handler_type:summarize_common_settings \
            3. A extract step with handler_type:extract_comp_baselines \
        "
    }

    @classmethod
    def from_str(cls, s: str) -> "RankType | None":
        value_to_member = {member.value["name"]: member for member in cls}
        return value_to_member.get(s)

def rank_default(content) -> str:
    print("rank default")
    return None

class RankStepExecutor(StepExecutor):
    """Executor for rank steps"""

    rank_type: RankType

    def __init__(self, db_name: str, step: ResearchStep, target_paper: str):
        super().__init__(db_name, step, target_paper)
        
        self.executor_type = ExecutorType.RANK
        type_str = step.handler_type if step.handler_type is not None else "default"
        self.rank_type = RankType.from_str(type_str)
        if self.rank_type is None:
            raise ValueError(f"No RankStepExecutor registered for type {type_str}")

    def execute(self, context: Dict[str, Any]) -> StepResult:
        # Retrieve relevant sections
        inputs = self.get_inputs(context)
        result = self.execute_internal(inputs)
        return StepResult(
            step_id=self.step.id,
            success=True,
            result=result
        )
    
    def execute_internal(self, inputs: List) -> str:
        map_func = {
            RankType.DATASETS: rank_datasets,
            RankType.VARIANTS: rank_variants,
            RankType.EXP_RESULTS: rank_exp_results_cross_papers,
            RankType.DEFAULT: rank_default,
        }
        handler = map_func[self.rank_type]
        return handler(*inputs)