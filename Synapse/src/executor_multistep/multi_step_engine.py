from collections import deque
import time
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
import json
import uuid
from abc import ABC, abstractmethod
import concurrent.futures

from src.executor_multistep.executor.analyze_step_executor import AnalyzeStepExecutor
from src.executor_multistep.executor.check_step_executor import CheckStepExecutor, CheckType
from src.executor_multistep.executor.extract_step_executor import ExtractStepExecutor, ExtractType
from src.executor_multistep.executor.plan_step import ExecutorType, ResearchPlan, ResearchStep, StepExecutor, StepResult, StepType
from src.executor_multistep.executor.rank_step_executor import RankStepExecutor, RankType
from src.executor_multistep.executor.retrieve_step_executor import RetrieveStepExecutor, RetrieveType
from src.executor_multistep.executor.search_step_executor import SearchStepExecutor
from src.executor_multistep.executor.summarize_step_executor import SummarizeStepExecutor, SummarizeType
from src.executor_multistep.executor.synthesize_step_executor import SynthesizeStepExecutor, SynthesizeType
from src.executor_multistep.executor.verify_step_executor import VerifyStepExecutor, VerifyType
from src.prompts.base import run_structured_prompt

EXECUTOR_REGISTRY = {
    StepType.EXTRACT: ExtractStepExecutor,
    StepType.SUMMARIZE: SummarizeStepExecutor,
    StepType.VERIFY: VerifyStepExecutor,
    StepType.CHECK: CheckStepExecutor,
    StepType.ANALYZE: AnalyzeStepExecutor,
    StepType.SYNTHESIZE: SynthesizeStepExecutor,
    StepType.SEARCH: SearchStepExecutor,
    StepType.RETRIEVE: RetrieveStepExecutor,
    StepType.RANK: RankStepExecutor
    # Add more executors as needed
}
def get_handler_enum(type: ExecutorType) -> Enum | None:
    step_map = {
        StepType.EXTRACT: ExtractType,
        StepType.SUMMARIZE: SummarizeType,
        StepType.CHECK: CheckType,
        StepType.RANK: RankType,
        StepType.SYNTHESIZE: SynthesizeType,
        StepType.RETRIEVE: RetrieveType,
        StepType.VERIFY: VerifyType
    }
    return step_map.get(type)

@dataclass
class ExecutionNode:
    """Represents an executable node in the DAG"""
    id: str
    step: ResearchStep
    executor: StepExecutor
    predecessors: List[str] = field(default_factory=list)
    successors: List[str] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)

    def execute(self, context: Dict[str, Any]) -> StepResult:
        """Execute this node using results from predecessors"""
        start = time.perf_counter()
        try:
            res = self.executor.execute(context)
            if not isinstance(res, StepResult):
                res = StepResult(step_id=self.step.id, success=True, result=res, metadata={})
        except Exception as e:
            res = StepResult(
                step_id=self.step.id,
                success=False,
                result=None,
                error_message=str(e),
                metadata={}
            )
        finally:
            end = time.perf_counter()
            if res.metadata is None:
                res.metadata = {}
            self.metadata["start_ts"] = start
            self.metadata["end_ts"] = end
            self.metadata["duration"] = end - start
            if res.result and isinstance(res.result, dict):
                self.metadata["input_tokens"] = res.result.get("input_tokens", 0)
                self.metadata["output_tokens"] = res.result.get("output_tokens", 0)
                res.result = res.result["response"]
        return res
    def get_input_steps(self):
        if isinstance(self.step.inputs, str):
            return [self.step.inputs]
        else:
            return self.step.inputs

@dataclass
class ExecutionGraph:
    """Represents the full execution DAG"""
    id: str
    query: str
    nodes: Dict[str, ExecutionNode] = field(default_factory=dict)
    step_nodes_map: Dict[str, Dict[str, ExecutionNode]] = field(default_factory=dict)

    def add_node(self, node: ExecutionNode):
        self.nodes[node.id] = node
        if node.step.id not in self.step_nodes_map:
            self.step_nodes_map[node.step.id] = {}
        self.step_nodes_map[node.step.id][node.executor.target_paper] = node
        
    def add_edge(self, from_id: str, to_id: str):
        self.nodes[from_id].successors.append(to_id)
        self.nodes[to_id].predecessors.append(from_id)
    
    def visualize(self, filename: str = "execution_graph.dot"):
        """Export the DAG structure to a Graphviz .dot file"""
        with open(filename, "w") as f:
            f.write("digraph ResearchPlan { \n")
            for node_id, node in self.nodes.items():
                label_lines = [
                    f"ID: {node_id}",
                    f"Type: {node.step.step_type}",
                    f"Handler: {node.step.handler_type or 'N/A'}",
                    f"Papers: {node.executor.target_paper}",
                    f"Sections: {','.join(node.step.target_sections) if node.step.target_sections else 'None'}",
                    f"Inputs: {','.join(node.step.inputs) if node.step.inputs else 'None'}"
                ]
                label = "\\n".join(label_lines)
                f.write(f'  "{node_id}" [label="{label}", shape=box, style=rounded];\n')

                for succ in node.successors:
                    f.write(f'  "{node_id}" -> "{succ}";\n')
            f.write("}\n")
        print(f"[INFO] Execution graph exported to {filename}")

    def visualize_analyzed(self, results: Dict[str, "StepResult"], filename: str = "execution_analyzed.dot"):
        """
        Generate a .dot file with execution information:
        - Node labels include: id, type, success/fail, and execution time (ms)
        - Node colors are based on status: success -> green, failure -> red, unknown -> gray
        - Edges retain their original dependency relationships
        - If there is an error_message, it will be placed in the tooltip (with a line break in the label)
        """
        def color_for(res: Optional[StepResult]) -> str:
            if res is None:
                return "gray"
            if res.success:
                return "palegreen"
            return "salmon"

        with open(filename, "w", encoding="utf-8") as f:
            f.write("digraph ResearchPlanAnalyzed {\n")
            f.write('  node [shape=box, style="rounded,filled", fontname="Helvetica"];\n\n')

            for node_id, node in self.nodes.items():
                res = results.get(node_id)
                color = color_for(res)
                # construct label: id, type, status, duration(ms)
                typ = node.step.step_type.value
                label_lines = [
                    f"ID: {node_id}",
                    f"Type: {node.step.step_type}",
                    f"Handler: {node.step.handler_type or 'N/A'}",
                    f"Papers: {node.executor.target_paper}",
                    f"Sections: {','.join(node.step.target_sections) if node.step.target_sections else 'None'}",
                    f"Inputs: {','.join(node.step.inputs) if node.step.inputs else 'None'}",
                    f"Time:{node.metadata.get("duration", 0)}",
                    f"Input/Output Tokens:{node.metadata.get("input_tokens", 0)}/{node.metadata.get("output_tokens", 0)}"
                ]
                label = "\\n".join(label_lines)

                f.write(f'  "{node_id}" [label="{label}", fillcolor="{color}"];\n')

            f.write("\n")
            for node_id, node in self.nodes.items():
                for succ in node.successors:
                    f.write(f'  "{node_id}" -> "{succ}";\n')

            f.write("}\n")
        print(f"[INFO] Execution analyzed graph exported to {filename}")
        print("Hint: use `dot -Tpng {filename} -o output.png` to render the image")

class ExecutionPlanBuilder:
    """Builds an ExecutionGraph (DAG) from a ResearchPlan"""

    def __init__(self, db_name: str, executor_registry: Dict[StepType, type] = EXECUTOR_REGISTRY):
        self.db_name = db_name
        self.executor_registry = executor_registry
        self.pk = 0

    def build_execution_graph(self, plan: ResearchPlan) -> ExecutionGraph:
        graph = ExecutionGraph(plan.id, plan.query)
        if plan is None:
            return graph
        # Step 1: build node
        for step in plan.steps:
            if step.mode == "global":
                node = self.create_execution_node(step, "*")
                graph.add_node(node)
            else:
                for paper in step.target_papers:
                    node = self.create_execution_node(step, paper)
                    graph.add_node(node)

        # Step 2: build dependency
        for step in plan.steps:
            for dep_id in step.dependencies:
                for key, start_node in graph.step_nodes_map[dep_id].items():
                    cur_step_node_map = graph.step_nodes_map[step.id]
                    if key not in cur_step_node_map:
                        key = "*"
                    end_node = cur_step_node_map[key]
                    graph.add_edge(start_node.id, end_node.id)
        return graph

    def create_execution_node(self, step: ResearchStep, target_paper: str)-> ExecutionNode:
        executor_cls = self.executor_registry.get(step.step_type)
        if not executor_cls:
            raise ValueError(f"No executor registered for type {step.step_type}")
        executor = executor_cls(self.db_name, step, target_paper)
        return ExecutionNode(id=self.get_pk(),step=step, executor=executor)

    def get_pk(self) -> str:
        new_pk = f"node_{self.pk}"
        self.pk+=1
        return new_pk

class MultiStepResearchEngine:
    """Main engine for executing multi-step research queries"""

    graph: ExecutionGraph # Represents the complete executable plan tree
    def __init__(self, max_workers: int = 5):
        self.max_workers = max_workers
    
    def execute_plan(self, graph: ExecutionGraph, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a complete research plan"""
        context = context or {}
        indegree = {nid: len(node.predecessors) for nid, node in graph.nodes.items()}
        ready_queue = deque([nid for nid, deg in indegree.items() if deg == 0])
        results: Dict[str, StepResult] = {}

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures: Dict[concurrent.futures.Future, str] = {}

            while ready_queue or futures:
                # submit all zero in-degree node task
                while ready_queue:
                    node_id = ready_queue.popleft()
                    node = graph.nodes[node_id]
                    dep_results = self.collect_inputs(node, results)
                    #     print(f"{node.id} get inputs: {dep_results}")
                    fut = executor.submit(node.execute, dep_results)  
                    futures[fut] = node_id
                    print(f"[EXEC] Submitted {node_id} ({node.step.step_type.value})")

                # wait
                done, _ = concurrent.futures.wait(futures.keys(), return_when=concurrent.futures.FIRST_COMPLETED)

                # handle finished task
                for fut in done:
                    node_id = futures.pop(fut)
                    node = graph.nodes[node_id]
                    try:
                        res = fut.result()
                        results[node_id] = res
                        print(f"[DONE] {node_id}: success={res.success}")
                    except Exception as e:
                        results[node_id] = StepResult(step_id=node.step.id, success=False, result=None, error_message=str(e))
                        print(f"[ERROR] {node_id}: {e}")

                    # decrease successors' in-degrees
                    for succ in graph.nodes[node_id].successors:
                        indegree[succ] -= 1
                        if indegree[succ] == 0:
                            ready_queue.append(succ)

        # examine whether it has a cycle
        if len(results) < len(graph.nodes):
            raise RuntimeError("Execution graph contains a cycle; topological execution incomplete.")

        return {
            "plan_id": graph.id,
            "query": graph.query,
            "results": results,
            # "final_synthesis": self._synthesize_final_answer(graph.query, results)
            "final_synthesis": list(results.items())[-1][1].result
        }

    def collect_inputs(self, node: ExecutionNode, results: Dict[str, StepResult]):
        # collect prev step result
        dep_results = {}
        if len(node.predecessors) == 0:
            return dep_results
        for dep in node.predecessors:
            if dep not in results or not results[dep].success:
                continue
            step_id = results[dep].step_id
            if step_id not in dep_results:
                dep_results[step_id] = []
            dep_results[step_id].append(results[dep].result)

        # reorder the input step
        ordered_dep_results = {}
        input_step_list = node.get_input_steps()

        if not input_step_list:
            return ordered_dep_results
        
        for input_step_id in input_step_list:
            if input_step_id not in dep_results:
                print("[Error] missing step input")
                continue
            ordered_dep_results[input_step_id] = dep_results[input_step_id]

        return ordered_dep_results
