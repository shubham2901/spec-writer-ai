import asyncio
from src.graph import app
from src.state import AgentState
from src.persona import HELPFUL_ASSISTANT_TONE

async def main():
    initial_state: AgentState = {
        "raw_input": "Create a new multi-agentic system for technical spec writing.\nLine 2\nLine 3\nLine 4\nLine 5",
        "current_spec": "",
        "missing_details": [],
        "status": {
            "sanity_ok": False,
            "goal_clear": False,
        },
        "history": [],
        "persona_prompt": HELPFUL_ASSISTANT_TONE
    }

    print("--- Starting Refactored Spec-Writing Workflow ---")
    
    config = {"configurable": {"thread_id": "production_test"}}
    
    async for event in app.astream(initial_state, config):
        for node_name, state in event.items():
            print(f"\nNode '{node_name}' executed.")
            print(f"Log: {state['history'][-1]}")
            
            # Simple simulation for the demo
            if node_name == "goal_judge":
                print("--- Simulating Goal Clarification ---")
                state["status"]["goal_clear"] = True

    print("\n--- Workflow Completed ---")

if __name__ == "__main__":
    asyncio.run(main())
