from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import MemorySaver

from src.state import AgentState
from src.nodes.component_master import component_master_node
from src.nodes.input_gatherer import input_gatherer_node
from src.nodes.detailer import detailer_node
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


workflow = StateGraph(AgentState)

workflow.add_node("component_master", component_master_node)
workflow.add_node("input_gatherer", input_gatherer_node)
workflow.add_node("detailer", detailer_node)

workflow.add_edge(START, "component_master")

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

app = workflow.compile(checkpointer=checkpointer)
