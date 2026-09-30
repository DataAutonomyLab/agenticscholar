import json
from typing import Tuple
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_community.callbacks import get_openai_callback
from src.synapse_utils import get_routing_path
from src.config.config import get_llm_config_for_module
from src.index.weaviate_instance import WeaviateIndexer4PlanSelection

PREDEFINED_PLANS_DB = "synapse_predefined_plans_db"

def get_candidate_plans(query: str) -> Tuple[dict, dict]:
    index = WeaviateIndexer4PlanSelection(db_name=PREDEFINED_PLANS_DB)
    results = index.search_candidate_plan(query)
    candidates_plan_desc = {}
    candidates_step_desc = {}
    for result in results:
        candidates_plan_desc[result.properties["plan_id"]] = result.properties["description"]
        candidates_step_desc[result.properties["plan_id"]] = result.properties["step_description"]

    return candidates_plan_desc, candidates_step_desc

def select_prompt_plan(query: str, enable_two_stage = True) -> Tuple[str, str, dict]:
    """
    Select the most appropriate prompt plan based on the user's query.
    :param query: The user's query string.
    :return: The selected prompt plan ID.
    """
    # TODO: Section 4.2
    local_config = get_llm_config_for_module("QueryRouting")
    llm = ChatOpenAI(
        model=local_config["default_model"],
        openai_api_base=local_config["base_url"],
        openai_api_key=local_config["api_key"],
        temperature=0.1)
    if enable_two_stage:
        name2description, name2stepdesc = get_candidate_plans(query)
    else:
        with open(get_routing_path() / "name2description.json", 'r', encoding='utf-8') as f:
            name2description = json.load(f)
        with open(get_routing_path() / "name2stepdesc.json", 'r', encoding='utf-8') as f:
            name2stepdesc = json.load(f)

    with open(get_routing_path() / "name2plan.json", 'r', encoding='utf-8') as f:
        name2plan = json.load(f)
        
        
    name2plan['no'] = 'plan_general_question_single'

    prompt_ = """
        You are an expert task classification agent. Your goal is to match a user's query to one of the predefined tasks.

        Analyze the user's query and determine which of the following tasks best matches the user's intent.

        **TASKS:**
        {task_description}

        **USER QUERY:**
        {user_query}

        **INSTRUCTIONS:**
        1.  Read the query and understand its core intent.
        2.  Compare the query's intent against the description of each task.
        3.  Respond with ONLY the ID of the single best-matching task in json format: {{ "task_id": "taskxxx" }} where "taskxxx" is the ID of the task.
        4.  If the query is asking about novelty, contributions, or impact justification, but does not constrain the novelty to a specific method, problem, or experiment, then return:
        {{"task_id": "no"}} — because no task covers general contribution analysis. If the query does not match any defined task at all, also return {{"task_id": "no"}}.
        5.  If no task is a suitable match for the query, you MUST respond with the exact word "no": {{ "task_id": "no" }}.
    """
    
    # prompt = prompt.format(user_query=query, prompt_dict=name2description)
    prompt = PromptTemplate.from_template(prompt_)
    chain = prompt | llm
    variables = {
        "user_query": query,
        "task_description": name2description
    }
    # name_and_papers = query_llm(prompt)
    with get_openai_callback() as cb:
        response = chain.invoke(variables)
    # response = chain.invoke({})
    token_stats = {
        "input_tokens": cb.prompt_tokens,
        "output_tokens": cb.completion_tokens
    }
    response_text = response.content if hasattr(response, "content") else str(response)
    answer =  json.loads(response_text)
    print(f"[DEBUG] LLM response: {answer}")
    plan_id = name2plan[answer["task_id"]]
    print(f"Selected plan ID: {plan_id}")

    if answer["task_id"] == "no":
        step_desc = list(name2stepdesc.items())[0][1]
    else:
        step_desc = name2stepdesc[answer["task_id"]]

    return plan_id, step_desc, token_stats

# print(select_prompt_plan("What are the q error of Histogram on JOB"))