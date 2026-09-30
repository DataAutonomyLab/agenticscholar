from typing import Any, Dict
from src.executor_multistep.executor.plan_step import ExecutorType, ResearchStep, StepExecutor, StepResult
from src.paper_search_in_kb import s2_paper_search
from src.prompts.base import run_structured_prompt


class SearchStepExecutor(StepExecutor):
    """Executor for focused search within papers"""
    
    def __init__(self, db_name: str, step: ResearchStep, target_paper: str):
        super().__init__(db_name, step, target_paper)
        self.executor_type = ExecutorType.SEARCH
        self.user_id = step.parameters.get("user_id", "synapse")
        self.kb_id = step.parameters.get("kb_id", "python")
        
    def execute(self, context: Dict[str, Any]) -> StepResult:
        #TODO: get query
        query = self.step.description
        paper_lists, _ = s2_paper_search.search_papers_entry(self.user_id, self.kb_id, query)
        if len(paper_lists) == 0:
            print("No papers found for the search query in current KB.")
        else:
            print(f"The relevant papers are {paper_lists}.")
        
        return StepResult(
            step_id=self.step.id,
            success=True,
            result=paper_lists,
            metadata={
                "papers_found": len(paper_lists)
            }
        )

#         try:
#             search_query = step.parameters.get('search_query', step.description)
            
#             # Perform targeted search across specified sections
#             search_results = []
#             for paper_id in step.target_papers:
#                 for section in step.target_sections:
#                     results = self.indexer.search_weaviatev2(
#                         query_text=search_query,
#                         paper_id=paper_id,
#                         tags=[section],
#                         db_name=self.db_name,
#                         n_results=step.parameters.get('max_results', 3)
#                     )
                    
#                     for result in results:
#                         search_results.append({
#                             "paper_id": result.properties['paper_id'],
#                             "section": result.properties['section_title'],
#                             "content": result.properties['section_text'],
#                             "relevance_score": getattr(result, 'score', 0.0)
#                         })
            
#             # Process and format search results
#             formatted_results = run_structured_prompt(
#                 "research/process_search_results.yaml",
#                 {
#                     "search_query": search_query,
#                     "search_results": search_results,
#                     "processing_focus": step.description
#                 }
#             )
            
#             return StepResult(
#                 step_id=step.id,
#                 success=True,
#                 result=formatted_results,
#                 metadata={
#                     "results_found": len(search_results),
#                     "papers_searched": len(step.target_papers),
#                     "sections_searched": len(step.target_sections)
#                 }
#             )
            
#         except Exception as e:
#             return StepResult(
#                 step_id=step.id,
#                 success=False,
#                 result=None,
#                 error_message=str(e)
#             )