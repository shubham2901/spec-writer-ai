import json
import logging
from typing import Dict, Any, Optional

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

from src.state import AgentState
from src.persona import MODEL_NAME
from src.knowledge_base import PRD_COMPONENT_NAMES

logger = logging.getLogger(__name__)


DETAILER_PROMPT = """You are a PRD (Product Requirements Document) editor. Your task is to elaborate and refine each component without adding new functional requirements.

## Instructions:
1. **Elaborate**: Clean up and structure the text for clarity. Fix grammar, improve flow, but DO NOT add new features or requirements.
2. **Question Generation**: Generate exactly 3 targeted questions that would help deepen the detail for this component.

## Component to Detail:
**{component_name}**

Current Text:
{component_text}

## Output Format:
Return a JSON object with this exact structure:
{{
  "text": "The elaborated and cleaned up text",
  "questions": [
    "First targeted question to deepen detail?",
    "Second targeted question to deepen detail?",
    "Third targeted question to deepen detail?"
  ]
}}

Keep the elaborated text faithful to the original intent. Questions should be specific, not generic.
"""


def detailer_node(state: AgentState) -> Dict[str, Any]:
    print("\n=== DETAILER NODE: START ===")
    logger.info("detailer: Starting component elaboration")
    
    components = state.get("components", {})
    
    if not components or not any(v for v in components.values() if v):
        print("=== DETAILER NODE: No components to detail ===")
        return {
            "detailed_components": {},
            "is_detailed": False,
            "feedback": "No components available to detail.",
        }
    
    llm = ChatGoogleGenerativeAI(
        model=MODEL_NAME,
        temperature=0.3,
        response_mime_type="application/json",
    )
    
    detailed_components = {}
    
    for name in PRD_COMPONENT_NAMES:
        text = components.get(name)
        
        if not text:
            detailed_components[name] = {
                "text": None,
                "questions": []
            }
            continue
        
        prompt = DETAILER_PROMPT.format(
            component_name=name,
            component_text=text,
        )
        
        try:
            response = llm.invoke([HumanMessage(content=prompt)])
            result_content = response.content
            
            def extract_json_from_text(text_input: str) -> dict:
                text_input = text_input.strip()
                if text_input.startswith("```json"):
                    text_input = text_input[7:]
                if text_input.startswith("```"):
                    text_input = text_input[3:]
                if text_input.endswith("```"):
                    text_input = text_input[:-3]
                return json.loads(text_input.strip())
            
            if isinstance(result_content, dict):
                result = result_content
            elif isinstance(result_content, list):
                first_item = result_content[0] if result_content else {}
                if isinstance(first_item, dict) and "text" in first_item and "questions" not in first_item:
                    result = extract_json_from_text(first_item.get("text", "{}"))
                elif isinstance(first_item, dict):
                    result = first_item
                elif isinstance(first_item, str):
                    result = extract_json_from_text(first_item)
                else:
                    result = {"text": text, "questions": []}
            elif isinstance(result_content, str) and result_content.strip():
                result = extract_json_from_text(result_content)
            else:
                result = {"text": text, "questions": []}
            
            detailed_components[name] = {
                "text": result.get("text", text),
                "questions": result.get("questions", [])[:3]
            }
            
            print(f"=== DETAILER NODE: Processed {name} ===")
            logger.info(f"detailer: Processed {name}")
            
        except Exception as e:
            logger.error(f"detailer: Error processing {name}: {e}")
            detailed_components[name] = {
                "text": text,
                "questions": []
            }
    
    print(f"=== DETAILER NODE: Detailed {len([c for c in detailed_components.values() if c.get('text')])} components ===")
    logger.info(f"detailer: Completed detailing all components")
    
    print("=== DETAILER NODE: END ===\n")
    
    return {
        "detailed_components": detailed_components,
        "is_detailed": True,
        "feedback": "Spec has been elaborated with recommended questions.",
    }
