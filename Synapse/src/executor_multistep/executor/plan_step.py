
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from enum import Enum
import json
from typing import Any, Dict, List, Optional
import yaml

class StepType(Enum):
    """Types of research steps that can be executed"""
    # semantic operators
    EXTRACT = "extract"           # Extract specific information from sections
    SUMMARIZE = "summarize"       # Summarize content from sections
    CHECK = "check"           # Compare information across sections/papers
    VERIFY = "verify"             # Verify claims against evidence
    ANALYZE = "analyze"           # Analyze patterns or relationships
    SYNTHESIZE = "synthesize"     # Combine information from multiple sources
    RANK = "rank"             # rank for specific information
    # knowledge access operators
    SEARCH = "search"             # Search for specific information
    TRAVERSE = "traverse"             # traverse for specific information
    FINDNODE = "findnode"             # findnode for specific information
    RETRIEVE = "retrieve"             # retieve for specific information
    # relational operator
    GROUPBY = "groupby"             # groupby for specific information
    AGGREGATE = "aggregate"             # aggregate for specific information
    FILTER = "filter"             # filter for specific information

    @classmethod
    def from_str(cls, s: str) -> "StepType | None":
        value_to_member = {member.value: member for member in cls}
        return value_to_member.get(s)

@dataclass
class ResearchStep:
    """Represents a single step in a multi-step research query"""
    id: str
    step_type: StepType
    description: str
    target_sections: List[str] = field(default_factory=list)  # e.g., ["Introduction", "Method"]
    target_papers: List[str] = field(default_factory=list)    # Paper IDs
    dependencies: List[str] = field(default_factory=list)     # IDs of steps this depends on
    parameters: Dict[str, Any] = field(default_factory=dict)  # Step-specific parameters
    prompt_template: Optional[str] = None                     # Custom prompt if needed
    handler_type: Optional[str] = None                        # concrete executor type
    mode: Optional[str] = None                        # "local" or "global"
    inputs: Optional[List[str]] = None                # the needed input step id of current stpe
    statistics: Dict = field(default_factory=dict)


@dataclass
class StepResult:
    """Result of executing a research step"""
    step_id: str
    success: bool
    result: Any
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ResearchPlan:
    """Complete multi-step research plan"""
    id: str
    query: str
    paper_scope: List[str] = field(default_factory=list)  # Paper IDs to work with
    steps: List[ResearchStep] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    def visualize(self, filename: str = "research_plan.dot"):
        """Export the ResearchPlan's dependency graph to a Graphviz .dot file"""
        with open(filename, "w") as f:
            f.write("digraph ResearchPlan {\n")
            f.write("  node [shape=box, style=rounded, fontsize=10];\n\n")

            for step in self.steps:
                label_lines = [
                    f"ID: {step.id}",
                    f"Type: {step.step_type}",
                    f"Handler: {step.handler_type or 'N/A'}",
                    f"Mode: {step.mode or 'N/A'}",
                    f"Papers: {','.join(step.target_papers) if step.target_papers else 'None'}",
                    f"Sections: {','.join(step.target_sections) if step.target_sections else 'None'}",
                    f"Inputs: {','.join(step.inputs) if step.inputs else 'None'}",
                    f"Description: {step.description if step.description else 'None'}"
                ]
                label = "\\n".join(label_lines)
                f.write(f'  "{step.id}" [label="{label}"];\n')

            f.write("\n")

            for step in self.steps:
                for dep in step.dependencies:
                    f.write(f'  "{dep}" -> "{step.id}";\n')

            f.write("}\n")

        print(f"[INFO] Research plan graph exported to {filename}")
    def serialize(self, filename: str = "serialized_research_plan.yaml"):
        """Serialize the research plan into a structured YAML file."""
        # --- task_scope ---
        task_scope = {
            "filter_type": "paper_id",
            "query": ", ".join(self.paper_scope)
        }

        # --- outputs ---
        outputs = [self.steps[-1].id] if self.steps else []

        # --- nodes ---
        nodes = []
        for step in self.steps:
            node = {
                "id": step.id,
                "type": step.step_type.value,
                "description": step.description,
                "mode": step.mode,
                "handler": step.handler_type,
            }

            # inputs
            if step.step_type.value == "retrieve":
                node["inputs"] = [f'section["{sec}"]' for sec in step.target_sections]
            else:
                node["inputs"] = [f'output["{inp}"]' for inp in (step.inputs or [])]

            # optional parameters (if you want to include special settings)
            if step.parameters:
                node["parameter"] = step.parameters
            nodes.append(node)

        # --- edges ---
        edges = []
        for step in self.steps:
            for dep in step.dependencies:
                edges.append({"from": dep, "to": step.id})
        # --- plan_desc ---
        plan_desc = []
        cnt = 1
        for step in self.steps:
            plan_desc.append(f"{cnt}.{step.description}")
            cnt += 1
        
        # --- overall structure ---
        plan_dict = {
            "task_scope": task_scope,
            "outputs": outputs,
            "nodes": nodes,
            "edges": edges,
            "metadata": {
                **self.metadata,
                "step_description": ' '.join(plan_desc)
            }
        }

        # --- write YAML ---
        with open(filename, "w", encoding="utf-8") as f:
            yaml.safe_dump(plan_dict, f, sort_keys=False, allow_unicode=True)

        print(f"[DONE]Research plan serialized to {filename}")

    def deserialize(self, filename: str):
        """
        Deserialize a YAML file back into a ResearchPlan instance.
        `step_type_enum` is an optional enum class for StepType resolution.
        """
        from src.executor_multistep.multi_step_engine import get_handler_enum
        with open(filename, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        # --- task_scope ---
        task_scope = data.get("task_scope", {})
        metadata = data.get("metadata", {})
        paper_scope = [s.strip() for s in task_scope.get("query", "").split(",") if s.strip()]

        # --- build step map for dependencies ---
        edges = data.get("edges", [])
        dep_map = {}
        for edge in edges:
            dep_map.setdefault(edge["to"], []).append(edge["from"])

        # --- construct ResearchStep list ---
        steps = []
        for node in data.get("nodes", []):
            step_id = node["id"]
            step_type_str = node.get("type", "")
            mode = node.get("mode")
            handler = node.get("handler")
            parameters = node.get("parameter", {})

            step_type = StepType.from_str(step_type_str)
            handler_type_enum = get_handler_enum(step_type)
            handler_type = handler_type_enum.from_str(handler)
            description = handler_type.value["description"]

            inputs_raw = node.get("inputs", [])
            target_sections, inputs = [], []

            # resolve inputs： section/output
            for item in inputs_raw:
                if item.startswith('section["'):
                    # e.g., section["Experiment"]
                    target_sections.append(item.split('"')[1])
                elif item.startswith('output["'):
                    inputs.append(item.split('"')[1])


            step = ResearchStep(
                id=step_id,
                step_type=step_type,
                description=description,
                target_sections=target_sections,
                target_papers=self.paper_scope,
                dependencies=dep_map.get(step_id, []),
                handler_type=handler,
                mode=mode,
                inputs=inputs,
                parameters=parameters,
            )
            steps.append(step)

        # --- build ResearchPlan ---
        self.steps = steps;
        self.metadata.update(metadata)

        print(f"Research plan deserialized from {filename}")
        
class ResearchJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        # 处理枚举类型
        if isinstance(obj, Enum):
            return obj.value  # 存储枚举值而非枚举对象
        
        # 处理ResearchPlan和ResearchStep
        if isinstance(obj, (ResearchPlan, ResearchStep)):
            # 添加类名标识，方便反序列化
            result = asdict(obj)
            result["__class__"] = obj.__class__.__name__
            return result
        
        # 其他类型使用默认处理
        return super().default(obj)

# 反序列化钩子：将字典还原为对象
def research_object_hook(dct):
    # 根据类名标识判断类型
    class_name = dct.get("__class__")
    
    if class_name == "ResearchPlan":
        # 先移除类名标识
        dct.pop("__class__", None)
        # 处理嵌套的steps（将字典转换为ResearchStep对象）
        steps = [research_object_hook(step) for step in dct.get("steps", [])]
        return ResearchPlan(
            id=dct["id"],
            query=dct["query"],
            paper_scope=dct.get("paper_scope", []),
            steps=steps,
            metadata=dct.get("metadata", {})
        )
    
    elif class_name == "ResearchStep":
        dct.pop("__class__", None)
        # 还原枚举类型（StepType）
        step_type = StepType(dct["step_type"])
        return ResearchStep(
            id=dct["id"],
            step_type=step_type,
            description=dct["description"],
            target_sections=dct.get("target_sections", []),
            target_papers=dct.get("target_papers", []),
            dependencies=dct.get("dependencies", []),
            parameters=dct.get("parameters", {}),
            prompt_template=dct.get("prompt_template"),
            handler_type=dct.get("handler_type"),
            mode=dct.get("mode"),
            inputs=dct.get("inputs", []),
            statistics=dct.get("statistics", {})
        )
    
    # 非自定义类直接返回字典
    return dct

class ExecutorType(Enum):
    """Types of executor"""
    # semantic operators
    EXTRACT = "extract"           # Extract specific information from sections
    SUMMARIZE = "summarize"       # Summarize content from sections
    CHECK = "check"           # Compare information across sections/papers
    VERIFY = "verify"             # Verify claims against evidence
    ANALYZE = "analyze"           # Analyze patterns or relationships
    SYNTHESIZE = "synthesize"     # Combine information from multiple sources
    RANK = "rank"             # rank for specific information
    # knowledge access operators
    SEARCH = "search"             # Search for specific information
    TRAVERSE = "traverse"             # traverse for specific information
    FINDNODE = "findnode"             # findnode for specific information
    RETRIEVE = "retrieve"             # findnode for specific information
    # relational operator
    GROUPBY = "groupby"             # groupby for specific information
    AGGREGATE = "aggregate"             # aggregate for specific information
    FILTER = "filter"             # filter for specific information

class StepExecutor(ABC):
    """Abstract base class for step executors"""

    executor_type: ExecutorType
    step: ResearchStep
    target_paper: str

    def __init__(self, db_name: str, step: ResearchStep, target_paper: str):
        self.db_name = db_name
        self.step = step
        self.target_paper = target_paper
        # self.indexer = WeaviateIndexer(db_name=db_name)
    
    @abstractmethod
    def execute(self, context: Dict[str, Any]) -> StepResult:
        """Execute a research step with given context"""
        pass
    
    def get_inputs(self, context: Dict[str, Any]) -> List:
        # Get inputs items from previous node
        items = []
        for key, result in context.items():
            items.append(result)

        return items


def try_dummy(step_map: Dict[str, ResearchStep], step: ResearchStep)-> bool:
    return True

def try_certain_prev_target_section(expected_target_section: str, step_map: Dict[str, ResearchStep], step: ResearchStep)-> bool:
    # succ = False
    for predecessor_id in step.dependencies:
        pre_step = step_map[predecessor_id]
        for section in pre_step.target_sections:
            if section == expected_target_section:
                return True
    return False

def try_experiment(step_map: Dict[str, ResearchStep], step: ResearchStep)-> bool:
    return try_certain_prev_target_section("Experiment", step_map, step)

def try_method(step_map: Dict[str, ResearchStep], step: ResearchStep)-> bool:
    return try_certain_prev_target_section("Method", step_map, step)

def try_problem_def(step_map: Dict[str, ResearchStep], step: ResearchStep)-> bool:
    return try_certain_prev_target_section("Problem Definition", step_map, step)

def try_cross_paper(step_map: Dict[str, ResearchStep], step: ResearchStep)-> bool:

    paper_set = set()

    for predecessor_id in step.dependencies:
        pre_step = step_map[predecessor_id]
        
        for paper in pre_step.target_papers:
            paper_set.add(paper)
    
    if len(paper_set) > 1:
        return True
    
    return False

def try_cross_paper_experiment(step_map: Dict[str, ResearchStep], step: ResearchStep)-> bool:
    return try_cross_paper(step_map, step) and try_experiment(step_map, step)

def try_certain_prev_node(expected_type: Enum, step_map: Dict[str, ResearchStep], step: ResearchStep)-> bool:
    for predecessor_id in step.dependencies:
        pre_step = step_map[predecessor_id]
        if pre_step.handler_type is None:
            continue
        if pre_step.handler_type == expected_type.value["name"]:
            return True
    return False