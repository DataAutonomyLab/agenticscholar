import re
import json
from typing import List, Tuple, Optional
from langchain_community.chat_models import ChatOpenAI
from langchain.schema import HumanMessage

# # 初始化 ChatOpenAI 模型

llm = ChatOpenAI(
    model_name="gpt-4.1-mini",
    openai_api_key="",  # 替换为你的 API 密钥
    openai_api_base="https://api.openai.com/v1"
)


def call_llm(prompt: str) -> str:
    """
    使用 LangChain 的 ChatOpenAI 调用 gpt-4.1-mini 模型处理提示。
    返回模型的响应，格式为字符串。
    """
    try:
        messages = [HumanMessage(content=prompt)]
        response = llm.invoke(messages)
        return response.content
    except Exception as e:
        print(f"LLM 调用失败: {str(e)}")
        exit()


# 定义 Researcher Levels 和 Tasks
RESEARCHER_LEVELS = ["Junior Student", "Senior Student", "Post-Doc", "Professor"]
TASKS = [
    "Reviewing papers", "Summarizing advances", "Identifying open problems",
    "Exploring new techniques", "Comparing methods", "Investigating applications",
    "Learning basics", "Preparing presentations", "Designing experiments",
    "Reproducibility studies", "Teaching preparation"
]

# 示例问题库（从文件中提取）
EXAMPLE_QUESTIONS = {
    "Junior Student": {
        "Reviewing papers": [
            "What is the main idea of the paper \"The Case for Learned Index Structures\" by Kraska et al.?",
            "Can you summarize the key contributions of this paper in simple terms?",
            "What are the main datasets used in the experiments of this paper?",
            "What are the evaluation metrics used to compare learned indexes with traditional indexes like B-trees?",
            "The paper mentions neural networks for indexing. Can you explain how they use neural networks in this context?",
            "Are there any specific limitations of learned indexes mentioned in the paper that I should note for my review?",
            "Can you suggest a few beginner-friendly resources to understand the background concepts of learned indexes?"
        ],
        "Exploring new techniques": [
            "What are the latest machine learning techniques used in learned indexes for databases?",
            "Can you explain how reinforcement learning could be applied to improve learned indexes?",
            "Are there any examples of hybrid models combining traditional indexes with learned indexes?",
            "What are the potential benefits of using transformer-based models for learned indexes?",
            "Can you suggest a simple experiment to test a new learned index technique on a small dataset?",
            "How do I implement a basic learned index using Python for a key-value store?",
            "What challenges should I expect when trying to apply a new ML technique to learned indexes?"
        ],
    },
    "Senior Student": {
        "Reviewing papers": [
            "What is the problem statement in the paper \"Learned Indexes for Dynamic Workloads\" by Ding et al.?",
            "How does the paper address the challenge of handling dynamic data in learned indexes compared to static data?",
            "What assumptions does the paper make about the data distribution for its learned index model?",
            "Can you identify any potential biases in the experimental setup of this paper?",
            "How does the paper compare the performance of its learned index against traditional indexing methods like hash tables?",
            "What are the main criticisms or limitations of the proposed approach as discussed in the paper or related works?",
            "Can you help me draft a critical question about the scalability of their approach for my class discussion?"
        ],
        "Comparing methods": [
            "How do learned indexes for spatial data differ from those for key-value stores in terms of model design?",
            "Can you compare the performance of learned indexes versus B-trees for range queries based on recent papers?",
            "What are the trade-offs between using neural networks versus decision trees for learned indexes?",
            "Are there any papers that directly compare learned indexes for different data types, like strings versus integers?",
            "Can you summarize the advantages and disadvantages of learned indexes for dynamic versus static datasets?",
            "How do memory requirements differ across learned index models for various data types?",
            "Can you help me create a comparison chart for my thesis based on these findings?"
        ],
        "Preparing presentations": [
            "What are the most impactful papers on learned indexes that I should highlight in my presentation?",
            "Can you summarize the evolution of learned index research from 2018 to 2025?",
            "How do I explain the benefits of learned indexes to a non-technical audience at the conference?",
            "Can you suggest a visual diagram to illustrate the workflow of a learned index for my slides?",
            "What are some recent controversies or debates in the learned index research community?",
            "Can you help me draft a slide outline for a 15-minute talk on learned indexes?",
            "Are there any recent X posts or discussions about learned indexes that I could reference to make my talk timely?"
        ],
        "Reproducibility studies": [
            "What are the key experimental results reported in the paper \"Learned Indexes for Dynamic Workloads\" by Ding et al.?",
            "Can you help me locate the source code or datasets used in this paper, if available?",
            "What hardware specifications are mentioned in the paper for their experiments?",
            "How can I replicate their learned index model for range queries on a similar dataset?",
            "Are there any discrepancies in the paper’s methodology that I should check for reproducibility?",
            "What statistical methods should I use to validate the reproducibility of their performance claims?",
            "Can you suggest a checklist to ensure I cover all aspects of a reproducibility study for this paper?"
        ],
        "Identifying open problems": [
            "What are the emerging trends in learned indexes for multi-dimensional data in recent papers?",
            "Can you identify gaps in current research on learned indexes for time-series databases?",
            "How could learned indexes be adapted for edge computing environments with limited resources?",
            "Are there any unexplored machine learning techniques, like graph neural networks, for learned indexes?",
            "What are the challenges of integrating learned indexes with approximate query processing?",
            "Can you help me formulate a novel research question combining learned indexes with real-time analytics?",
            "How can I structure a literature review to support my proposed research direction?"
        ]
    },
    "Post-Doc": {
        "Summarizing advances": [
            "Can you provide a summary of the most recent papers (2023–2025) on learned indexes for databases?",
            "Which papers focus specifically on learned indexes for high-dimensional data?",
            "What are the common evaluation benchmarks used across these recent papers?",
            "Can you identify any trends in the types of machine learning models used for learned indexes in these papers?",
            "Are there any papers that combine learned indexes with other database optimization techniques, like query optimization?",
            "Can you generate a table summarizing the key contributions and limitations of the top 5 recent papers on learned indexes?",
            "How do these recent advancements address the limitations of earlier learned index models, like those from Kraska et al.?"
        ],
        "Investigating applications": [
            "What are some real-world database applications where learned indexes have been successfully implemented?",
            "Can you find case studies or industry reports on the use of learned indexes in cloud databases?",
            "How do learned indexes handle write-heavy workloads in practical database systems?",
            "Are there any open-source database systems that have integrated learned indexes?",
            "What are the challenges of deploying learned indexes in production environments with real-time constraints?",
            "Can you suggest a methodology to evaluate the cost-benefit of using learned indexes in a commercial database?",
            "How do learned indexes perform in distributed database systems compared to centralized ones?",
            "Are there any studies applying learned indexes to bioinformatics databases, such as genomic data?",
            "What challenges arise when adapting learned indexes for high-dimensional biological datasets?",
            "Can you summarize how learned indexes could improve query performance in protein sequence databases?",
            "Are there machine learning models from bioinformatics that could enhance learned index designs?",
            "What are the data characteristics of genomic datasets that might affect learned index performance?",
            "Can you suggest a research question combining learned indexes with bioinformatics applications?",
            "How can I find recent X posts or papers discussing database optimizations in bioinformatics?"
        ],
    },
    "Professor": {
        "Identifying open problems": [
            "What are the main limitations of current learned index structures for large-scale databases?",
            "Can you identify any open problems related to learned indexes for time-series data?",
            "Are there gaps in handling skewed data distributions in existing learned index research?",
            "What challenges remain in adapting learned indexes for multi-dimensional data queries?",
            "Can you find any recent papers or posts on X discussing unsolved issues in learned indexes?",
            "How do energy efficiency and computational cost factor into the limitations of learned indexes?",
            "Can you suggest a potential research question based on these gaps for a new project proposal?"
        ],
        "Exploring new techniques": [
            "How can learned indexes be integrated with quantum computing for database optimization?",
            "Are there any studies exploring learned indexes in the context of graph databases?",
            "What are the potential benefits of combining learned indexes with federated learning for privacy-preserving databases?",
            "Can you identify any recent advancements in hardware acceleration that could enhance learned index performance?",
            "What are the open challenges in applying learned indexes to streaming data applications?",
            "Can you propose a research framework for combining learned indexes with blockchain-based databases?",
            "How can I structure a research proposal to explore these interdisciplinary ideas?"
        ],

        "Teaching preparation": [
            "What are the key concepts of learned indexes that I should cover in a 1-hour lecture for graduate students?",
            "Can you provide a simple example to demonstrate how learned indexes work compared to B-trees?",
            "What are some real-world applications of learned indexes that I can use to engage students?",
            "Can you suggest a classroom activity to help students understand the trade-offs of learned indexes?",
            "Are there any recent advancements in learned indexes (2024–2025) that I should include in my lecture?",
            "How can I explain the role of machine learning in learned indexes to students with limited ML background?",
            "Can you help me create a quiz question to test students’ understanding of learned index limitations?"
        ]
    }
}


class ResearchAgent:
    def __init__(self):
        self.conversation_history = []

    def extract_researcher_level(self, question: str) -> Optional[str]:
        """通过正则表达式提取用户输入中的 Researcher Level"""
        for level in RESEARCHER_LEVELS:
            if re.search(rf"{level}", question, re.IGNORECASE):
                return level
        return None

    def extract_task(self, query: str) -> Optional[str]:
        """通过 LLM 语义分析提取任务"""
        prompt = f"""
        Given the following query, identify the most relevant task from the list: {json.dumps(TASKS)}.
        Query: {query}
        Consider the semantic intent of the query and match it to the most appropriate task.
        Examples:
        - Query: "How do learned indexes for spatial data differ from those for key-value stores in terms of model design?" → Task: Comparing methods
        - Query: "Can you help me formulate a novel research question combining learned indexes with real-time analytics?" → Task: Identifying open problems
        - Query: "What are the main datasets used in the experiments of this paper?" → Task: Reviewing papers
        Return only the task name as a string, without quotes or additional formatting (e.g., Identifying open problems).
        If no task matches or the intent is unclear, return: Reviewing papers
        """
        task = call_llm(prompt).strip()
        return task if task in TASKS else "Reviewing papers"

    # 提取研究领域
    def extract_research_topic(self, query: str) -> str:
        """
        从用户查询中提取研究领域，使用 LLM 进行语义分析。
        如果无法提取，返回默认领域 'learned indexes'。
        """
        prompt = f"""
        Extract the primary research topic from the following query. The topic should be a concise phrase describing the research area (e.g., 'learned indexes', 'graph neural networks', 'reinforcement learning').
        Query: {query}
        If no clear topic is identified, return 'learned indexes' as the default topic.
        Return only the topic as a string.
        """
        topic = call_llm(prompt).strip()
        return topic if topic else "learned indexes"

    def infer_researcher_level(self, query: str) -> str:
        """通过 LLM 推断 Researcher Level"""
        prompt = f"""
        Based on the following query, infer the researcher's level (Junior Student, Senior Student, Post-Doc, Professor).
        Query: {query}
        Consider the complexity, terminology, and context of the query.
        Return only the inferred level as a string (e.g., 'Senior Student').
        """
        return call_llm(prompt)

    # === 修改方法：recommend_questions ===
    def recommend_questions(self, researcher_level: str, task: str, query: str) -> List[str]:
        """根据 Researcher Level、Task 和用户查询推荐问题"""
        # 提取用户查询中的研究领域
        user_topic = self.extract_research_topic(query)
        is_learned_indexes = user_topic.lower() == "learned indexes"

        if researcher_level in EXAMPLE_QUESTIONS and task in EXAMPLE_QUESTIONS[researcher_level] and is_learned_indexes:
            # 如果领域是 learned indexes 且有匹配的示例问题，直接返回
            return EXAMPLE_QUESTIONS[researcher_level][task]
        else:
            # 使用 LLM 生成问题，参考 EXAMPLE_QUESTIONS 的结构
            example_questions = []
            if researcher_level in EXAMPLE_QUESTIONS and task in EXAMPLE_QUESTIONS[researcher_level]:
                example_questions = EXAMPLE_QUESTIONS[researcher_level][task][:3]  # 取前 3 个示例问题作为模板

            prompt = f"""
            Generate 3 relevant questions for a {researcher_level} working on {task} in the research area of '{user_topic}' based on the following user query:
            Query: {query}

            Ensure the questions:
            - Are relevant to the research area '{user_topic}'.
            - Match the researcher's level ({researcher_level}) and task ({task}).
            - Follow the style and structure of the following example questions (if provided):
            {json.dumps(example_questions, indent=2) if example_questions else "No example questions available."}

            Return a JSON list of exactly 3 questions as a string, without Markdown code blocks or additional formatting (e.g., ["question1", "question2", "question3"]).
            """
            try:
                response = call_llm(prompt)
                return json.loads(response)
            except json.JSONDecodeError:
                # 如果 LLM 返回非 JSON 格式，提供默认问题
                return [
                    f"What are the key concepts of {user_topic} that a {researcher_level} should understand for {task}?",
                    f"How do recent advancements in {user_topic} address challenges in {task}?",
                    f"Can you suggest an experimental setup to evaluate {user_topic} for {task}?"
                ]

    def process_query(self, query: str) -> Tuple[str, List[str]]:
        """处理用户问题，返回响应和推荐问题"""
        self.conversation_history.append({"role": "user", "content": query})

        researcher_level = self.extract_researcher_level(query)
        task = self.extract_task(query)

        if researcher_level:
            # 场景 a：用户明确提供身份
            if not task:
                task = "Reviewing papers"  # 默认任务
            recommended_questions = self.recommend_questions(researcher_level, task, query)
            response = f"Your identity has been identified as {researcher_level}, and your task is {task}. Here are the recommended questions:"
        else:
            # 场景 b：未提供身份，尝试推断
            inferred_level = self.infer_researcher_level(query)
            if inferred_level in RESEARCHER_LEVELS:
                task = task or "Reviewing papers"  # 默认任务
                recommended_questions = self.recommend_questions(inferred_level, task, query)
                response = f"Your identity has been inferred as {inferred_level}, and your task is {task}. Here are the recommended questions:"
            else:
                response = "We are unable to verify your researcher levels. Which of the following applies to you? \nOptions: Junior Student, Senior Student, Post-Doc, Professor。"
                recommended_questions = []
                self.conversation_history.append({
                    "role": "system",
                    "content": response})
                return response, recommended_questions

        return response, recommended_questions

    def process_followup(self, user_response: str) -> Tuple[str, List[str]]:
        """处理用户对身份询问的回复"""
        self.conversation_history.append({"role": "user", "content": user_response})
        researcher_level = self.extract_researcher_level(user_response)

        if researcher_level in RESEARCHER_LEVELS:
            original_question = next((item["content"] for item in self.conversation_history if item["role"] == "user"),
                                     "")
            task = self.extract_task(original_question) or "Reviewing papers"
            recommended_questions = self.recommend_questions(researcher_level, task, original_question)
            response = f"Thank you for your response. Your identity has been confirmed as {researcher_level} and your task is {task}. Here are the recommended questions:"
        else:
            response = "Sorry, we were unable to identify you. Please select again: Junior Student, Senior Student, Post-Doc, Professor。"
            recommended_questions = []

        return response, recommended_questions


# 测试代码
if __name__ == "__main__":
    agent = ResearchAgent()
    question = "I am a junior student and plan to make a presentation about learned indexes."
    print('User 1:', question)
    response, recommended = agent.process_query(question)
    print("System:", response)
    if len(recommended) != 0:
        print("Recommended questions:", recommended)


    '''
    # ================ 测试场景 a：用户明确提供身份 ================
    question1 = "I am a junior student and would like to review papers on learned indexes."
    print('User 1:', question1)
    response, recommended = agent.process_query(question1)
    print("System:", response)
    if len(recommended) != 0:
        print("Recommended questions:", recommended)
        


    # ================ 测试场景 b：用户仅提供问题 ================
    question2 = "Can you identify gaps in current research on learned indexes for time-series databases?"
    print('\nUser 2:', question2)
    response, recommended = agent.process_query(question2)
    print("System:", response)
    if len(recommended) != 0:
        print("Recommended questions:", recommended)

    # 模拟用户回复身份
    followup = "I am a senior student."
    print('User 2:', followup)
    response, recommended = agent.process_followup(followup)
    print("System (followed):", response)
    if len(recommended) != 0:
        print("Recommended questions:", recommended)


    # ================ 测试场景 c: 其他研究领域下用户提问 ================
    question3 = "How can we compare the performance of different knowledge graph methods in recommender systems?"
    print('\nUser 3:', question3)
    response, recommended = agent.process_query(question3)
    print("System:", response)
    if len(recommended) != 0:
        print("Recommended questions:", recommended)

    # 模拟用户回复身份
    followup = "I am a senior student."
    print('User 3:', followup)
    response, recommended = agent.process_followup(followup)
    print("System (followed):", response)
    if len(recommended) != 0:
        print("Recommended questions:", recommended)
    '''