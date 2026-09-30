from src.config.config import get_llm_config_for_module
from src.synapse_utils import *
from src.defined_plans.id_mapping import ID2File
from src.executor.executor_entry import executor_entry
from src.routing.select_plan import select_prompt_plan
from src.paper_search_in_kb import s2_paper_search
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
import yaml
import uuid
from src.executor_qa_lc.large_context_qa import LargeContextQAEngine
from src.executor_multistep.multi_step_engine import ExecutionPlanBuilder, MultiStepResearchEngine
from src.executor_multistep.multi_step_optimizer import ResearchPlanGenerator, ResearchPlanInstantiation

CHAT_ONLINE_SEARCH = "OS"
CHAT_PAPER_SEARCH_KB = "PS"
CHAT_QA = "QA"
SEP_L1 = "#" 
import sqlite3
# Format of queries:
# CHAT_PAPER_SEARCH_KB SEP_L1 User Query
# CHAT_QA SEP_L1 Paper IDs SEP_L1 Plan ID SEP_L1 User Query
# paper1 SEP_L2 paper2 SEP_L2 ... SEP_L2 paperN

SEP_L2 = "," # for Paper IDs

USE_PLAN_CLASSIFIER = False

# TODO: move it to configuration file
DATABASE_NAME = get_data_path() / "db" / "synapse_python.db"
print(f"Database path: {DATABASE_NAME}")

class QAEngine(enumerate):
    DEFAULT_ENGINE = 0
    LARGE_CONTEXT = 1
    MULTI_STEP = 2

class QAHandler:
    def __init__(self, user_id, kb_id, session_id, where="ms"):
        self.user_id = user_id
        self.kb_id = kb_id
        self.session_id = session_id
        user_id_2 = user_id.split('-')[0].lower()
        kb_name_2 = kb_id.split('-')[0].lower()
        db_name = f"SYNAPSE{user_id_2}{kb_name_2}_{where}"
        self.db_name = db_name
        self.research_engine = MultiStepResearchEngine(db_name)
        self.plan_generator = ResearchPlanGenerator()
        self.plan_instantiation = ResearchPlanInstantiation()
        self.execution_plan_builder = ExecutionPlanBuilder(db_name)
        self.large_context_engine = LargeContextQAEngine(user_id=user_id, kb_id=kb_id, where=where)
    
    '''
    route_query -> _paper_search_handle
                -> _qa_handle -> _decompose_query
                              -> select_prompt_plan
                              -> executor_entry
    '''
       
    def route_query(self, query):
        # print(f"Routing query: {query}")
        # infos = query.split(SEP_L1)
        # if infos[0] == CHAT_ONLINE_SEARCH:
        #     return self._online_search_handle(infos[1:])
        # elif infos[0] == CHAT_PAPER_SEARCH_KB:
        #     return self._paper_search_handle(infos[1:])
        # elif infos[0] == CHAT_QA:
        #     return self._qa_handle(infos[1:])
        # else:
        #     raise ValueError(f"Unknown query type: {infos[0]}")
        
        prompt_query_routing = '''
                ## Task
            You are an expert query classifier for an academic search system.  
            Your task is to classify a user's query into one of two categories: **PAPER_SEARCH** or **PAPER_QA**.

            ---

            ## 1. Category Definitions

            - **PAPER_SEARCH**  
            The user's primary intent is to find or discover papers.  
            They are looking for a list of papers based on metadata (like title, author, venue, year) or concepts.  
            The answer to their query would be a list of one or more papers.

            - **PAPER_QA**  
            The user has one or more specific papers already in mind and is asking a question about their content.  
            They want to understand, summarize, or compare the methods, results, or other details from within those papers.

            ---

            ## 2. Examples

            - **Query:** "Have there been works like 'Graph Attention Networks' for graph neural network improvements?"  
            **Category:** PAPER_SEARCH  

            - **Query:** "what are the differences between FLAT and UAE in their proposed method?"  
            **Category:** PAPER_QA  

            - **Query:** "Studies from Stanford University focusing on graph embeddings"  
            **Category:** PAPER_SEARCH  

            - **Query:** "what are the experimental settings in the 'Attention is All You Need' paper?"  
            **Category:** PAPER_QA  

            - **Query:** "Graph neural network methods introduced from 2017 onwards"  
            **Category:** PAPER_SEARCH  

            - **Query:** "what are the baselines?"  
            **Category:** PAPER_QA *(This is implicitly asking about a paper from a previous context).*

            ---

            ## 3. Instructions
            You must respond with **only the category name**:  
            - `PAPER_SEARCH`  
            - `PAPER_QA`  

            Do **not** add any explanation.

            ---

            ## User Query to Classify
            {user_query}
        '''        
        local_config = get_llm_config_for_module("QueryRouting")
        llm = ChatOpenAI(
            model=local_config["default_model"],
            openai_api_base=local_config["base_url"],
            openai_api_key=local_config["api_key"],
            # temperature=0.3
        )
        prompt_ = PromptTemplate.from_template(prompt_query_routing)
        chain = prompt_ | llm
        response = chain.invoke({"user_query": query})
        response_text = response.content if hasattr(response, "content") else str(response)
        
        if response_text.strip() == "PAPER_SEARCH":
            return self._paper_search_handle(query)
        elif response_text.strip() == "PAPER_QA":
            return self._qa_handle(query)
        else:
            raise ValueError(f"Unknown query type returned by LLM: {response_text.strip()}")

    # it is not used now, but we can use it in the future 
    # by searching from google or other search engines
    def _online_search_handle(self, query):
        pass

    def _paper_search_handle(self, query):
        print("Paper search handle called with query:", query)
        paper_lists, _ = s2_paper_search.search_papers_entry(self.user_id, self.kb_id, query)
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        timestamp_iso = get_cur_time()
        for paper_id in paper_lists:
            new_id = str(uuid.uuid4())
            cursor.execute(
                "INSERT INTO session_focused_papers (id, session_id, paper_id, timestamp) VALUES (?, ?, ?, ?)",
                (new_id, self.session_id, paper_id, timestamp_iso)
            )
        conn.commit()
        conn.close()
        print(f"Updated focused papers for session {self.session_id} with: {paper_lists}")
        
        if len(paper_lists) == 0:
            return "No papers found for the search query in current KB."
        return "The relevant papers are " + SEP_L2.join(paper_lists)  # 0 is the plan ID for general question single plan
        
    def _decompose_query(self, query):
        prompt_decompose = '''## Task
            Decompose the user's query into two parts: a **paper scope** and a **question**.

            ## Instructions
            You will be given a user query. Your task is to identify the specific academic papers the user is asking about (the **paper scope**) and the question they are asking about those papers.

            - The **paper scope** is a comma-separated list of paper titles mentioned in the query.  
            - If no specific papers are mentioned, the paper scope is empty.

            ## Output Format
            You **MUST** return a single string in the following format:

            `paper_list#$#question`

            - `paper_list` is the comma-separated list of paper titles.  
            - `#$#` is the exact, required separator.  
            - `question` is the user's question.  
            - If `paper_list` is empty, the output should start with `#$#`.
            - Remove the paper information from the question, so that the question is only about the content of the papers.

            ---

            ## Examples

            **Query 1:**  
            in the papers 'Attention is All You Need' and 'BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding', what is the main difference in their architecture?  

            **Output 1:**  
            Attention is All You Need,BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding#$#what is the main difference in their architecture?

            ---

            **Query 2:**  
            what are the latest advancements in large language models?  

            **Output 2:**  
            #$#what are the latest advancements in large language models?

            ---

            **Query 3:**  
            can you summarize the key findings of the 'PaLM 2 Technical Report'?  

            **Output 3:**  
            PaLM 2 Technical Report#$#summarize the key findings

            ---

            ## User Query to Process
            {user_query}'''
        
        local_config = get_llm_config_for_module("QueryDecomposition")
        llm = ChatOpenAI(
            model=local_config["default_model"],
            openai_api_base=local_config["base_url"],
            openai_api_key=local_config["api_key"],
            temperature=0.3
        )
        prompt_ = PromptTemplate.from_template(prompt_decompose)
        chain = prompt_ | llm
        response = chain.invoke({"user_query": query})
        response_text = response.content if hasattr(response, "content") else str(response)
        print(f"[DEGBUG] LLM response for query decomposition: {response_text}")
        _info = response_text.split("#$#")
        return _info[0].split(','), _info[1]  # paper_list, question
        
    def _qa_handle(self, query):
        # TODO: call LLM to check whether the users mention the paper IDs
        # if they do, we will use the paper IDs to retrieve the sections from the database
        # and also extract the question from the query
        # paper_lists = query[0].split(SEP_L2)
        paper_lists, rewrite_query = self._decompose_query(query)
        if len(paper_lists) == 0:
            conn = sqlite3.connect(DATABASE_NAME)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT paper_id FROM session_focused_papers
                WHERE session_id = ? AND timestamp = (
                    SELECT MAX(timestamp) FROM session_focused_papers WHERE session_id = ?
                )
                """,
                (self.session_id, self.session_id)
            )
            focused_papers_rows = cursor.fetchall()
            conn.close()
            paper_lists = [row['paper_id'] for row in focused_papers_rows]
            print(f"Session {self.session_id} latest focused papers from DB: {paper_lists}")
        else:
            conn = sqlite3.connect(DATABASE_NAME)
            cursor = conn.cursor()
            timestamp_iso = get_cur_time()
            for paper_id in paper_lists:
                new_id = str(uuid.uuid4())
                cursor.execute(
                    "INSERT INTO session_focused_papers (id, session_id, paper_id, timestamp) VALUES (?, ?, ?, ?)",
                    (new_id, self.session_id, paper_id, timestamp_iso)
                )
            conn.commit()
            conn.close()
            print(f"Updated focused papers for session {self.session_id} with: {paper_lists}")
        if len(paper_lists) == 0:
            print("No papers provided for QA handling for query:", query)
            return "No papers provided for QA handling."
        
        
        user_query = rewrite_query # we only use it for the plan '0', the generate case        
        

        plan_id, *_ = select_prompt_plan(user_query)
        if plan_id == 'no':
            plan_id = 'plan_general_question_single' # general question plan
            
        if plan_id == 'plan_general_question_single':
            # suc, result = s(user_query, paper_lists, where)
            research_plan = self.plan_generator.generate_plan(user_query, paper_lists)
            if research_plan:
                self.plan_instantiation.instantiate_plan(research_plan)
                execution_graph = self.execution_plan_builder.build_execution_graph(research_plan)
                execution_result = self.research_engine.execute_plan(execution_graph)
                suc = True
                result = execution_result["final_synthesis"]
            else:
                suc = False
                result = ""
            if suc:
                print("[Info] Using multi-step QA result for general question.")
                return result
        
        plan_path = get_plan_path() / f"{plan_id}.yaml"
       

        with open(plan_path, "r") as f:
            workflow = yaml.safe_load(f)

        new_query = ','.join(paper_lists)
        workflow["task_scope"]["query"] = new_query

        for node in workflow.get("nodes", []):
            if plan_id == "plan_general_question_single":
                if node["id"] == "synthesize_answer":
                    node["inputs"] = [f'retrieval_query["{user_query}"]']
            node["db_name"] = self.db_name

        result = executor_entry(self.db_name, workflow)
        

        return result
        # for test routing and plan selection test purpose
        # return ','.join(paper_lists) + 'xxxx' + plan_id
