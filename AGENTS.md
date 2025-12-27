# AGENTS.md

## Commands
- **Run Streamlit app**: `streamlit run app.py`
- **Run CLI workflow**: `python main.py`
- **Run component tests**: `GOOGLE_API_KEY=<key> python test_components.py`
- **Install deps**: `pip install -r requirements.txt`

## Architecture
LangGraph-based multi-agent spec writing system with Streamlit UI.
- `app.py` - Streamlit web UI with st.fragment for partial reruns, Live Spec display
- `main.py` - CLI entrypoint for workflow execution
- `src/graph.py` - LangGraph workflow with MemorySaver checkpointer (loop: component_master → input_gatherer)
- `src/state.py` - `AgentState` TypedDict with components, gaps, is_spec_complete
- `src/knowledge_base.py` - PRD component definitions, prompts, MIN_WORDS_THRESHOLD
- `src/persona.py` - System prompts and model config (Gemini)
- `src/nodes/component_master.py` - LLM extraction + gap detection (10 word threshold)
- `src/nodes/input_gatherer.py` - User input wait state

## Code Style
- Python 3.10+, type hints via `typing` module (TypedDict for state)
- Imports: stdlib → third-party (langgraph, streamlit, google-genai) → local (src.*)
- Use `async/await` for LangGraph workflow execution
- LLM: Google Gemini via `langchain-google-genai`, model in `src/persona.py`
- State mutations return partial dicts merged by LangGraph
- Error handling: log via `logging` module, surface to UI via `ui_queue`
