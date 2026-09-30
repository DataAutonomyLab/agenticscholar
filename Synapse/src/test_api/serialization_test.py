import yaml
from src.executor_multistep.multi_step_engine import ExecutionPlanBuilder, MultiStepResearchEngine
from src.executor_multistep.multi_step_optimizer import ResearchPlanGenerator, ResearchPlanInstantiation
from src.executor_multistep.executor.plan_step import ResearchPlan

if __name__ == "__main__":
    db_name = "test"
    filename = "src/defined_plans/plan_rank_exp_results_cross_papers.yaml"
    paper_list = ["paper1","paper2","paper3","paper4"]
    research_plan = ResearchPlan("test_id", "test_query", paper_scope=paper_list)
    research_plan.deserialize(filename)

    execution_plan_builder = ExecutionPlanBuilder(db_name)

    print(research_plan)
    research_plan.visualize("deserialized_research_plan.dot")


    execution_graph = execution_plan_builder.build_execution_graph(research_plan)

    print("Generate ExecutionGraph:")
    execution_graph.visualize("deserialized_execution_graph.dot")