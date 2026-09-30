prompt_title = '''
# System
You are an expert technical editor. Given a linear list of paper headings (mix of paper title, section titles, and subsection titles), extract the **first-level section titles** (i.e., the main sections directly under the paper title). The number of leading `#` characters is **not** reliable and must **not** be used as the sole signal.

# Rules
1. **Exclude the paper title** (the very first, global title of the paper).
2. **Identify first-level sections semantically**, not by `#` count. A first-level section is a broad umbrella that other headings logically fall under.
3. Common first-level sections include (non-exhaustive, case-insensitive, variations allowed):
   - Abstract
   - Introduction / Overview / Motivation
   - Background / Preliminary / Preliminaries
   - Related Work / Literature Review
   - Method / Methods / Methodology / Approach / Model
   - Experiments / Evaluation / Empirical Study / Results
   - Discussion / Analysis / Limitations / Broader Impact / Ethics Statement
   - Conclusion / Concluding Remarks / Summary / Future Work (if it's a stand-alone top section)
   - Acknowledgments / Acknowledgements
4. **Demote typical experiment subsections** (e.g., Datasets, Experimental Setup/Details, Results & Analysis, Ablations, Parameter Sensitivity, Efficiency) **under** the umbrella “Experiments/Evaluation/Results” if that umbrella exists. Include only the umbrella as first-level.
5. **Order**: preserve the order of appearance in the input list.
6. **Deduplicate** semantically equivalent headings (e.g., “Introduction” and “Overview” both appear—keep the first that serves as the umbrella).
7. **Ignore appendices, references, supplementary, and footers** unless the paper explicitly treats them as main sections.
8. **Output format**: a **JSON array of strings**, each string being the **original heading text** exactly as it appears in the input (including its leading `#`s and punctuation). Output nothing else.
9. **Ignore Markdown Syntax for Hierarchy**: Do not rely solely on the number of '#' characters to determine the hierarchy. A title's meaning and its typical placement in a paper's structure are more important than the markdown.
10. **Exclude the Paper Title**: The main title of the paper (usually the very first item) must be excluded from the output.
11. **Exclude All Subsections**: Subsections are titles that logically fall under a first-level section. For example, "Datasets," "Experimental Details," and "Ablation Study" are nearly always subsections of a main "Experiments" section and must be excluded. Similarly, titles describing specific parts of a model, like "Encoder" or "Attention Mechanism," are typically subsections of "Methodology" and must be excluded.

# Edge Cases
- If there is no explicit “Experiments/Evaluation/Results” umbrella, but only subsections like “Datasets”, “Experimental Details”, etc., **promote the best umbrella candidate** among them (choose the broadest/most comprehensive, e.g., “Results and Analysis” over “Datasets”).
- If both “Conclusion” and “Future Work” are separate and parallel, include both; if “Future Work” is clearly a subsection of “Conclusion”, include only “Conclusion”.
- If “Ethics Statement” or “Broader Impact” appear, treat them as first-level if they stand alone.

# Input
A JSON array of headings (strings) in reading order: {title_list}

# Output
A JSON array of the first-level section titles (strings), preserving original text.


# Example
**Input**
```json
[
  "# Informer: Beyond Efficient Transformer for Long Sequence Time-Series Forecasting",
  "#### Abstract",
  "## Introduction",
  "## Preliminary",
  "## Methodology",
  "## Efficient Self-attention Mechanism",
  "## Encoder: Allowing for Processing Longer Sequential Inputs under the Memory Usage Limitation",
  "## Decoder: Generating Long Sequential Outputs Through One Forward Procedure",
  "## Experiment",
  "## Datasets",
  "## Experimental Details",
  "## Results and Analysis",
  "## Parameter Sensitivity",
  "## Ablation Study: How well Informer works?",
  "## Computation Efficiency",
  "## Conclusion",
  "## Acknowledgments",
  "## Ethics Statement"
]
```

**Output**
```json
[
  "#### Abstract",
  "## Introduction",
  "## Preliminary",
  "## Methodology",
  "## Experiment",
  "## Conclusion",
  "## Acknowledgments",
  "## Ethics Statement"
]
```
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

def generate_section_title(title_list):
    # json_path = f"{get_data_path()}/{user_id}/{kb_name}/{where}/{paper_name}/{paper_name}_structured.json"
    # print('title_list:', title_list)
    prompt = PromptTemplate.from_template(prompt_title)
    chain = prompt | llm
    variables = {
        "title_list": json.dumps(title_list)
    }
    response = chain.invoke(variables)
    response_text = response.content if hasattr(response, "content") else str(response)
    match = re.search(r"```(?:json)?\s*(.*?)```", response_text, re.DOTALL)
    json_str = match.group(1) if match else response_text.strip()
    try:
        answer =  json.loads(json_str)
        # print
        # print(answer)# return {"subquestions": subqs, "answers": [], "current_q_index": 0}
        return answer
    except json.JSONDecodeError:
        print("Error parsing JSON from response:")
        print(json_str)
        raise
    except Exception as e:
        print("Unexpected error while parsing JSON:")
        print(str(e))
        print("Raw response:", json_str)
        # Also fall back to default    

