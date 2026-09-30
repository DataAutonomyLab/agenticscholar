from typing import Any, Dict
from src.executor_multistep.executor.plan_step import ExecutorType, ResearchStep, StepExecutor, StepResult
from src.prompts.base import run_structured_prompt


class FilterStepExecutor(StepExecutor):
    """
    Executor for take a list of entities and 
    return a subset that satisfies a specific, logical criterion.
    """
    
    def __init__(self, db_name: str, step: ResearchStep, target_paper: str):
        super().__init__(db_name, step, target_paper)
        self.executor_type = ExecutorType.FILTER

    def execute(self, context: Dict[str, Any]) -> StepResult:
        print("not yet finish!")
        # Retrieve relevant sections
        content_list = self.get_inputs(context)
        result = self.execute_internal(content_list, 
                                        self.step.description)
        
        return StepResult(
            step_id=self.step.id,
            success=True,
            result=result
        )
        
    def execute_internal(self, content_list: list, filter_instruction: str) -> str:
        result = run_structured_prompt(
            template_name =  "",
            variables= {
                # "extraction_query": description,
                # "content": content,
                # "format_instructions": format_instruction
            },
            is_reserch=True
        )
        return result
