import streamlit as st
import asyncio
import logging
from datetime import datetime
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

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    * { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important; }
    body, .stApp { background: #f5f3f9; color: #1A1A1A; min-height: 100vh; }
    h1, h2, h3, h4, h5, h6 { color: #1A1A1A !important; font-weight: 700 !important; }
    
    .stButton > button {
        background: linear-gradient(135deg, #a855f7 0%, #3b82f6 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        padding: 10px 20px !important;
        transition: all 0.3s ease !important;
    }
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 20px rgba(168, 85, 247, 0.3) !important;
    }
    
    .component-card {
        background: rgba(255, 255, 255, 0.8);
        backdrop-filter: blur(10px);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 16px;
        border: 1px solid rgba(168, 85, 247, 0.1);
    }
    .component-complete {
        border-left: 4px solid #22c55e;
    }
    .component-incomplete {
        border-left: 4px solid #f59e0b;
    }
    .component-detailed {
        border-left: 4px solid #6366f1;
    }
    
    .question-item {
        background: rgba(99, 102, 241, 0.08);
        border-radius: 8px;
        padding: 10px 14px;
        margin: 6px 0;
        font-size: 13px;
        color: #4338ca;
    }
    
    [data-testid="stHeader"] { display: none !important; }
</style>
""", unsafe_allow_html=True)


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
        }
    if "thread_id" not in st.session_state:
        st.session_state.thread_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    if "initialized" not in st.session_state:
        st.session_state.initialized = False


init_state()


def render_sidebar_exports():
    """Render export buttons in sidebar - always accessible."""
    with st.sidebar:
        st.markdown("### 📥 Export Spec")
        
        components = st.session_state.workflow_state.get("components", {})
        detailed_components = st.session_state.workflow_state.get("detailed_components", {})
        is_detailed = st.session_state.workflow_state.get("is_detailed", False)
        
        has_content = any(v for v in components.values() if v)
        
        if not has_content:
            st.caption("Add content to enable exports")
            return
        
        export_source = detailed_components if is_detailed else None
        source_label = "📝 Detailed" if is_detailed else "📋 Draft"
        st.caption(f"Export source: {source_label}")
        
        md_content = export_to_markdown(components, export_source)
        st.download_button(
            "📄 Download Markdown",
            md_content,
            file_name="spec.md",
            mime="text/markdown",
            use_container_width=True,
            key="sidebar_md_download"
        )
        
        try:
            pdf_content = export_to_pdf(components, export_source)
            st.download_button(
                "📑 Download PDF",
                pdf_content,
                file_name="spec.pdf",
                mime="application/pdf",
                use_container_width=True,
                key="sidebar_pdf_download"
            )
        except Exception as e:
            st.caption(f"PDF export unavailable: {e}")
        
        st.divider()
        
        st.markdown("### 🔄 Actions")
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


def count_words(text):
    if not text:
        return 0
    return len(text.split())


def render_detailed_spec_display():
    """Render the detailed spec with elaborated text and questions."""
    detailed_components = st.session_state.workflow_state.get("detailed_components", {})
    components = st.session_state.workflow_state.get("components", {})
    
    st.markdown("### 📋 Detailed Spec")
    st.success("✨ Your spec has been elaborated with recommended next steps!")
    
    for name in PRD_COMPONENT_NAMES:
        detail = detailed_components.get(name, {})
        text = detail.get("text") or components.get(name)
        questions = detail.get("questions", [])
        
        st.markdown(f"""
        <div class="component-card component-detailed">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <strong>✓ {name}</strong>
                <span style="font-size: 12px; color: #6366f1;">Detailed</span>
            </div>
            <div style="color: #333; font-size: 14px; line-height: 1.6; margin-bottom: 12px;">
                {text if text else '<em style="color: #999;">No information provided</em>'}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if questions:
            st.markdown("**🔍 Recommended Next Steps:**")
            for i, q in enumerate(questions, 1):
                st.markdown(f"""
                <div class="question-item">
                    {i}. {q}
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)


def render_spec_display():
    """Render all 7 components in a stable container."""
    components = st.session_state.workflow_state.get("components", {})
    gaps = st.session_state.workflow_state.get("gaps", [])
    
    st.markdown("### 📋 Live Spec")
    
    for name in PRD_COMPONENT_NAMES:
        text = components.get(name)
        is_complete = name not in gaps
        word_count = count_words(text)
        
        status_class = "component-complete" if is_complete else "component-incomplete"
        status_icon = "✓" if is_complete else "○"
        status_text = f"{word_count} words" if text else "Missing"
        
        st.markdown(f"""
        <div class="component-card {status_class}">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <strong>{status_icon} {name}</strong>
                <span style="font-size: 12px; color: {'#22c55e' if is_complete else '#f59e0b'};">{status_text}</span>
            </div>
            <div style="color: #333; font-size: 14px; line-height: 1.6;">
                {text if text else '<em style="color: #999;">No information provided yet</em>'}
            </div>
        </div>
        """, unsafe_allow_html=True)


@st.fragment
def render_gap_inputs():
    """Fragment for gap input forms - only reruns this section on interaction."""
    gaps = st.session_state.workflow_state.get("gaps", [])
    
    if not gaps:
        st.success("🎉 Spec Complete! All components have sufficient detail.")
        st.info("The Detailer is now elaborating your spec and generating recommended questions...")
        return
    
    st.markdown("### ✏️ Fill in the Gaps")
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
                label_visibility="collapsed"
            )
            
            col1, col2 = st.columns([1, 4])
            with col1:
                if st.button("Add", key=f"btn_{gap_name}", use_container_width=True):
                    if user_input.strip():
                        combined_input = f"{gap_name}: {user_input}"
                        if current_text:
                            combined_input = f"{gap_name}: {current_text} {user_input}"
                        
                        logger.info(f"Adding input for {gap_name}")
                        run_workflow_sync(combined_input, gap_name)
                        st.rerun()
                    else:
                        st.warning("Please enter some text first")
            
            st.divider()


def render_initial_input():
    """Render the initial PRD input form."""
    st.markdown("### 🚀 Start Your Spec")
    st.caption("Paste your product idea, feature description, or draft PRD below.")
    
    with st.form("initial_input_form"):
        user_input = st.text_area(
            "Describe your idea",
            placeholder="Share the details of what you want to build. Include goals, target users, success metrics, and any constraints.",
            height=200
        )
        
        submitted = st.form_submit_button("Analyze & Extract Components", use_container_width=True)
        
        if submitted and user_input.strip():
            logger.info("Processing initial input...")
            run_workflow_sync(user_input)
            st.rerun()


st.markdown("""
<div style="margin-bottom: 30px;">
    <h1 style="font-size: 2.5rem; margin-bottom: 8px;">Spec Writer</h1>
    <p style="font-size: 1.1rem; color: #666666; margin: 0;">Create technical specifications with AI-powered analysis</p>
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
    st.balloons()
    
    st.markdown("---")
    st.markdown("### 📥 Export Your Spec")
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        md_content = export_to_markdown(components, st.session_state.workflow_state.get("detailed_components", {}))
        st.download_button(
            "📄 Download Markdown",
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
                "📑 Download PDF",
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
        st.info("✨ Spec complete! The Detailer is elaborating your components...")
