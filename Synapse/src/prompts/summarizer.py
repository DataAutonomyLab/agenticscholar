from src.prompts.base import run_structured_prompt

def summarize_common_settings(setting_jsons):
    # print(f"Summarizing common settings: {setting_jsons}")
    return run_structured_prompt("13_summarize_common_settings.yaml", {
        "setting_jsons": setting_jsons
    })

def summarize_missing_settings(setting_jsons):
    # print(f"Summarizing missing settings: {setting_jsons}")
    return run_structured_prompt("7_summarize_missing_settings.yaml", {
        "setting_jsons": setting_jsons
    })

def check_inconsistencies_metrics(section_text):
    # print(f"Checking inconsistencies in metrics: {section_text}")
    return run_structured_prompt("12_check_inconsistencies_metrics.yaml", {
        "section_text": section_text
    })

def rank_exp_results_cross_papers(base_comparison_summaries, paper_settings, common_settings):
    # print(f"Ranking experimental results across papers: {exp_results}")
    return run_structured_prompt("16_rank_methods_dataset_metric.yaml", {
        "base_comparison_summaries": base_comparison_summaries,
        "paper_settings": paper_settings,
        "common_settings": common_settings
    })

def check_inconsistencies_cross_papers(base_comparison_summaries, paper_settings, common_settings):
    # print(f"Ranking experimental results across papers: {exp_results}")
    return run_structured_prompt("17_check_inconsistencies_results_dataset_metric.yaml", {
        "base_comparison_summaries": base_comparison_summaries,
        "paper_settings": paper_settings,
        "common_settings": common_settings
    })

def rank_datasets(section_text):
    # print(f"Ranking dataset: {section_text}")
    return run_structured_prompt("10_rank_datasets.yaml", {
        "section_text": section_text
    })

def rank_variants(section_text):
    # print(f"Ranking variants: {section_text}")
    return run_structured_prompt("9_rank_variants_method.yaml", {
        "section_text": section_text
    }, str_type="MARKDOWN_T")

def summarize_parameter_impact(section_text):
    # print(f"Summarizing parameter impact: {section_text}")
    return run_structured_prompt("8_summarize_impact_parameters.yaml", {
        "section_text": section_text
    }, str_type="MARKDOWN_T")

def summarize_problem_def_diff(problem_summaries):
    # print(f"Summarizing problem definition differences: {problem_summaries}")
    return run_structured_prompt("15_summarize_differences_problem_definition.yaml", {
        "problem_summaries": problem_summaries
    }, str_type="MARKDOWN_T")

def summarize_methods_pros_cons(method_summaries):
    # print(f"Summarizing methods pros and cons: {method_summaries}")
    return run_structured_prompt("14_summarize_pros_cons_methods.yaml", {
        "method_summaries": method_summaries
    }, str_type="MARKDOWN_T")