import json
import logging
from typing import Dict, Any, List, Optional

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

from src.state import AgentState
from src.persona import MODEL_NAME
from src.knowledge_base import (
    COMPONENT_EXTRACTION_PROMPT,
    PRD_COMPONENT_NAMES,
    MIN_WORDS_THRESHOLD,
    get_component_descriptions_text,
)

logger = logging.getLogger(__name__)


def count_words(text: Optional[str]) -> int:
    if not text:
        return 0
    return len(text.split())


def detect_gaps(components: Dict[str, Optional[str]]) -> List[str]:
    gaps = []
    for name in PRD_COMPONENT_NAMES:
        text = components.get(name)
        if count_words(text) < MIN_WORDS_THRESHOLD:
            gaps.append(name)
    return gaps


def component_master_node(state: AgentState) -> Dict[str, Any]:
    print("\n=== COMPONENT_MASTER NODE: START ===")
    logger.info("component_master: Starting PRD component extraction")
    
    raw_input = state.get("raw_input", "")
    current_components = state.get("components", {})
    
    if not current_components:
        current_components = {name: None for name in PRD_COMPONENT_NAMES}
    
    if not raw_input.strip():
        print("=== COMPONENT_MASTER NODE: Empty input, checking existing components ===")
        gaps = detect_gaps(current_components)
        is_complete = len(gaps) == 0
        return {
            "components": current_components,
            "gaps": gaps,
            "is_spec_complete": is_complete,
            "feedback": "No new input provided." if not is_complete else "Spec complete!",
        }
    
    llm = ChatGoogleGenerativeAI(
        model=MODEL_NAME,
        temperature=0,
        response_mime_type="application/json",
    )
    
    current_components_str = json.dumps(current_components, indent=2)
    
    prompt = COMPONENT_EXTRACTION_PROMPT.format(
        component_descriptions=get_component_descriptions_text(),
        current_components=current_components_str,
        raw_input=raw_input,
    )
    
    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        result_content = response.content
        
        def extract_json_from_text(text: str) -> dict:
            text = text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            return json.loads(text.strip())
        
        if isinstance(result_content, dict):
            result = result_content
        elif isinstance(result_content, list):
            first_item = result_content[0] if result_content else {}
            if isinstance(first_item, dict) and "text" in first_item:
                result = extract_json_from_text(first_item["text"])
            elif isinstance(first_item, dict):
                result = first_item
            elif isinstance(first_item, str):
                result = extract_json_from_text(first_item)
            else:
                result = {}
        elif isinstance(result_content, str) and result_content.strip():
            result = extract_json_from_text(result_content)
        else:
            raise ValueError(f"Empty or invalid response: {result_content}")
        
        components = result.get("components", current_components)
        
        for name in PRD_COMPONENT_NAMES:
            if name not in components:
                components[name] = current_components.get(name)
        
        gaps = detect_gaps(components)
        is_complete = len(gaps) == 0
        
        print(f"=== COMPONENT_MASTER NODE: gaps={gaps}, is_complete={is_complete} ===")
        logger.info(f"component_master: gaps={gaps}, is_complete={is_complete}")
        
        return {
            "components": components,
            "gaps": gaps,
            "is_spec_complete": is_complete,
            "raw_input": "",
            "feedback": "Spec complete!" if is_complete else f"Missing details for: {', '.join(gaps)}",
        }
        
    except json.JSONDecodeError as e:
        error_msg = f"Failed to parse LLM response as JSON: {e}"
        print(f"=== COMPONENT_MASTER NODE: ERROR - {error_msg} ===")
        logger.error(f"component_master: {error_msg}")
        gaps = detect_gaps(current_components)
        return {
            "components": current_components,
            "gaps": gaps,
            "is_spec_complete": False,
            "feedback": error_msg,
        }
    except Exception as e:
        error_msg = f"LLM invocation failed: {e}"
        print(f"=== COMPONENT_MASTER NODE: ERROR - {error_msg} ===")
        logger.error(f"component_master: {error_msg}")
        gaps = detect_gaps(current_components)
        return {
            "components": current_components,
            "gaps": gaps,
            "is_spec_complete": False,
            "feedback": error_msg,
        }
    finally:
        print("=== COMPONENT_MASTER NODE: END ===\n")
