import streamlit as st
import asyncio
import logging
from datetime import datetime
from typing import Dict
from src.graph import app, get_checkpointer
from src.state import AgentState
from src.knowledge_base import PRD_COMPONENT_NAMES, MIN_WORDS_THRESHOLD
from src.utils.exporter import export_to_markdown, export_to_pdf

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class StreamlitLogHandler(logging.Handler):
    def emit(self, record):
        if record.levelno < logging.INFO:
            return
        if "thinking_logs" not in st.session_state:
            st.session_state.thinking_logs = []
        log_entry = {
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "level": record.levelname,
            "message": self.format(record)
        }
        st.session_state.thinking_logs.append(log_entry)


streamlit_handler = StreamlitLogHandler()
streamlit_handler.setFormatter(logging.Formatter('%(name)s - %(levelname)s - %(message)s'))
logging.getLogger().addHandler(streamlit_handler)


@st.cache_resource
def get_event_loop():
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop


event_loop = get_event_loop()

st.set_page_config(
    page_title="Spec Writer AI",
    layout="wide",
    initial_sidebar_state="expanded"
)


def inject_custom_css():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        
        /* Global Reset & Base Styles */
        body, .stApp { 
            background-color: #0E1117; 
            color: #F9FAFB; 
            font-family: 'Inter', sans-serif;
        }
        
        /* Typography overrides */
        h1, h2, h3, h4, h5, h6 { 
            color: #F9FAFB !important; 
            font-weight: 700 !important; 
            letter-spacing: -0.025em;
        }
        
        /* Font exclusion for icons */
        p, div, span:not([data-testid="stIconMaterial"]), label, button, input, textarea { 
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important; 
        }

        /* Task 2: Button Styling - Subtle Gradient */
        .stButton > button {
            background: linear-gradient(180deg, #2E303E 0%, #1F2128 100%) !important;
            color: #F9FAFB !important;
            border: 1px solid #3F4152 !important;
            border-radius: 8px !important;
            font-weight: 500 !important;
            padding: 0.5rem 1rem !important;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
            box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.2) !important;
        }
        
        .stButton > button:hover {
            background: linear-gradient(180deg, #3A3C4D 0%, #2A2C35 100%) !important;
            border-color: #7C3AED !important; /* Luminous Purple Accent */
            transform: translateY(-1px) !important;
            box-shadow: 0 4px 12px rgba(124, 58, 237, 0.2) !important;
        }
        
        .stButton > button:active {
            transform: translateY(0) !important;
        }

        /* Task 2: Card Styling - 1px solid #2D2E3A, Rounded 12px */
        .component-card {
            background: #15171E;
            border: 1px solid #2D2E3A;
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            transition: box-shadow 0.2s ease;
        }
        
        .component-card:hover {
            box-shadow: 0 8px 15px -3px rgba(0, 0, 0, 0.2), 0 4px 6px -2px rgba(0, 0, 0, 0.1);
            border-color: #3F4152;
        }

        /* Status Indicators (borders/accents) - Updated for Dark Mode */
        .component-complete {
            border-left: 3px solid #10B981; /* Emerald 500 */
        }
        
        .component-incomplete {
            border-left: 3px solid #F59E0B; /* Amber 500 */
        }
        
        .component-detailed {
            border-left: 3px solid #7C3AED; /* Purple 600 */
        }

        /* Task 2: Detailer Questions - "Action Chips" */
        .question-item {
            background: rgba(124, 58, 237, 0.1); /* Light Purple Tint */
            border: 1px solid rgba(124, 58, 237, 0.2);
            border-radius: 20px; /* Bubble/Chip shape */
            padding: 8px 16px;
            margin: 8px 0;
            font-size: 0.9rem;
            color: #E2E8F0;
            transition: all 0.2s ease;
        }
        
        .question-item:hover {
            background: rgba(124, 58, 237, 0.2);
            border-color: rgba(124, 58, 237, 0.4);
            transform: translateX(2px);
        }

        /* Streamlit specific tweaks */
        [data-testid="stHeader"] { display: none !important; }
        
        /* Task 2: Input Focus - Glow Purple */
        .stTextArea textarea {
            background-color: #1A1C23 !important;
            border: 1px solid #2D2E3A !important;
            border-radius: 8px !important;
            color: #F9FAFB !important;
            transition: border-color 0.2s, box-shadow 0.2s;
        }
        
        .stTextArea textarea:focus {
            border-color: #7C3AED !important;
            box-shadow: 0 0 0 2px rgba(124, 58, 237, 0.3) !important;
        }
        
        /* Expander */
        .streamlit-expanderHeader {
            background-color: transparent !important;
            color: #E2E8F0 !important;
            font-weight: 600 !important;
        }
        
        
        /* Sidebar styling tweak */
        [data-testid="stSidebar"] {
            background-color: #0E1117;
            border-right: 1px solid #2D2E3A;
        }
        
        /* === COMPREHENSIVE STREAMLIT OVERRIDES FOR DEPLOYMENT === */
        
        /* Main container backgrounds */
        .main .block-container {
            background-color: #0E1117;
            padding-top: 2rem;
        }
        
        /* All Streamlit widgets - base styling */
        .stSelectbox, .stMultiSelect, .stSlider, .stCheckbox, .stRadio {
            color: #F9FAFB !important;
        }
        
        /* Select boxes and dropdowns */
        .stSelectbox > div > div,
        .stMultiSelect > div > div {
            background-color: #1A1C23 !important;
            border: 1px solid #2D2E3A !important;
            color: #F9FAFB !important;
        }
        
        /* Dropdown menu items */
        [data-baseweb="menu"] {
            background-color: #1A1C23 !important;
            border: 1px solid #2D2E3A !important;
        }
        
        [data-baseweb="menu"] li {
            background-color: #1A1C23 !important;
            color: #F9FAFB !important;
        }
        
        [data-baseweb="menu"] li:hover {
            background-color: #2D2E3A !important;
        }
        
        /* Input fields (text, number, etc.) */
        .stTextInput input,
        .stNumberInput input {
            background-color: #1A1C23 !important;
            border: 1px solid #2D2E3A !important;
            color: #F9FAFB !important;
            border-radius: 8px !important;
        }
        
        .stTextInput input:focus,
        .stNumberInput input:focus {
            border-color: #7C3AED !important;
            box-shadow: 0 0 0 2px rgba(124, 58, 237, 0.3) !important;
        }
        
        /* Slider */
        .stSlider > div > div > div {
            background-color: #2D2E3A !important;
        }
        
        .stSlider > div > div > div > div {
            background-color: #7C3AED !important;
        }
        
        /* Checkbox and Radio */
        .stCheckbox label,
        .stRadio label {
            color: #F9FAFB !important;
        }
        
        /* Success, Info, Warning, Error messages */
        .stAlert {
            background-color: #1A1C23 !important;
            border: 1px solid #2D2E3A !important;
            color: #F9FAFB !important;
        }
        
        [data-testid="stNotificationContentSuccess"] {
            background-color: rgba(16, 185, 129, 0.1) !important;
            border-left: 3px solid #10B981 !important;
        }
        
        [data-testid="stNotificationContentInfo"] {
            background-color: rgba(59, 130, 246, 0.1) !important;
            border-left: 3px solid #3B82F6 !important;
        }
        
        [data-testid="stNotificationContentWarning"] {
            background-color: rgba(245, 158, 11, 0.1) !important;
            border-left: 3px solid #F59E0B !important;
        }
        
        [data-testid="stNotificationContentError"] {
            background-color: rgba(239, 68, 68, 0.1) !important;
            border-left: 3px solid #EF4444 !important;
        }
        
        /* Spinner */
        .stSpinner > div {
            border-color: #7C3AED !important;
        }
        
        /* Progress bar */
        .stProgress > div > div {
            background-color: #2D2E3A !important;
        }
        
        .stProgress > div > div > div {
            background-color: #7C3AED !important;
        }
        
        /* Download button */
        .stDownloadButton > button {
            background: linear-gradient(180deg, #2E303E 0%, #1F2128 100%) !important;
            color: #F9FAFB !important;
            border: 1px solid #3F4152 !important;
        }
        
        .stDownloadButton > button:hover {
            border-color: #7C3AED !important;
            box-shadow: 0 4px 12px rgba(124, 58, 237, 0.2) !important;
        }
        
        /* Form submit button */
        .stFormSubmitButton > button {
            background: linear-gradient(180deg, #7C3AED 0%, #6D28D9 100%) !important;
            color: #F9FAFB !important;
            border: none !important;
            font-weight: 600 !important;
        }
        
        .stFormSubmitButton > button:hover {
            background: linear-gradient(180deg, #8B5CF6 0%, #7C3AED 100%) !important;
            box-shadow: 0 4px 12px rgba(124, 58, 237, 0.4) !important;
        }
        
        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {
            background-color: transparent !important;
            border-bottom: 1px solid #2D2E3A !important;
        }
        
        .stTabs [data-baseweb="tab"] {
            color: #94A3B8 !important;
            background-color: transparent !important;
        }
        
        .stTabs [aria-selected="true"] {
            color: #7C3AED !important;
            border-bottom-color: #7C3AED !important;
        }
        
        /* Expander content */
        .streamlit-expanderContent {
            background-color: #15171E !important;
            border: 1px solid #2D2E3A !important;
            border-top: none !important;
        }
        
        /* Code blocks */
        .stCodeBlock {
            background-color: #1A1C23 !important;
            border: 1px solid #2D2E3A !important;
        }
        
        code {
            background-color: #1A1C23 !important;
            color: #E2E8F0 !important;
            padding: 2px 6px !important;
            border-radius: 4px !important;
        }
        
        /* Dataframe/Table */
        .stDataFrame {
            background-color: #1A1C23 !important;
            border: 1px solid #2D2E3A !important;
        }
        
        /* Metric */
        [data-testid="stMetricValue"] {
            color: #F9FAFB !important;
        }
        
        [data-testid="stMetricLabel"] {
            color: #94A3B8 !important;
        }
        
        /* Caption text */
        .stCaption {
            color: #94A3B8 !important;
        }
        
        /* Divider */
        hr {
            border-color: #2D2E3A !important;
        }
        
        /* Markdown links */
        a {
            color: #7C3AED !important;
        }
        
        a:hover {
            color: #8B5CF6 !important;
        }
    </style>
    """, unsafe_allow_html=True)

inject_custom_css()


def init_state():
    if "workflow_state" not in st.session_state:
        st.session_state.workflow_state = {
            "raw_input": "",
            "current_spec": "",
            "can_proceed": False,
            "metadata": {},
            "feedback": "",
            "ui_queue": [],
            "messages": [],
            "components": {name: None for name in PRD_COMPONENT_NAMES},
            "gaps": PRD_COMPONENT_NAMES.copy(),
            "last_updated_component": None,
            "is_spec_complete": False,
            "awaiting_user_input": True,
            "detailed_components": {},
            "is_detailed": False,
            "question_answers": {},
        }
    if "thread_id" not in st.session_state:
        st.session_state.thread_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    if "initialized" not in st.session_state:
        st.session_state.initialized = False
    if "is_processing" not in st.session_state:
        st.session_state.is_processing = False
    if "show_logs" not in st.session_state:
        st.session_state.show_logs = False


init_state()


def render_sidebar_exports():
    """Render export buttons in sidebar - always accessible."""
    with st.sidebar:
        st.title("Spec Builder")
        st.markdown("---")
        st.markdown("### Export Spec")
        
        components = st.session_state.workflow_state.get("components", {})
        detailed_components = st.session_state.workflow_state.get("detailed_components", {})
        is_detailed = st.session_state.workflow_state.get("is_detailed", False)
        
        has_content = any(v for v in components.values() if v)
        
        if not has_content:
            st.caption("Add content to enable exports")
            return
        
        export_source = detailed_components if is_detailed else None
        source_label = "Detailed" if is_detailed else "Draft"
        st.caption(f"Export source: {source_label}")
        
        md_content = export_to_markdown(components, export_source)
        st.download_button(
            "Download Markdown",
            md_content,
            file_name="spec.md",
            mime="text/markdown",
            use_container_width=True,
            key="sidebar_md_download"
        )
        
        try:
            pdf_content = export_to_pdf(components, export_source)
            st.download_button(
                "Download PDF",
                pdf_content,
                file_name="spec.pdf",
                mime="application/pdf",
                use_container_width=True,
                key="sidebar_pdf_download"
            )
        except Exception as e:
            st.caption(f"PDF export unavailable: {e}")
        
        st.divider()
        
        st.markdown("### Actions")
        if st.button("Reset Spec", type="secondary", use_container_width=True, key="sidebar_reset"):
            st.session_state.workflow_state = {
                "raw_input": "",
                "current_spec": "",
                "can_proceed": False,
                "metadata": {},
                "feedback": "",
                "ui_queue": [],
                "messages": [],
                "components": {name: None for name in PRD_COMPONENT_NAMES},
                "gaps": PRD_COMPONENT_NAMES.copy(),
                "last_updated_component": None,
                "is_spec_complete": False,
                "awaiting_user_input": True,
                "detailed_components": {},
                "is_detailed": False,
                "question_answers": {},
            }
            st.rerun()


render_sidebar_exports()


async def run_component_master(user_input: str, target_component: str = None):
    """Run component master with new input."""
    state = st.session_state.workflow_state.copy()
    state["raw_input"] = user_input
    state["awaiting_user_input"] = False
    if target_component:
        state["last_updated_component"] = target_component
    
    config = {"configurable": {"thread_id": st.session_state.thread_id}}
    
    result = await app.ainvoke(state, config)
    st.session_state.workflow_state = result


async def run_refiner(question_answers: Dict[str, Dict[int, str]]):
    """Run refiner node to process question answers."""
    state = st.session_state.workflow_state.copy()
    state["question_answers"] = question_answers
    
    # Manually invoke refiner node since it's not in the main flow
    from src.nodes.refiner import refiner_node
    result = refiner_node(state)
    
    # Update state with refinement results
    st.session_state.workflow_state["detailed_components"] = result["detailed_components"]
    st.session_state.workflow_state["question_answers"] = result["question_answers"]


def run_workflow_sync(user_input: str, target_component: str = None):
    """Sync wrapper for async workflow."""
    try:
        event_loop.run_until_complete(run_component_master(user_input, target_component))
    except RuntimeError as e:
        if "Event loop is closed" in str(e):
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            new_loop.run_until_complete(run_component_master(user_input, target_component))
        else:
            raise


def run_refiner_sync(question_answers: Dict[str, Dict[int, str]]):
    """Sync wrapper for refiner node."""
    try:
        event_loop.run_until_complete(run_refiner(question_answers))
    except RuntimeError as e:
        if "Event loop is closed" in str(e):
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            new_loop.run_until_complete(run_refiner(question_answers))
        else:
            raise


def count_words(text):
    if not text:
        return 0
    return len(text.split())


def render_detailed_spec_display():
    """Render the detailed spec with elaborated text and question dropdowns for answers."""
    detailed_components = st.session_state.workflow_state.get("detailed_components", {})
    components = st.session_state.workflow_state.get("components", {})
    
    st.markdown("### Detailed Specification")
    st.success("Your specification has been elaborated. Answer any questions below to refine further.")
    
    # Create a dict to track answers for this render
    current_answers = {}
    
    for name in PRD_COMPONENT_NAMES:
        detail = detailed_components.get(name, {})
        text = detail.get("text") or components.get(name)
        questions = detail.get("questions", [])
        
        st.markdown(f"""
        <div class="component-card component-detailed">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <strong>{name}</strong>
                <span style="font-size: 12px; color: #4F46E5; font-weight: 500; background: #EEF2FF; padding: 2px 8px; border-radius: 12px;">Detailed</span>
            </div>
            <div style="color: #E2E8F0; font-size: 14px; line-height: 1.6; margin-bottom: 12px;">
                {text if text else '<em style="color: #94A3B8;">No information provided</em>'}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if questions:
            with st.expander(f"Follow-up questions for {name}"):
                current_answers[name] = {}
                
                for q_idx, question in enumerate(questions):
                    answer = st.text_area(
                        question,
                        value="",
                        height=80,
                        key=f"qa_{name}_{q_idx}",
                        label_visibility="visible",
                        disabled=st.session_state.is_processing
                    )
                    
                    if answer.strip():
                        current_answers[name][q_idx] = answer
                
                if current_answers.get(name):
                    if st.button(f"Refine {name} with answers", key=f"refine_{name}", use_container_width=True, disabled=st.session_state.is_processing):
                        st.session_state.question_answers = current_answers
                        st.session_state.is_processing = True
                        st.rerun()
        
        st.markdown("<br>", unsafe_allow_html=True)
    
    # Process refinement if questions were answered
    if st.session_state.is_processing and st.session_state.question_answers:
        with st.spinner("Refining your specification with the provided answers..."):
            run_refiner_sync(st.session_state.question_answers)
            st.session_state.is_processing = False
            st.rerun()


def render_spec_display():
    """Render all 7 components in a stable container."""
    components = st.session_state.workflow_state.get("components", {})
    gaps = st.session_state.workflow_state.get("gaps", [])
    
    st.markdown("### Live Specification")
    
    for name in PRD_COMPONENT_NAMES:
        text = components.get(name)
        is_complete = name not in gaps
        word_count = count_words(text)
        
        status_class = "component-complete" if is_complete else "component-incomplete"
        status_indicator = "Complete" if is_complete else "Incomplete"
        status_text = f"{word_count} words" if text else "Missing"
        
        st.markdown(f"""
        <div class="component-card {status_class}">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <strong>{name}</strong>
                <span style="font-size: 12px; font-weight: 500; color: {'#059669' if is_complete else '#D97706'}; background: {'#ECFDF5' if is_complete else '#FFFBEB'}; padding: 2px 8px; border-radius: 12px;">{status_text}</span>
            </div>
            <div style="color: #E2E8F0; font-size: 14px; line-height: 1.6;">
                {text if text else '<em style="color: #94A3B8;">No information provided yet</em>'}
            </div>
        </div>
        """, unsafe_allow_html=True)


@st.fragment
def render_gap_inputs():
    """Fragment for gap input forms - only reruns this section on interaction."""
    gaps = st.session_state.workflow_state.get("gaps", [])
    
    if not gaps:
        st.success("Specification complete. All components have sufficient detail.")
        st.info("Your spec is being refined with additional insights...")
        return
    
    st.markdown("### Fill in the Gaps")
    st.caption(f"The following {len(gaps)} component(s) need more detail (minimum {MIN_WORDS_THRESHOLD} words each):")
    
    for gap_name in gaps:
        with st.container():
            st.markdown(f"**{gap_name}**")
            
            current_text = st.session_state.workflow_state.get("components", {}).get(gap_name, "") or ""
            
            user_input = st.text_area(
                f"Add details for {gap_name}",
                value="",
                placeholder=f"Describe the {gap_name.lower()} for your product/feature...",
                height=100,
                key=f"input_{gap_name}",
                label_visibility="collapsed",
                disabled=st.session_state.is_processing
            )
            
            col1, col2 = st.columns([1, 4])
            with col1:
                if st.button("Add", key=f"btn_{gap_name}", use_container_width=True, disabled=st.session_state.is_processing):
                    if user_input.strip():
                        st.session_state.is_processing = True
                        st.rerun()
                    else:
                        st.warning("Please enter some text first")
            
            # Process submission if button was pressed
            if st.session_state.is_processing and user_input.strip():
                with st.spinner("Processing your input..."):
                    combined_input = f"{gap_name}: {user_input}"
                    if current_text:
                        combined_input = f"{gap_name}: {current_text} {user_input}"
                    
                    logger.info(f"Adding input for {gap_name}")
                    run_workflow_sync(combined_input, gap_name)
                    st.session_state.is_processing = False
                    st.rerun()
            
            st.divider()


def render_initial_input():
    """Render the initial PRD input form."""
    st.markdown("### Start Your Specification")
    st.caption("Describe your product idea, feature, or project requirements.")

    # Display feedback if sanity check fails - logic moved here
    feedback = st.session_state.workflow_state.get("feedback")
    can_proceed = st.session_state.workflow_state.get("can_proceed", True)
    
    if feedback and not can_proceed:
        st.error(f"Need more details: {feedback}")

    
    with st.form("initial_input_form"):
        user_input = st.text_area(
            "Describe your idea",
            placeholder="Share some details of what you want to build. I will help you elaborate it.",
            height=200,
            disabled=st.session_state.is_processing
        )
        
        submitted = st.form_submit_button("Analyze and Extract Components", use_container_width=True, disabled=st.session_state.is_processing)
        
        if submitted and user_input.strip():
            st.session_state.is_processing = True
            st.session_state.show_logs = False
            st.rerun()
    
    # Process initial submission with loader and hidden logs
    if st.session_state.is_processing and user_input.strip():
        with st.spinner("Analyzing your specification and extracting components..."):
            logger.info("Processing initial input...")
            run_workflow_sync(user_input)
            st.session_state.is_processing = False
            st.rerun()


st.markdown("""
<div style="margin-bottom: 30px;">
    <h1 style="font-size: 2.5rem; margin-bottom: 8px;">SpecBuilder</h1>
    <p style="font-size: 1.1rem; color: #64748B; margin: 0;">Save time and rework in writing high quality specs with SpecBuilder </p>
</div>
""", unsafe_allow_html=True)

components = st.session_state.workflow_state.get("components", {})
has_any_content = any(v for v in components.values() if v)
is_detailed = st.session_state.workflow_state.get("is_detailed", False)
is_complete = st.session_state.workflow_state.get("is_spec_complete", False)

if not has_any_content:
    render_initial_input()
elif is_detailed:
    render_detailed_spec_display()
    
    st.markdown("---")
    st.markdown("### Export Your Specification")
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        md_content = export_to_markdown(components, st.session_state.workflow_state.get("detailed_components", {}))
        st.download_button(
            "Download Markdown",
            md_content,
            file_name="spec.md",
            mime="text/markdown",
            use_container_width=True,
            key="main_md_download"
        )
    with col2:
        try:
            pdf_content = export_to_pdf(components, st.session_state.workflow_state.get("detailed_components", {}))
            st.download_button(
                "Download PDF",
                pdf_content,
                file_name="spec.pdf",
                mime="application/pdf",
                use_container_width=True,
                key="main_pdf_download"
            )
        except Exception as e:
            st.caption(f"PDF unavailable: {e}")
else:
    col1, col2 = st.columns([1, 1], gap="large")
    
    with col1:
        render_gap_inputs()
    
    with col2:
        render_spec_display()
    
    if is_complete:
        st.markdown("---")
        st.info("Your specification is complete. Refining with additional details...")
