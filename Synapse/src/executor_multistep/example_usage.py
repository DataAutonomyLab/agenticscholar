from src.executor_multistep.multi_step_engine import ExecutionPlanBuilder, MultiStepResearchEngine, ResearchPlanGenerator
from src.executor_multistep.multi_step_optimizer import ResearchPlanInstantiation

def example_usage():
    """Examples of how to use the multi-step research system"""
    
    # Example 1: Basic setup
    user_id = "test-user"
    kb_id = "test-kb" 
    user_id_2 = user_id.split('-')[0].lower()
    kb_name_2 = kb_id.split('-')[0].lower()
    db_name = f"SYNAPSE{user_id_2}{kb_name_2}_ms"
    session_id = "test-session"
        
    # Example 2: Complex queries that will trigger multi-step processing
    complex_queries = [
        "Do the experimental results in these papers support the claims made in their introductions?",
        "Compare the methodologies proposed in these papers and analyze their relative effectiveness",
        "What are the main theoretical contributions and how well are they validated experimentally?",
        "Identify inconsistencies between the problem statements and the proposed solutions",
        "How do the evaluation metrics used relate to the stated research objectives?"
    ]
    # method argue!
    
    # Example 3: Processing a complex query
    query = "hat are the main differences in the novelty claims of the two methods, and how convincingly are these claims supported throughout the studies?" #complex_queries[0] #"Do the experimental results support the claims made in the introduction?"
    
    # try:
    #     result = qa_handler.route_query(query)
    #     print(f"Query: {query}")
    #     print(f"Result: {result}")
    # except Exception as e:
    #     print(f"Error processing query: {e}")
    
    # Example 4: Direct research engine usage
    research_engine = MultiStepResearchEngine(db_name)
    plan_generator = ResearchPlanGenerator()
    plan_instantiation = ResearchPlanInstantiation()
    execution_plan_builder = ExecutionPlanBuilder(db_name)

    paper_ids = ["autoformer", "informer"]  # Example paper IDs
    research_plan = plan_generator.generate_plan(query, paper_ids)
    
    print("Generated Research Plan:")
    print(research_plan)
    
    if research_plan:
        plan_instantiation.instantiate_plan(research_plan)
        execution_graph = execution_plan_builder.build_execution_graph(research_plan)
        execution_result = research_engine.execute_plan(execution_graph)
        
        print("Multi-step research completed:")
        print(execution_result["final_synthesis"])
    else:
        print("Query doesn't require multi-step processing")

example_usage()