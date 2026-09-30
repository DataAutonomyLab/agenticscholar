from enum import Enum
from typing import Any, Dict, List, Optional
from src.executor_multistep.executor.plan_step import ExecutorType, ResearchStep, StepExecutor, StepResult, try_dummy
from src.index.weaviate_instance import WeaviateIndexer

class RetrieveType(Enum):
    DEFAULT = {
        "name": "default",
        "description": "Retrieves the relevant section from each paper to gather relevant content.",
        "mode": "local",
        "handler": try_dummy
    }
    @classmethod
    def from_str(cls, s: str) -> "RetrieveType | None":
        value_to_member = {member.value["name"]: member for member in cls}
        return value_to_member.get(s)
    
class RetrieveStepExecutor(StepExecutor):
    """Executor for verification steps"""
    retrieve_type: RetrieveType

    def __init__(self, db_name: str, step: ResearchStep, target_paper: str):
        super().__init__(db_name, step, target_paper)
        self.indexer = WeaviateIndexer(db_name=db_name)
        self.executor_type = ExecutorType.RETRIEVE
        type_str = step.handler_type if step.handler_type is not None else "default"
        self.retrieve_type = RetrieveType.from_str(type_str)
        if self.retrieve_type is None:
            print(f"No RetrieveStepExecutor registered for type {type_str}, fallback to default") 
            self.retrieve_type = RetrieveType.DEFAULT

    def execute(self, context: Dict[str, Any]) -> StepResult:
        
        result = self.execute_internal()
        return StepResult(
            step_id=self.step.id,
            success=True,
            result=result
        )

    def execute_internal(self) -> str:
        content = self.retrieve_sections(
            [self.target_paper], 
            self.step.target_sections,
            self.step.parameters.get('search_query', self.step.description)
        )
        combined_content = "\n".join(content)
        return combined_content
    
    def retrieve_sections(self, paper_ids: List[str], section_tags: List[str], 
                         query_text: Optional[str] = None) -> List[str]:
        """Retrieve relevant sections from papers"""
        all_content = []
        for paper_id in paper_ids:
            for tag in section_tags:
                results = self.indexer.search_weaviatev2(
                    query_text=query_text or "",
                    paper_id=paper_id,
                    tags=[tag],
                    db_name=self.db_name,
                    n_results=5
                )
                for result in results:
                    content = f"Paper ID: {result.properties['paper_id']}\n"
                    content += f"Section: {result.properties['section_title']}\n"
                    content += f"Content: {result.properties['section_text']}\n\n"
                    all_content.append(content)
        return all_content