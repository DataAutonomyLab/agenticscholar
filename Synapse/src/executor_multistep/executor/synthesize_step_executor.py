from enum import Enum
from typing import Any, Dict, List
from src.executor_multistep.executor.plan_step import ExecutorType, ResearchStep, StepExecutor, StepResult
from src.prompts.base import run_structured_prompt
from src.executor_multistep.executor.plan_step import try_dummy


class SynthesizeType(Enum):
    FINAL_ANSWER = {
        "name": "synthesize_final_answer",
        "description": "synthesize the research results into a comprehensive, well-structured answer to the original query.",
        "mode":"global",
        "handler": try_dummy,
        "input_hint": "it can take all preceding steps as inputs",
    }
    DEFAULT = {
        "name": "default",
        "description": "synthesize findings from multiple research steps to create a comprehensive understanding of the research question.",
        "mode":"global",
        "handler": try_dummy,
        "input_hint": "it can take all preceding steps as inputs"
    }
    
    @classmethod
    def from_str(cls, s: str) -> "SynthesizeType | None":
        value_to_member = {member.value["name"]: member for member in cls}
        return value_to_member.get(s)
    
def synthesize_research_findings(content: List, description: str, question: str) -> str:
    return run_structured_prompt(
        template_name = "synthesize_research_findings.yaml",
        variables={
            "research_steps": content,
            "original_question": question,
            "synthesis_goal": description
        },
        is_reserch=True
    )

def synthesize_final_answer(query: str, results: str) -> str:
    return run_structured_prompt(
        template_name = "synthesize_final_answer.yaml",
        variables={
            "query": query,
            "research_results": results
        },
        is_reserch=True 
    )

class SynthesizeStepExecutor(StepExecutor):
    """Executor for synthesis steps that combine multiple information sources"""

    synthesize_type: SynthesizeType

    def __init__(self, db_name: str, step: ResearchStep, target_paper: str):
        super().__init__(db_name, step, target_paper)
        self.executor_type = ExecutorType.SYNTHESIZE
        type_str = step.handler_type if step.handler_type is not None else "default"
        self.synthesize_type = SynthesizeType.from_str(type_str)
        if self.synthesize_type is None:
            raise ValueError(f"No SynthesizeStepExecutor registered for type {type_str}") 
        
    def execute(self, context: Dict[str, Any]) -> StepResult:
        inputs = self.get_inputs(context)
        if self.synthesize_type == SynthesizeType.DEFAULT:
            # content = self.get_content(context)
            result = synthesize_research_findings(inputs,
                                    self.step.description,
                                    self.step.parameters.get('original_question', ''))
            return StepResult(
                step_id=self.step.id,
                success=True,
                result=result,
                metadata={"inputs_synthesized": len(inputs)}
            )
        elif self.synthesize_type == SynthesizeType.FINAL_ANSWER:
            
            result = synthesize_final_answer(self.step.description, inputs)
            return StepResult(
                step_id=self.step.id,
                success=True,
                result=result,
            )
        
    # def get_content(self, context: Dict[str, Any]):
    #     # Gather all dependency results
    #     synthesis_inputs = []
    #     for dep_id in self.step.dependencies:
    #         if dep_id in context:
    #             synthesis_inputs.append({
    #                 "step_id": dep_id,
    #                 "content": str(context[dep_id])
    #             })
        
    #     # Also include any direct section content if specified
    #     if self.step.target_sections:
    #         section_content = self.retrieve_sections(
    #             self.step.target_papers,
    #             self.step.target_sections
    #         )
    #         synthesis_inputs.append({
    #             "step_id": "direct_sections",
    #             "content": "\n".join(section_content)
    #         })
    #     return synthesis_inputs