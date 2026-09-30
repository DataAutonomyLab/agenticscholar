from typing import Any, Dict
from src.executor_multistep.executor.plan_step import ExecutorType, ResearchStep, StepExecutor, StepResult
from src.prompts.base import run_structured_prompt


class FindNodeStepExecutor(StepExecutor):
    """Executor for aggregate steps"""

    def __init__(self, db_name: str, step: ResearchStep, target_paper: str):
        super().__init__(db_name, step, target_paper)
        self.executor_type = ExecutorType.FINDNODE

    def execute(self, context: Dict[str, Any]) -> StepResult:
        print("not yet finish!")