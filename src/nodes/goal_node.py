import logging
from typing import Dict, Any

from src.state import AgentState

logger = logging.getLogger(__name__)


def goal_node(state: AgentState) -> Dict[str, Any]:
    print("\n=== GOAL_NODE: START ===")
    logger.info("goal_node: Goal clarification needed")
    
    print("=== GOAL_NODE: Calling Goal ===")
    logger.info("goal_node: Calling Goal")
    
    print("=== GOAL_NODE: END ===\n")
    
    return {
        "feedback": "Calling Goal - goal clarification process initiated",
    }
