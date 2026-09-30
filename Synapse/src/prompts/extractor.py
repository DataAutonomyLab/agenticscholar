from src.prompts.base import run_structured_prompt 

def extract_exp_settings(section_text):
    return run_structured_prompt("1_extract_experimental_settings.yaml", {
        "section_text": section_text
    })
    
def extract_exp_settings_datasets(section_text):
    return run_structured_prompt("1_1_extract_experimental_settings-datasets.yaml", {
        "section_text": section_text
    })

def extract_exp_settings_metrics(section_text):
    return run_structured_prompt("1_2_extract_experimental_settings-mertrics.yaml", {
        "section_text": section_text
    })

def extract_exp_settings_baselines(section_text):
    return run_structured_prompt("1_3_extract_experimental_settings-baselines.yaml", {
        "section_text": section_text
    })

def extract_exp_settings_setup(section_text):
    return run_structured_prompt("1_4_extract_experimental_settings-setup.yaml", {
        "section_text": section_text
    })

def extract_comp_baselines(section_text):
    return run_structured_prompt("2_extract_comparison_baselines.yaml", {
        "section_text": section_text
    }, str_type="MARKDOWN_T")

def extract_parameter_study(section_text):
    return run_structured_prompt("3_extract_parameter_study.yaml", {
        "section_text": section_text
    }, str_type="MARKDOWN_T")

def extract_ablation_study(section_text):
    return run_structured_prompt("4_extract_ablation_study.yaml", {
        "section_text": section_text
    }, str_type="MARKDOWN_T")

def extract_problem_def(section_text):
    return run_structured_prompt("5_extract_problem_definition.yaml", {
        "section_text": section_text
    }, str_type="MARKDOWN_T")

def extract_problem_def_input(section_text):
    return run_structured_prompt("5_1_extract_problem_definition-input.yaml", {
        "section_text": section_text
    }, str_type="MARKDOWN_T")
    
def extract_problem_def_output(section_text):
    return run_structured_prompt("5_2_extract_problem_definition-output.yaml", {
        "section_text": section_text
    }, str_type="MARKDOWN_T")

def extract_problem_def_goal(section_text):
    return run_structured_prompt("5_3_extract_problem_definition-goal.yaml", {
        "section_text": section_text
    }, str_type="MARKDOWN_T")


def extract_method(methodology_text):
    return run_structured_prompt("6_extract_methodv2.yaml", {
        "methodology_text": methodology_text
    })