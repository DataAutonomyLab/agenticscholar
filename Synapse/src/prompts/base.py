from typing import Any, Dict, Tuple
from langchain_openai import ChatOpenAI
import yaml
from pathlib import Path
from langchain_core.prompts import PromptTemplate
from langchain_community.callbacks import get_openai_callback
import re
import json
from src.config.config import get_llm_config_for_module

from google import genai

def load_prompt_template(name: str):
    path = Path(__file__).parent / "templates" / "new-version" / name
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def load_prompt_template_research(name: str):
    path = Path(__file__).parent / "templates" / "research" / name
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def run_structured_prompt(template_name: str, variables: dict, str_type = "MARKDOWN_T", LLM_Type='Executor', is_reserch=False, process=True)->Dict:
    if is_reserch:
        tpl = load_prompt_template_research(template_name)
    else:
        tpl = load_prompt_template(template_name)
    
    local_config = get_llm_config_for_module(LLM_Type)
    
    maximum_retries = 5
    last_error = None
    for attempt in range(maximum_retries):
        try:
            input_tokens = 0
            output_tokens = 0
            if local_config["provider"] == "gemini":
                prompt_string = tpl["prompt"]
                formatted_prompt = prompt_string.format(**variables)
                
                client = genai.Client(api_key=local_config["api_key"])

                response = client.models.generate_content(
                    model=local_config["default_model"],
                    contents=formatted_prompt) 
                response_text = response.text

                if hasattr(response, "usage_metadata"):
                    usage = response.usage_metadata
                    input_tokens = usage.get("prompt_token_count")
                    output_tokens = usage.get("candidates_token_count")

            elif local_config["provider"] == "openai":
                llm = ChatOpenAI(
                    model=local_config["default_model"],
                    openai_api_base=local_config["base_url"],
                    openai_api_key=local_config["api_key"],
                    temperature=0.3
                )

                prompt = PromptTemplate.from_template(tpl["prompt"])
                chain = prompt | llm
                # print("Before invoking ...")
                # try:
                with get_openai_callback() as cb:
                    response = chain.invoke(variables)
                # except Exception as e:
                #     print("Error during LLM invocation:", str(e))
                #     raise
                # print("After invoking ...")
                response_text = response.content if hasattr(response, "content") else str(response)
                # print("Full Response:", response)
                input_tokens = cb.prompt_tokens
                output_tokens = cb.completion_tokens
                
            else:
                raise ValueError(f"Unsupported provider: {local_config['provider']}")
            
            
            
            # print(f"Response Text: {response_text}")
            if not process:
                return {
                    "response": response,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens
                }

            if str_type == "JSON_T":
                match = re.search(r"```(?:json)?\s*(.*?)```", response_text, re.DOTALL)
                json_str = match.group(1) if match else response_text.strip()
                # try:
                answer =  json.loads(json_str)
                    # return {"subquestions": subqs, "answers": [], "current_q_index": 0}
                # except json.JSONDecodeError:
                #     print("Error parsing JSON from response:")
                #     print(json_str)
                #     raise
            elif str_type == "LATEX_T":
                match = re.search(r"```(?:latex)?\s*(.*?)```", response_text, re.DOTALL)
                answer = match.group(1) if match else response_text.strip()
            elif str_type == "MARKDOWN_T":
                match = re.search(r"```(?:markdown)?\s*(.*?)```", response_text, re.DOTALL)
                answer = match.group(1) if match else response_text.strip()
            else:
                raise ValueError("Unsupported response type")
            
            return {
                "response": answer,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens
            }
        except (json.JSONDecodeError, Exception) as e:
            # print(f"Attempt {attempt + 1} failed with error: {e}")
            last_error = e
            if attempt == maximum_retries - 1:
                print("Max retries reached. Raising the last error.")
                raise last_error
