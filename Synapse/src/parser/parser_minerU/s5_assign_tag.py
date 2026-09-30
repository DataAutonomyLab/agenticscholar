from src.synapse_utils import get_data_path

prompt_tag = '''
[ROLE DESCRIPTION]
You are an AI assistant skilled in analyzing the structure and content of scientific research papers. Your task is to categorize sections based on their primary and significant secondary functions related to the problem, method, or experiments, using both the section's title and content, and applying specific constraints.

[TASK DESCRIPTION]
Your task is to read the provided text section and its title from a computer science research paper. Assign **up to three relevant labels** to it from the list: `Problem Definition`, `Method`, `Experiment`, `Related Work`, `Introduction`. The label(s) should reflect the section's primary and potentially a significant secondary purpose, determined by analyzing the content in the context provided by the title, and adhering to the specific constraints for *all* labels.

[INPUT]
- **Section Title:** `{section_title}` - A string containing the title of the section (e.g., "1 Introduction", "3 Method", "5.1 Experimental Setup", "9 CONCLUSION").
- **Section Text:** `{section_text}` - A string containing the text content of the section.

[LABELS AND DEFINITIONS]
Here is the exclusive list of possible labels and their definitions with constraints:
* **Problem Definition:** The section's content significantly focuses on describing the challenge the paper addresses. This includes defining the scope, motivation, importance, inputs, desired outputs, or constraints of the problem being tackled.
    * **Constraint:** **Do NOT assign this label** if the section's primary function and content resemble a **Conclusion** (e.g., summarizing overall findings, discussing limitations/impact, suggesting future work, often indicated by titles like "Conclusion", "Summary").
    **Must** assign Problem Definition to the section if the section title indicates "Problem Definition" or "Introduction" or similar, while we still can include other tags.**
* **Method:** The section's content significantly focuses on explaining the proposed solution. This **must include either a high-level overview (core idea, intuition) OR technical details** (algorithms, architecture, mathematical formulations, theoretical analysis, system design) of the approach developed or used by the authors.
    * **Constraint:** **Do NOT assign this label** if the section's primary focus is:
        * Merely mentioning the method by name or using it without explaining how it works.
        * Summarizing the paper's overall findings, discussing limitations, or suggesting future work (**Conclusion-like** content, often indicated by titles like "Conclusion", "Discussion").
        * Reviewing, comparing, or critiquing prior research publications by other authors (**Related Work-like** content, often indicated by titles like "Related Work").
* **Experiment:** The section's content significantly focuses on detailing the empirical evaluation of the method. This **must include substantive details** about the experimental setup (e.g., datasets, metrics, baselines, implementation details, hyperparameters) OR the presentation and analysis of results (e.g., tables, figures, performance outcomes, comparisons, interpretation of results).
    * **Constraint:** **Do NOT assign this label** if:
        * The section only briefly mentions that experiments were conducted without providing substantive details.
        * The section's primary function and content resemble an **Introduction** (e.g., setting context, motivating the problem, outlining paper structure, often indicated by titles like "Introduction"), even if experiments are mentioned or results hinted at.
* **Introduction:** The section's content significantly focuses on the overview of this the paper. This typically includes motivating the problem, providing background context, highlighting the importance of the research area, outlining contributions, and/or describing the structure of the paper.
    * If section title indicates "Introduction" or similar, please **MUST** add Introduction into the final tag list while we still can include other tags.
* **Related Work:** The section's content significantly focuses on reviewing, comparing, or critiquing prior research publications by other authors. This includes describing existing methods, highlighting differences, identifying gaps, or situating the current work within the broader research landscape.
    * **Constraint:** **Do NOT assign this label** if the section primarily:
        * Explains the authors' own proposed method (→ Method).
        * Describes the paper's problem scope, motivation, or objectives (→ Problem Definition or Introduction).
        * Summarizes contributions or discusses impact/limitations/future work (→ Conclusion-like).
    * If section title indicates "Related Work" or similar, please **MUST** add Related Work into the final tag list while we still can include other tags.

[INSTRUCTIONS]
1.  **Analyze Title and Content:** Carefully examine the **Section Title** and read the **Section Text**. Use the title as a strong indicator of the section's intended primary function. Analyze the text content for specific details, structure, emphasis, and characteristics (e.g., defining terms, explaining algorithms, presenting results, summarizing findings, reviewing literature, setting context).
2.  **Evaluate Against Labels & Constraints (Initial Check):** Compare the primary and secondary content/purposes against the positive definitions for `Problem Definition`, `Method`, and `Experiment`.
3.  **Apply Problem Definition Constraint:** If considering the `Problem Definition` label (primary or secondary), explicitly check if the section's primary function/content strongly resembles a **Conclusion** (summarizing findings, impact, future work, etc., often indicated by title). If yes, **do not assign `Problem Definition`**.
4.  **Apply Method Constraint:** If considering the `Method` label (primary or secondary):
    * Verify the *content* provides a high-level overview OR technical details of the proposed method itself.
    * Explicitly check that the section's primary focus is NOT merely mentioning the method, **Conclusion-like**, or **Related Work-like** (use title and content characteristics). If it is primarily one of these excluded functions, **do not assign `Method`**.
5.  **Apply Experiment Constraint:** If considering the `Experiment` label (primary or secondary):
    * Verify the *content* meets the requirement for **substantive details** (setup or results/analysis).
    * Explicitly check if the section's primary function/content strongly resembles an **Introduction** (setting context, motivating, outlining structure, etc., often indicated by title). If yes, **do not assign `Experiment`**.
6.  **Select One, Two, or Three Valid Labels:**
    * Based on the analysis and *after applying all constraints* (Steps 3, 4, 5), identify the label(s) that best describe the section's valid primary and potentially significant secondary function(s).
    * Prioritize the primary function. Add a secondary label only if it represents a distinct, significant, and *valid* secondary function according to the definitions and constraints.
    * **Do not select more than three labels in total.**
7.  **Handle Non-Matches:** If, after applying all constraints, the section does not significantly align with any *valid* interpretation of `Problem Definition`, `Method`, or `Experiment`, output `None`. This includes sections clearly functioning as Introduction, Conclusion, Related Work, Background, Abstract, References, Acknowledgments, etc., based on title and content.
8.  **Output Selected Labels:** Format the output based on the number of selected valid labels:
    * If **one** valid label is selected, output just that label name.
    * If **two** or **three** valid labels are selected, output them as a comma-separated string.
    * If **no** valid labels are selected, output `None`.

[OUTPUT]
- Provide the selected label(s) as a **single string**: no more than three labels names separated by a comma and space, or the word `None`.
- Output only the label names exactly as specified or `None`. Do not add any other text, explanation, or formatting.
'''


from langchain_openai import ChatOpenAI
import yaml
from pathlib import Path
from langchain_core.prompts import PromptTemplate
import re
import json

from src.config.config import get_llm_config_for_module


local_config = get_llm_config_for_module("TagAssignment")
llm = ChatOpenAI(
    model=local_config["default_model"],
    openai_api_base=local_config["base_url"],
    openai_api_key=local_config["api_key"],
    temperature=0.3
)

def assign_tag(user_id: str, kb_name: str, paper_name: str, where: str = "ms"):
    # json_path = f"{get_data_path()}/{user_id}/{kb_name}/{where}/{paper_name}/{paper_name}_structured.json"
    json_path = get_data_path() / user_id / kb_name / where / paper_name / f"{paper_name}_structured.json"
    with open(json_path, "r", encoding="utf-8") as f:
        sections = json.load(f)
    prompt = PromptTemplate.from_template(prompt_tag)
    chain = prompt | llm
    for section in sections:
        variables = {
            "section_text": section["section_content"],
            "section_title": section["section_title"]
        }
        response = chain.invoke(variables)
        response_text = response.content if hasattr(response, "content") else str(response)
        if response_text == "None":
            continue
        response_text = response_text.replace(", ", ",")
        tags = response_text.split(",")
        section["section_tags"] = tags
        # print(tags)
        # print(f"Section: {section['section_title']}, Labels: {response_text}")
    new_path = get_data_path() / user_id / kb_name / where / paper_name / f"{paper_name}_structured.json"
    with open(new_path, "w", encoding="utf-8") as f:
        json.dump(sections, f, indent=4, ensure_ascii=False)