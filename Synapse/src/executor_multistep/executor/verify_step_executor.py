from enum import Enum
from typing import Any, Dict
from src.executor_multistep.executor.plan_step import ExecutorType, ResearchStep, StepExecutor, StepResult, try_dummy
from src.prompts.base import run_structured_prompt

def verify_claims(claims: str, content: str, criteria: str) -> str:
    return run_structured_prompt(
        template_name = "verify_claims.yaml",
        variables={
            "claims": claims,
            "evidence": content,
            "verification_criteria": criteria
        },
        is_reserch=True
    )

class VerifyType(Enum):
    DEFAULT = {
        "name": "default",
        "description": "Verify the provided claims against the given evidence, determining support levels and identifying gaps.",
        "mode": "global",
        "handler": try_dummy
    }
    @classmethod
    def from_str(cls, s: str) -> "VerifyType | None":
        value_to_member = {member.value["name"]: member for member in cls}
        return value_to_member.get(s)

class VerifyStepExecutor(StepExecutor):
    """Executor for verification steps"""
    verify_type: VerifyType

    def __init__(self, db_name: str, step: ResearchStep, target_paper: str):
        super().__init__(db_name, step, target_paper)
        self.executor_type = ExecutorType.VERIFY

        type_str = step.handler_type if step.handler_type is not None else "default"
        self.verify_type = VerifyType.from_str(type_str)
        if self.verify_type is None:
            print(f"No VerifyStepExecutor registered for type {type_str}, fallback to default") 
            self.verify_type = VerifyType.DEFAULT

    def execute(self, context: Dict[str, Any]) -> StepResult:
        # Get claims from previous steps
        claims = context.get(self.step.dependencies[0]) if self.step.dependencies else ""
        
        # Get evidence from sections
        # evidence_content = self.get_content(context)
        evidence_content = context.get(self.step.dependencies[1]) if self.step.dependencies else ""
        
        result = self.verify_claims(str(claims),
                                        evidence_content,
                                        self.step.parameters.get('criteria', 'standard'))
        return StepResult(
            step_id=self.step.id,
            success=True,
            result=result
        )

    # def get_content(self, context: Dict[str, Any]):
    #     # Get evidence from sections
    #     evidence_content = self.retrieve_sections(
    #         self.step.target_papers,
    #         self.step.target_sections
    #     )
    #     evidence = "\n".join(evidence_content)
    #     return evidence