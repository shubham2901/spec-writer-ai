from src.state import AgentState

NODE_INSTRUCTIONS = "Generate acceptance criteria based on the spec."

async def tester(state: AgentState) -> AgentState:
    prompt = f"{state['persona_prompt']}\n\n{NODE_INSTRUCTIONS}"
    log_entry = f"tester: Executed. Prompt starts with: '{state['persona_prompt'][:30]}...'"
    return {
        **state,
        "history": [log_entry]
    }
