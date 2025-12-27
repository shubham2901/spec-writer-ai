from src.state import AgentState

NODE_INSTRUCTIONS = "Identify potential failures or unhandled states."

async def edge_case_catcher(state: AgentState) -> AgentState:
    prompt = f"{state['persona_prompt']}\n\n{NODE_INSTRUCTIONS}"
    log_entry = f"edge_case_catcher: Executed. Prompt starts with: '{state['persona_prompt'][:30]}...'"
    return {
        **state,
        "history": [log_entry]
    }
