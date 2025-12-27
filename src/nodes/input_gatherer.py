import logging
from typing import Dict, Any

from src.state import AgentState

logger = logging.getLogger(__name__)


def input_gatherer_node(state: AgentState) -> Dict[str, Any]:
    """
    Input Gatherer Node - Sets awaiting_user_input flag.
    
    This node acts as a "wait for user" state. The Streamlit app
    checks this flag to render input forms for gaps.
    When user provides input, the graph resumes from checkpointer.
    """
    print("\n=== INPUT_GATHERER NODE: START ===")
    logger.info("input_gatherer: Waiting for user input")
    
    gaps = state.get("gaps", [])
    
    print(f"=== INPUT_GATHERER NODE: Awaiting input for gaps: {gaps} ===")
    logger.info(f"input_gatherer: Gaps requiring input: {gaps}")
    
    print("=== INPUT_GATHERER NODE: END ===\n")
    
    return {
        "awaiting_user_input": True,
        "feedback": f"Please provide details for: {', '.join(gaps)}" if gaps else "All components complete",
    }
