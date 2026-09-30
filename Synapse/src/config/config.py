import os
import json
from dotenv import load_dotenv
import src.synapse_utils

CONFIG_DIR = src.synapse_utils.get_config_path()

# Load secrets from the .env file into environment variables
load_dotenv()

def get_llm_config_for_module(module_name: str):
    """
    Loads configuration from config.json, finds the LLM assigned to the
    specified module, and returns its resolved configuration.

    Args:
        module_name (str): The name of the module (e.g., "ExecutorModule").

    Returns:
        dict: A dictionary containing the 'api_key' and 'default_model'.
    """
    with open(CONFIG_DIR / "config.json", 'r') as f:
        config_data = json.load(f)

    # 1. Find which LLM is assigned to the module
    assignments = config_data["module_assignments"]
    if module_name not in assignments:
        raise ValueError(f"Error: Module '{module_name}' is not defined in config.json module_assignments.")
    
    assigned_llm = assignments[module_name]

    # 2. Get the settings for that assigned LLM
    providers = config_data["llm_entries"]
    if assigned_llm not in providers:
        raise ValueError(f"Error: LLM provider '{assigned_llm}' is not defined in config.json llm_entries.")

    provider_config = providers[assigned_llm]
    
    # 3. Resolve the API key from environment variables
    api_key_env_var = provider_config["api_key_env"]
    provider_name = provider_config["provider"]
    base_url = provider_config["base_url"]
    api_key = os.getenv(api_key_env_var)

    if not api_key:
        raise ValueError(f"Error: API key variable '{api_key_env_var}' not found in .env file.")

    # 4. Return the final, resolved configuration for the module
    return {
        "provider": provider_name,
        "api_key": api_key,
        "default_model": provider_config["default_model"],
        "base_url": base_url
    }
    
# def test():
#     """
#     Test function to verify the configuration loading.
#     """
#     try:
#         config = get_llm_config_for_module("ExecutorModule")
#         print("Configuration loaded successfully:")
#         print(config)
#     except ValueError as e:
#         print(e)
        
# test()