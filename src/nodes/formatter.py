from src.state import AgentState

NODE_INSTRUCTIONS = "Output dual Markdown (AI-optimized) and English (Human-readable)."

async def formatter(state: AgentState) -> AgentState:
    prompt = f"{state['persona_prompt']}\n\n{NODE_INSTRUCTIONS}"
    log_entry = f"formatter: Executed. Prompt starts with: '{state['persona_prompt'][:30]}...'"
    return {
        **state,
        "history": [log_entry]
    }
