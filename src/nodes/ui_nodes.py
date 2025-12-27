from typing import Dict, Any
from src.state import AgentState

def prepare_ui_feedback_node(state: AgentState) -> Dict[str, Any]:
    """Node to populate ui_queue with component descriptions."""
    
    ui_queue = []
    
    if not state.get("can_proceed", False):
        ui_queue.append({
            "type": "error_alert",
            "content": state.get("feedback", "Sanity check failed.")
        })
        ui_queue.append({
            "type": "text_input_form",
            "label": "Try again with more detail"
        })
    else:
        prd_components = state.get("prd_components", {})
        
        if prd_components:
            ui_queue.append({"type": "prd_display"})
            
            if state.get("goal_exists", False):
                ui_queue.append({
                    "type": "success_card",
                    "content": "Goal exists - PRD analysis complete!",
                    "metadata": {"goal_exists": True}
                })
            else:
                ui_queue.append({
                    "type": "success_card",
                    "content": "Calling Goal - goal clarification initiated",
                    "metadata": {"goal_exists": False}
                })
        else:
            metadata = state.get("metadata", {})
            missing_metadata = any(v is None for v in metadata.values())
            
            if missing_metadata:
                ui_queue.append({
                    "type": "success_card",
                    "content": "Sanity check passed, but we need more context.",
                    "metadata": metadata
                })
                ui_queue.append({
                    "type": "metadata_input_form",
                    "missing_fields": [k for k, v in metadata.items() if v is None]
                })
            else:
                ui_queue.append({
                    "type": "success_card",
                    "content": "Ready to proceed!",
                    "metadata": metadata
                })
            
    return {
        "ui_queue": ui_queue
    }
