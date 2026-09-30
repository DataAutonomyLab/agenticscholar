from typing import Any, Dict
from src.executor_multistep.executor.plan_step import ExecutorType, ResearchStep, StepExecutor, StepResult
from src.prompts.base import run_structured_prompt
#### TODO: delete
def analyze_content(content: str, analysis_type: str, description: str, depth: str) -> str:
    return run_structured_prompt(
        template_name = "analyze_content.yaml",
        variables={
            "content": content,
            "analysis_type": analysis_type,
            "analysis_focus": description,
            "depth": depth
        },
        is_reserch=True
    )

class AnalyzeStepExecutor(StepExecutor):
    """Executor for analysis steps"""

    def __init__(self, db_name: str, step: ResearchStep, target_paper: str):
        super().__init__(db_name, step, target_paper)
        self.executor_type = ExecutorType.ANALYZE

    def execute(self, context: Dict[str, Any]) -> StepResult:
        analysis_content = self.get_content(context)
        result = analyze_content(analysis_content, 
                                self.step.parameters.get('analysis_type', 'general'), 
                                self.step.description, 
                                self.step.parameters.get('depth', 'moderate'))
        return StepResult(
            step_id=self.step.id,
            success=True,
            result=result
        )
            
    def get_content(self, context: Dict[str, Any]):
        # Get content for analysis
        if self.step.dependencies:
            content_parts = []
            for dep_id in self.step.dependencies:
                if dep_id in context:
                    content_parts.append(str(context[dep_id]))
            analysis_content = "\n\n".join(content_parts)
        else:
            content = self.retrieve_sections(
                self.step.target_papers, 
                self.step.target_sections,
                self.step.parameters.get('focus_query')
            )
            analysis_content = "\n".join(content)

        return analysis_content