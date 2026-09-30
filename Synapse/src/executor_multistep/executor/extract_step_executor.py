from enum import Enum
from typing import Any, Dict, List
from src.executor_multistep.executor.plan_step import ExecutorType, ResearchStep, StepExecutor, StepResult, try_dummy, try_experiment, try_method, try_problem_def
from src.prompts.base import run_structured_prompt
from src.prompts.extractor import extract_ablation_study, extract_comp_baselines, extract_exp_settings, extract_exp_settings_baselines, extract_exp_settings_datasets, extract_exp_settings_metrics, extract_exp_settings_setup, extract_method, extract_parameter_study, extract_problem_def, extract_problem_def_goal, extract_problem_def_input, extract_problem_def_output

class ExtractType(Enum):
    EXP_SETTINGS = {
        "name": "extract_exp_settings",
        "description": "Extracts key experimental details, including datasets, baselines, metrics, and setup.",
        "mode": "local",
        "handler": try_experiment
    }
    EXP_SETTINGS_DATASETS = {
        "name": "extract_exp_settings_datasets",
        "description": "Extracts only dataset-related details such as dataset names, sources, and statistics.",
        "mode": "local",
        "handler": try_experiment
    }
    EXP_SETTINGS_METRICS = {
        "name": "extract_exp_settings_metrics",
        "description": "Extracts only evaluation metrics and their definitions used in experiments.",
        "mode": "local",
        "handler": try_experiment
    }
    EXP_SETTINGS_BASELINES = {
        "name": "extract_exp_settings_baselines",
        "description": "Extracts only baseline methods used for comparison.",
        "mode": "local",
        "handler": try_experiment
    }
    EXP_SETTINGS_SETUP = {
        "name": "extract_exp_settings_setup",
        "description": "Extracts only experimental environment and setup information (hardware, software, etc.).",
        "mode": "local",
        "handler": try_experiment
    }
    EXP_COMP_BASELINES = {
        "name": "extract_comp_baselines",
        "description": "Extracts and formats comprehensive performance comparisons across all methods.",
        "mode": "local",
        "handler": try_experiment
    }
    EXP_PARAMETER_STUDY = {
        "name": "extract_parameter_study",
        "description": "Extracts parameter study details and how different parameter values affect results.",
        "mode": "local",
        "handler": try_experiment
    }
    EXP_ABLATION_STUDY = {
        "name": "extract_ablation_study",
        "description": "Extracts ablation study data showing the contribution of each model component.",
        "mode": "local",
        "handler": try_experiment
    }
    PROBLEM_DEF = {
        "name": "extract_problem_def",
        "description": "Extracts the overall problem definition and its key components.",
        "mode": "local",
        "handler": try_problem_def
    }
    PROBLEM_DEF_INPUT = {
        "name": "extract_problem_def_input",
        "description": "Extracts only the input description of the defined problem.",
        "mode": "local",
        "handler": try_problem_def
    }
    PROBLEM_DEF_OUTPUT = {
        "name": "extract_problem_def_output",
        "description": "Extracts only the output description of the defined problem.",
        "mode": "local",
        "handler": try_problem_def
    }
    PROBLEM_DEF_GOAL = {
        "name": "extract_problem_def_goal",
        "description": "Extracts only the goal or objective of the defined problem.",
        "mode": "local",
        "handler": try_problem_def
    }
    METHOD = {
        "name": "extract_method",
        "description": "Extracts research methods and describes their mechanisms, strengths, and weaknesses.",
        "mode": "local",
        "handler": try_method
    }
    DEFAULT = {
        "name": "default",
        "description": "Extracts information matching the given extraction query",
        "mode": "local | global",
        "handler": try_dummy
    }

    @classmethod
    def from_str(cls, s: str) -> "ExtractType | None":
        value_to_member = {member.value["name"]: member for member in cls}
        return value_to_member.get(s)

def extract_information(content: str, description: str, format_instruction: str) -> str:
    return run_structured_prompt(
        template_name = "extract_information.yaml",
        variables= {
            "extraction_query": description,
            "content": content,
            "format_instructions": format_instruction
        },
        is_reserch=True
    )

class ExtractStepExecutor(StepExecutor):
    """Executor for extraction steps"""

    extract_type: ExtractType

    def __init__(self, db_name: str, step: ResearchStep, target_paper: str):
        super().__init__(db_name, step, target_paper)
        self.executor_type = ExecutorType.EXTRACT
        type_str = step.handler_type if step.handler_type is not None else "default"
        self.extract_type = ExtractType.from_str(type_str)
        if self.extract_type is None:
            print(f"[Error]No ExtractStepExecutor registered for type {type_str}, fallback to default")
            self.extract_type = ExtractType.DEFAULT
        
    def execute(self, context: Dict[str, Any]) -> StepResult:
        inputs = self.get_inputs(context)
        if self.extract_type == ExtractType.DEFAULT:
            # content = self.get_content(context)
            result = extract_information(inputs, 
                                        self.step.parameters.get('extraction_query', self.step.description),
                                        self.step.parameters.get('format', 'bullet_points'))
        else:
            result = self.execute_internal(inputs)

        return StepResult(
            step_id=self.step.id,
            success=True,
            result=result,
        )
        
    def execute_internal(self, inputs: List) -> str:
        map_func = {
            ExtractType.EXP_SETTINGS: extract_exp_settings,
            ExtractType.EXP_SETTINGS_DATASETS: extract_exp_settings_datasets,
            ExtractType.EXP_SETTINGS_METRICS: extract_exp_settings_metrics,
            ExtractType.EXP_SETTINGS_BASELINES: extract_exp_settings_baselines,
            ExtractType.EXP_SETTINGS_SETUP: extract_exp_settings_setup,
            ExtractType.EXP_COMP_BASELINES: extract_comp_baselines,
            ExtractType.EXP_PARAMETER_STUDY: extract_parameter_study,
            ExtractType.EXP_ABLATION_STUDY: extract_ablation_study,
            ExtractType.PROBLEM_DEF: extract_problem_def,
            ExtractType.PROBLEM_DEF_INPUT: extract_problem_def_input,
            ExtractType.PROBLEM_DEF_OUTPUT: extract_problem_def_output,
            ExtractType.PROBLEM_DEF_GOAL: extract_problem_def_goal,
            ExtractType.METHOD: extract_method
        }
        handler = map_func[self.extract_type]
        return handler(*inputs)

    # def get_content(self, context: Dict[str, Any]):
    #     # Retrieve relevant sections
    #     content = self.retrieve_sections(
    #         self.step.target_papers, 
    #         self.step.target_sections,
    #         self.step.parameters.get('search_query')
    #     )
    #     combined_content = "\n".join(content)
    #     return combined_content