# Large context window QA system for direct paper processing

from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
import logging
from pathlib import Path

from src.prompts.base import run_structured_prompt
from src.synapse_utils import get_data_path
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from src.config.config import get_llm_config_for_module


class QuestionType(Enum):
    """Types of questions based on how they apply to multiple papers"""
    INDIVIDUAL = "individual"  # Apply to each paper separately
    CROSS_PAPER = "cross_paper"  # Work on all papers simultaneously
    SINGLE_PAPER = "single_paper"  # Only one paper involved


@dataclass
class PaperContent:
    """Container for paper content"""
    paper_id: str
    title: str
    content: str  # Full markdown content
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class QAResult:
    """Result of QA processing"""
    question: str
    question_type: QuestionType
    papers_involved: List[str]
    answer: str
    individual_answers: Dict[str, str] = None  # For individual questions
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.individual_answers is None:
            self.individual_answers = {}
        if self.metadata is None:
            self.metadata = {}


class QuestionTypeClassifier:
    """Classifies question types for multi-paper scenarios"""
    
    def __init__(self):
        self.logger = logging.getLogger("question_classifier")
    
    def classify_question(self, question: str, paper_count: int) -> QuestionType:
        """Classify question type based on content and paper count"""
        
        if paper_count == 1:
            return QuestionType.SINGLE_PAPER
        
        # Use LLM to classify the question type
        classification_prompt = '''
        You are an expert at analyzing research questions to determine how they should be applied to multiple papers.

        Given a research question and the fact that there are {paper_count} papers involved, classify the question as either:

        1. **INDIVIDUAL**: The question should be answered separately for each paper, then potentially combined
           - Examples: "What are the experimental settings?", "Summarize the methodology", "What datasets were used?"
           - These questions ask for specific information that exists independently in each paper

        2. **CROSS_PAPER**: The question requires analyzing all papers together simultaneously
           - Examples: "Compare the proposed methods", "Which paper has better performance?", "What are the differences in approaches?"
           - These questions require direct comparison, ranking, or analysis across papers

        Question: "{question}"
        Number of papers: {paper_count}

        Respond with only one word: "INDIVIDUAL" or "CROSS_PAPER"
        '''
        
        local_config = get_llm_config_for_module("QueryClassification")
        llm = ChatOpenAI(
            model=local_config["default_model"],
            openai_api_base=local_config["base_url"],
            openai_api_key=local_config["api_key"],
            temperature=0.1
        )
        
        prompt = PromptTemplate.from_template(classification_prompt)
        chain = prompt | llm
        
        response = chain.invoke({
            "question": question,
            "paper_count": paper_count
        })
        
        response_text = response.content.strip().upper()
        
        if "INDIVIDUAL" in response_text:
            return QuestionType.INDIVIDUAL
        elif "CROSS_PAPER" in response_text:
            return QuestionType.CROSS_PAPER
        else:
            # Default fallback logic
            return self._fallback_classification(question, paper_count)
    
    def _fallback_classification(self, question: str, paper_count: int) -> QuestionType:
        """Fallback classification using keyword matching"""
        question_lower = question.lower()
        
        # Keywords that typically indicate cross-paper questions
        cross_paper_keywords = [
            "compare", "comparison", "difference", "differ", "vs", "versus",
            "better", "best", "worse", "superior", "inferior",
            "rank", "ranking", "order", "which", "what are the differences",
            "how do they differ", "similarities and differences",
            "contrast", "contradicts", "conflicts", "agrees", "disagrees"
        ]
        
        # Keywords that typically indicate individual questions
        individual_keywords = [
            "what are", "what is", "describe", "explain", "summarize",
            "list", "identify", "extract", "find", "show me",
            "tell me about", "what does", "how does"
        ]
        
        # Check for cross-paper indicators
        for keyword in cross_paper_keywords:
            if keyword in question_lower:
                return QuestionType.CROSS_PAPER
        
        # Check for individual indicators
        for keyword in individual_keywords:
            if keyword in question_lower:
                return QuestionType.INDIVIDUAL
        
        # Default to cross-paper for multiple papers
        return QuestionType.CROSS_PAPER


class PaperContentLoader:
    """Loads paper content from stored markdown files"""
    
    def __init__(self, user_id: str, kb_id: str, where: str = "ms"):
        self.user_id = user_id
        self.kb_id = kb_id
        self.where = where
        self.data_path = Path(get_data_path())
        self.logger = logging.getLogger("paper_loader")
    
    def load_paper_content(self, paper_id: str) -> Optional[PaperContent]:
        """Load full paper content from markdown file"""
        try:
            # Try different possible paths for the markdown file
            possible_paths = [
                self.data_path / self.user_id / self.kb_id / self.where / paper_id / f"{paper_id}.md",
                # self.data_path / self.user_id / self.kb_id / self.where / paper_id / "output.md",
                # self.data_path / self.user_id / self.kb_id / self.where / paper_id / "content.md"
            ]
            
            for path in possible_paths:
                if path.exists():
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Extract title from content if possible
                    title = self._extract_title_from_content(content, paper_id)
                    
                    return PaperContent(
                        paper_id=paper_id,
                        title=title,
                        content=content,
                        metadata={
                            "file_path": str(path),
                            "content_length": len(content)
                        }
                    )
            
            self.logger.warning(f"Could not find markdown content for paper: {paper_id}")
            return None
            
        except Exception as e:
            self.logger.error(f"Error loading paper {paper_id}: {e}")
            return None
    
    def load_multiple_papers(self, paper_ids: List[str]) -> List[PaperContent]:
        """Load content for multiple papers"""
        papers = []
        for paper_id in paper_ids:
            paper_content = self.load_paper_content(paper_id)
            if paper_content:
                papers.append(paper_content)
            else:
                self.logger.warning(f"Failed to load paper: {paper_id}")
        
        return papers
    
    def _extract_title_from_content(self, content: str, paper_id: str) -> str:
        """Extract title from markdown content"""
        lines = content.split('\n')
        
        # Look for title patterns
        for line in lines[:20]:  # Check first 20 lines
            line = line.strip()
            if line.startswith('# ') and len(line) > 2:
                return line[2:].strip()
            elif line.startswith('## ') and len(line) > 3 and 'title' in line.lower():
                return line[3:].strip()
        
        # If no title found, use paper_id
        return paper_id #.replace('_', ' ').title()


class LargeContextQAEngine:
    """Main QA engine using large context windows"""
    
    def __init__(self, user_id: str, kb_id: str, where: str = "ms"):
        self.user_id = user_id
        self.kb_id = kb_id
        self.where = where
        
        self.classifier = QuestionTypeClassifier()
        self.loader = PaperContentLoader(user_id, kb_id, where)
        self.logger = logging.getLogger("large_context_qa")
        
        # LLM configuration
        self.llm_config = get_llm_config_for_module("LargeContextQA")
    
    def answer_question(self, question: str, paper_ids: List[str]) -> QAResult:
        """Main method to answer questions using large context"""
        
        # Load paper contents
        papers = self.loader.load_multiple_papers(paper_ids)
        if not papers:
            return QAResult(
                question=question,
                question_type=QuestionType.SINGLE_PAPER,
                papers_involved=paper_ids,
                answer="No paper content could be loaded for the specified papers.",
                metadata={"error": "Failed to load paper content"}
            )
        
        # Classify question type
        question_type = self.classifier.classify_question(question, len(papers))
        
        self.logger.info(f"Processing {question_type.value} question for {len(papers)} papers")
        
        # Route to appropriate handler
        if question_type == QuestionType.INDIVIDUAL:
            return self._handle_individual_question(question, papers)
        elif question_type == QuestionType.CROSS_PAPER:
            return self._handle_cross_paper_question(question, papers)
        else:  # SINGLE_PAPER
            return self._handle_single_paper_question(question, papers[0])
    
    def _handle_single_paper_question(self, question: str, paper: PaperContent) -> QAResult:
        """Handle questions for a single paper"""
        
        prompt = '''
        You are an expert research assistant analyzing academic papers. Answer the user's question based on the provided paper content.

        <Paper Title> {title} <End of Paper Title>
        <Paper ID>{paper_id}<End of Paper ID>

        <Paper Content>
        {content}
        <End of Paper Content>

        <User Question> {question} <End of User Question>

        **Instructions:**
        1. Read through the entire paper content carefully
        2. Answer the question based solely on the information in the paper
        3. Be specific and cite relevant sections when possible
        4. If the information is not available in the paper, state this clearly
        5. Provide a comprehensive but concise answer

        **Answer:**
        '''
        
        # Check content length and truncate if necessary
        max_content_length = 100000  # Adjust based on your model's context limit
        content = paper.content
        if len(content) > max_content_length:
            content = content[:max_content_length] + "\n\n[Content truncated due to length...]"
            self.logger.warning(f"Truncated content for paper {paper.paper_id}")
        
        llm = ChatOpenAI(
            model=self.llm_config["default_model"],
            openai_api_base=self.llm_config["base_url"],
            openai_api_key=self.llm_config["api_key"],
            temperature=0.3,
            max_tokens=2000
        )
        
        formatted_prompt = prompt.format(
            title=paper.title,
            paper_id=paper.paper_id,
            content=content,
            question=question
        )
        
        response = llm.invoke(formatted_prompt)
        answer = response.content if hasattr(response, 'content') else str(response)
        
        return QAResult(
            question=question,
            question_type=QuestionType.SINGLE_PAPER,
            papers_involved=[paper.paper_id],
            answer=answer,
            metadata={
                "paper_title": paper.title,
                "content_length": len(content),
                "was_truncated": len(paper.content) > max_content_length
            }
        )
    
    def _handle_individual_question(self, question: str, papers: List[PaperContent]) -> QAResult:
        """Handle questions that should be answered individually for each paper"""
        
        individual_answers = {}
        
        # Answer for each paper individually
        for paper in papers:
            result = self._handle_single_paper_question(question, paper)
            individual_answers[paper.paper_id] = result.answer
        
        # Combine individual answers
        # combined_prompt = '''
        # You have received individual answers to the question "{question}" for multiple research papers. 
        
        # **Individual Answers:**
        # {individual_answers}
        
        # **Task:**
        # Synthesize these individual answers into a well-structured, comprehensive response that:
        # 1. Organizes the information clearly by paper
        # 2. Highlights common themes and differences
        # 3. Provides a coherent overall summary
        # 4. Maintains the specific details from each paper
        
        # **Synthesized Answer:**
        # '''
        
        # # Format individual answers
        # answers_text = ""
        # for paper_id, answer in individual_answers.items():
        #     paper_title = next((p.title for p in papers if p.paper_id == paper_id), paper_id)
        #     answers_text += f"\n<Paper Title> {paper_title} ({paper_id}) <End of Paper Title> : \n <Answer>\n{answer} </End of Answer>\n"
        
        # llm = ChatOpenAI(
        #     model=self.llm_config["default_model"],
        #     openai_api_base=self.llm_config["base_url"],
        #     openai_api_key=self.llm_config["api_key"],
        #     temperature=0.3,
        #     max_tokens=3000
        # )
        
        # synthesis_prompt = combined_prompt.format(
        #     question=question,
        #     individual_answers=answers_text
        # )
        
        # response = llm.invoke(synthesis_prompt)
        # synthesized_answer = response.content if hasattr(response, 'content') else str(response)
        
        return QAResult(
            question=question,
            question_type=QuestionType.INDIVIDUAL,
            papers_involved=[p.paper_id for p in papers],
            answer="",
            individual_answers=individual_answers,
            metadata={
                "papers_count": len(papers),
                "synthesis_method": "individual_then_combine"
            }
        )
    
    def _handle_cross_paper_question(self, question: str, papers: List[PaperContent]) -> QAResult:
        """Handle questions that require cross-paper analysis"""
        
        # Calculate content limits per paper
        # max_total_length = 150000  # Adjust based on model limits
        # max_length_per_paper = max_total_length // len(papers)
        
        # Prepare combined content
        combined_content = ""
        paper_info = []
        
        i = 0
        for paper in papers:
            content = paper.content
            # if len(content) > max_length_per_paper:
            #     content = content[:max_length_per_paper] + "\n[Truncated...]"
            
            combined_content += f"\n<Start of Paper {i}>\n<Paper Title> {paper.title} (ID: {paper.paper_id}) <End of Paper Title>\n"
            combined_content += '<Paper Content>' + content + "\n" + '<End of Paper Content>' + "\n" + '<End of Paper {i}>\n'
            
            paper_info.append({
                "id": paper.paper_id,
                "title": paper.title,
                "was_truncated": False
            })
        
        prompt = '''
        You are an expert research assistant analyzing multiple academic papers simultaneously. Answer the user's question by comparing and analyzing all the provided papers together.

        **Papers to Analyze:**
        {paper_list}

        **All Paper Contents:**
        {combined_content}

        **User Question:** {question}

        **Instructions:**
        1. Analyze all papers simultaneously to answer the question
        2. Make direct comparisons between papers when relevant
        3. Highlight similarities and differences
        4. Provide specific examples and citations from the papers
        5. Structure your answer clearly with proper headings if needed
        6. If comparing, be fair and objective in your analysis

        **Cross-Paper Analysis:**
        '''
        
        # Format paper list
        paper_list_text = "\n".join([f"- {info['title']} (ID: {info['id']})" for info in paper_info])
        
        llm = ChatOpenAI(
            model=self.llm_config["default_model"],
            openai_api_base=self.llm_config["base_url"],
            openai_api_key=self.llm_config["api_key"],
            temperature=0.3,
            max_tokens=4000
        )
        
        formatted_prompt = prompt.format(
            paper_list=paper_list_text,
            combined_content=combined_content,
            question=question
        )
        
        response = llm.invoke(formatted_prompt)
        answer = response.content if hasattr(response, 'content') else str(response)
        
        return QAResult(
            question=question,
            question_type=QuestionType.CROSS_PAPER,
            papers_involved=[p.paper_id for p in papers],
            answer=answer,
            metadata={
                "papers_count": len(papers),
                "total_content_length": len(combined_content),
                "paper_info": paper_info,
                "analysis_method": "simultaneous_cross_paper"
            }
        )
        
        
# if __name__ == "__main__":
#     logging.basicConfig(level=logging.INFO)
    
#     # Example usage
#     user_id = "8b392d82-81dc-4a6e-8fe3-03984cb78ffe"
#     kb_id = "afea9a91-2369-4e36-8637-f0dd9675b740"
#     where = "ms"
    
#     qa_engine = LargeContextQAEngine(user_id, kb_id, where)
    
#     question = "Does the experimental results in these papers support the claims made in their introduction?"
#     # question = "Compare the methodologies proposed in these papers and analyze their relative effectiveness."
#     paper_ids = ["FLAT"]
#     import time
#     s = time.time()
#     result = qa_engine.answer_question(question, paper_ids)
#     e = time.time()
#     print(f"Time taken: {e - s:.2f} seconds")
    
#     print("Question:", result.question)
#     print("Question Type:", result.question_type.value)
#     print("Papers Involved:", result.papers_involved)
#     print("Answer:\n", result.answer)
#     if result.individual_answers:
#         print("\nIndividual Answers:")
#         for pid, ans in result.individual_answers.items():
#             print(f"- {pid}: {ans}\n")
#     print("Metadata:", result.metadata)