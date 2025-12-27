# Spec Writer AI

AI-powered PRD (Product Requirements Document) generator using LangGraph and Google Gemini.

## Features

- **Component Extraction**: Automatically maps input to 7 PRD components (Goal, Problem Statement, User Cohort, Metrics, Solutions, Risks, GTM)
- **Gap Detection**: Identifies incomplete components (< 10 words)
- **Live Spec View**: Real-time display of extracted components
- **Detailer**: Elaborates components and generates 3 follow-up questions each
- **Export**: Download as Markdown or PDF

## Setup

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Set your Google API key:
   ```bash
   export GOOGLE_API_KEY=your-api-key
   ```
   Or create a `.env` file with `GOOGLE_API_KEY=your-api-key`

5. Run the app:
   ```bash
   streamlit run app.py
   ```

## Architecture

- `app.py` - Streamlit web UI with st.fragment for partial reruns
- `src/graph.py` - LangGraph workflow with MemorySaver checkpointer
- `src/nodes/component_master.py` - LLM extraction + gap detection
- `src/nodes/detailer.py` - Component elaboration + question generation
- `src/nodes/input_gatherer.py` - User input wait state
- `src/knowledge_base.py` - PRD component definitions
- `src/utils/exporter.py` - Markdown and PDF export

## Deployment

Deploy on [Streamlit Community Cloud](https://streamlit.io/cloud):

1. Push to GitHub
2. Connect repo at streamlit.io/cloud
3. Add `GOOGLE_API_KEY` in Secrets

## License

MIT
