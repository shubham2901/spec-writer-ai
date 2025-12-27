from typing import TypedDict, List, Dict, Any, Optional


class AgentState(TypedDict):
    raw_input: str
    current_spec: str
    can_proceed: bool
    metadata: Dict[str, Optional[str]]
    feedback: str
    ui_queue: List[Dict[str, Any]]
    messages: List[Dict[str, Any]]
    
    components: Dict[str, Optional[str]]
    gaps: List[str]
    last_updated_component: Optional[str]
    is_spec_complete: bool
    
    awaiting_user_input: bool
    
    detailed_components: Dict[str, Dict[str, Any]]
    is_detailed: bool
