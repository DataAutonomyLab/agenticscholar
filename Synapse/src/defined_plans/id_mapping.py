_id2file = {
    0: "plan_general_question_single.yaml",
    1: "plan_extract_experimental_settings.yaml",
    2: "plan_extract_comp_baselines.yaml",
    3: "plan_extract_parameter_study.yaml",
    4: "plan_extract_ablation_study.yaml ",
    5: "plan_extract_problem_def.yaml",
    6: "plan_extract_method.yaml",
    7: "plan_summarize_missing_settings.yaml",
    8: "plan_summarize_parameter_impact.yaml",
    9: "plan_rank_variants.yaml",
    10: "plan_rank_datasets.yaml",
    11: "plan_check_inconsistencies_cross_papers.yaml",
    12: "plan_check_inconsistencies_metrics.yaml",
    13: "plan_summarize_common_settings.yaml",
    14: "plan_summarize_methods_pros_cons.yaml",
    15: "plan_summarize_problem_def_diff.yaml",
    16: "plan_rank_exp_results_cross_papers.yaml",
    17: "plan_check_inconsistencies_cross_papers.yaml",
    18: "plan_extract_experimental_datasets.yaml",
    19: "plan_extract_experimental_baselines.yaml",
    20: "plan_extract_experimental_metrics.yaml",
    21: "plan_extract_experimental_setup.yaml",
    22: "plan_extract_problem_def_input.yaml",
    23: "plan_extract_problem_def_output.yaml",
    24: "plan_extract_problem_def_goal.yaml",
}

def ID2File(id: int) -> str:
    """
    Convert an ID to its corresponding file name.

    Args:
        id (int): The ID to convert.

    Returns:
        str: The corresponding file name.
    """
    if id in _id2file:
        return _id2file[id]
    else:
        raise ValueError(f"ID {id} does not exist in the mapping.")