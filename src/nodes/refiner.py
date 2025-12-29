import json
import logging
from typing import Dict, Any

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

from src.state import AgentState
from src.persona import MODEL_NAME
from src.knowledge_base import PRD_COMPONENT_NAMES

logger = logging.getLogger(__name__)


REFINER_PROMPT = """You are a specification refinement expert. Your task is to improve a component based on additional answers provided by the user.

## Component: {component_name}

### Current Text:
{current_text}

### User's Answers to Follow-up Questions:
{answers_text}

## Instructions:
1. **Integration**: Seamlessly integrate the user's answers into the current component text.
2. **Coherence**: Maintain consistency with the existing content while incorporating new details.
3. **Clarity**: Enhance clarity without losing the original intent.
4. **No Hallucination**: Only use information provided by the user. Do not invent details.

## Output Format:
Return a JSON object with this exact structure:
{{
  "text": "The improved and integrated text"
}}

Keep the refined text professional and comprehensive.
"""


def refiner_node(state: AgentState) -> Dict[str, Any]:
    """Refine components based on question answers."""
    print("\n=== REFINER NODE: START ===")
    logger.info("refiner: Starting component refinement based on answers")
    
    question_answers = state.get("question_answers", {})
    detailed_components = state.get("detailed_components", {})
    
    if not question_answers:
        print("=== REFINER NODE: No answers to process ===")
        return {
            "detailed_components": detailed_components,
            "question_answers": {},
            "feedback": "No answers provided for refinement.",
        }
    
    llm = ChatGoogleGenerativeAI(
        model=MODEL_NAME,
        temperature=0.3,
        response_mime_type="application/json",
    )
    
    updated_components = detailed_components.copy()
    
    for component_name, answers_dict in question_answers.items():
        if not answers_dict or not any(answers_dict.values()):
            continue
        
        current_text = detailed_components.get(component_name, {}).get("text")
        current_questions = detailed_components.get(component_name, {}).get("questions", [])
        
        if not current_text:
            print(f"=== REFINER NODE: Skipping {component_name} - no current text ===")
            continue
        
        # Build answers text from the answers dict
        answers_text_lines = []
        for q_idx, answer in answers_dict.items():
            if answer and q_idx < len(current_questions):
                question = current_questions[q_idx]
                answers_text_lines.append(f"Q: {question}\nA: {answer}")
        
        if not answers_text_lines:
            continue
        
        answers_text = "\n\n".join(answers_text_lines)
        
        prompt = REFINER_PROMPT.format(
            component_name=component_name,
            current_text=current_text,
            answers_text=answers_text,
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
            elif isinstance(result_content, str) and result_content.strip():
                result = extract_json_from_text(result_content)
            else:
                result = {"text": current_text}
            
            updated_components[component_name] = {
                "text": result.get("text", current_text),
                "questions": current_questions
            }
            
            print(f"=== REFINER NODE: Refined {component_name} ===")
            logger.info(f"refiner: Refined {component_name} with user answers")
            
        except Exception as e:
            logger.error(f"refiner: Error refining {component_name}: {e}")
            # Keep the original if refinement fails
            pass
    
    print(f"=== REFINER NODE: Refined {len([c for c in question_answers if question_answers[c]])} components ===")
    logger.info("refiner: Completed refinement")
    
    print("=== REFINER NODE: END ===\n")
    
    return {
        "detailed_components": updated_components,
        "question_answers": {},  # Clear answers after processing
        "feedback": "Components refined based on your answers.",
    }
