from __future__ import annotations

from typing import Any, TypedDict

from langgraph.graph import END, StateGraph

from bdd_agent.nodes.analyze_structure import analyze_structure_node
from bdd_agent.nodes.classify import classify_test_cases_node
from bdd_agent.nodes.generate_gherkin import gherkin_generation_node
from bdd_agent.nodes.load_excel import load_excel_node
from bdd_agent.nodes.normalize import normalize_test_cases_node
from bdd_agent.nodes.scenario_design import scenario_design_node
from bdd_agent.nodes.validate import validation_node
from bdd_agent.nodes.write_files import write_feature_files_node


class AgentState(TypedDict, total=False):
    input_paths: list[str]
    output_dir: str
    model: str
    raw_sheets: dict[str, dict[str, Any]]
    structure_analysis: list[dict[str, Any]]
    normalized_test_cases: list[dict[str, Any]]
    classified_test_cases: list[dict[str, Any]]
    feature_documents: dict[str, Any]
    validation_errors: list[str]
    written_files: list[str]



def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("load_excel_node", load_excel_node)
    graph.add_node("analyze_structure_node", analyze_structure_node)
    graph.add_node("normalize_test_cases_node", normalize_test_cases_node)
    graph.add_node("classify_test_cases_node", classify_test_cases_node)
    graph.add_node("scenario_design_node", scenario_design_node)
    graph.add_node("gherkin_generation_node", gherkin_generation_node)
    graph.add_node("validation_node", validation_node)
    graph.add_node("write_feature_files_node", write_feature_files_node)

    graph.set_entry_point("load_excel_node")
    graph.add_edge("load_excel_node", "analyze_structure_node")
    graph.add_edge("analyze_structure_node", "normalize_test_cases_node")
    graph.add_edge("normalize_test_cases_node", "classify_test_cases_node")
    graph.add_edge("classify_test_cases_node", "scenario_design_node")
    graph.add_edge("scenario_design_node", "gherkin_generation_node")
    graph.add_edge("gherkin_generation_node", "validation_node")
    graph.add_edge("validation_node", "write_feature_files_node")
    graph.add_edge("write_feature_files_node", END)

    return graph.compile()



def run_agent(input_paths: list[str], output_dir: str, model: str = "gpt-4.1-mini") -> AgentState:
    graph = build_graph()
    return graph.invoke(
        {
            "input_paths": input_paths,
            "output_dir": output_dir,
            "model": model,
        }
    )
