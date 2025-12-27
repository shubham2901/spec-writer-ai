from src.state import AgentState

GOAL_JUDGE_INSTRUCTIONS = "Evaluate the 'Why' using the JTBD framework."

async def goal_judge(state: AgentState) -> AgentState:
    prompt = f"{state['persona_prompt']}\n\n{GOAL_JUDGE_INSTRUCTIONS}"
    log_entry = f"goal_judge: Executed with persona. Prompt prefix: '{state['persona_prompt'][:30]}...'"
    return {
        **state,
        "history": [log_entry]
    }
