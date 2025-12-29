from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import MemorySaver

from src.state import AgentState
from src.nodes.component_master import component_master_node
from src.nodes.input_gatherer import input_gatherer_node
from src.nodes.detailer import detailer_node
from src.nodes.refiner import refiner_node
from src.knowledge_base import PRD_COMPONENT_NAMES


checkpointer = MemorySaver()


def get_checkpointer():
    return checkpointer


def component_master_router(state: AgentState) -> str:
    """Route based on spec completeness."""
    is_complete = state.get("is_spec_complete", False)
    gaps = state.get("gaps", [])
    
    if is_complete or not gaps:
        print("=== ROUTER: Spec complete, routing to detailer ===")
        return "detailer"
    
    print(f"=== ROUTER: Gaps exist ({len(gaps)}), routing to input_gatherer ===")
    return "input_gatherer"


from src.nodes.sanity_checker import sanity_checker_node

def sanity_router(state: AgentState) -> str:
    """Route based on sanity check."""
    can_proceed = state.get("can_proceed", False)
    if can_proceed:
        print("=== ROUTER: Sanity check passed, routing to component_master ===")
        return "component_master"
    
    print("=== ROUTER: Sanity check failed, ending workflow ===")
    return "end"

workflow = StateGraph(AgentState)

workflow.add_node("sanity_checker", sanity_checker_node)
workflow.add_node("component_master", component_master_node)
workflow.add_node("input_gatherer", input_gatherer_node)
workflow.add_node("detailer", detailer_node)
workflow.add_node("refiner", refiner_node)

workflow.add_edge(START, "sanity_checker")

workflow.add_conditional_edges(
    "sanity_checker",
    sanity_router,
    {
        "component_master": "component_master",
        "end": END
    }
)

workflow.add_conditional_edges(
    "component_master",
    component_master_router,
    {
        "input_gatherer": "input_gatherer",
        "detailer": "detailer",
    }
)

workflow.add_edge("input_gatherer", END)
workflow.add_edge("detailer", END)
workflow.add_edge("refiner", END)

app = workflow.compile(checkpointer=checkpointer)
