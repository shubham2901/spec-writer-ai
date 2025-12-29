import os
import json
from typing import Dict, Any
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from src.state import AgentState
from src.persona import SYSTEM_PERSONA, MODEL_NAME

# Load environment variables
load_dotenv()

SANITY_CHECK_PROMPT = """
Analyze this user input to determine if it has ENOUGH INFORMATION to begin specification writing.

User Input:
{user_input}

CRITERIA FOR "can_proceed": TRUE
---
Accept input if it provides:
- A clear problem statement OR feature idea
- At least some context about what the system should do
- Reasonable length (3+ sentences minimum)

CRITERIA FOR "can_proceed": FALSE
---
Reject ONLY if the input is:
- Extremely vague or single-word/phrase
- Missing any sense of purpose or use case
- Clearly incomplete or placeholder text

DO NOT reject just because it lacks "perfect" detail—our workflow will gather that iteratively.

User Input Analysis:
{user_input}

RESPOND WITH ONLY VALID JSON (no markdown, no explanation):
{{
  "can_proceed": true/false,
  "feedback": "Constructive sentence explaining the decision",
  "metadata": {{
    "maturity": "Greenfield" | "Brownfield" | null,
    "environment": "Web" | "Mobile" | "Backend" | null
  }}
}}
"""

import re
import logging

logger = logging.getLogger(__name__)

def sanity_checker_node(state: AgentState) -> AgentState:
    """True implementation of sanity checker using centralized model name."""
    
    logger.info("Sanity Checker Node started.")
    
    # Using 'rest' transport can sometimes resolve 404/connectivity issues
    llm = ChatGoogleGenerativeAI(
        model=MODEL_NAME
    )
    
    # Use replace to avoid KeyError if the user input contains curly braces
    prompt = SANITY_CHECK_PROMPT.replace("{user_input}", state["raw_input"])
    
    messages = [
        ("system", SYSTEM_PERSONA),
        ("human", prompt)
    ]
    
    logger.debug(f"Sending prompt to LLM: {prompt[:100]}...")
    
    try:
        response = llm.invoke(messages)
        text = response.content
        logger.info(f"Received response from LLM (type: {type(text)}): {str(text)[:200]}...")
    except Exception as e:
        logger.error(f"Error invoking LLM: {e}")
        return {**state, "can_proceed": False, "feedback": f"Error calling AI: {e}", "metadata": {}}
    
    # Handle case where response.content might be a list of blocks
    if isinstance(text, list):
        # Extract text from dict blocks (e.g., {'type': 'text', 'text': '...'})
        logger.info("Response is a list, extracting text...")
        text = "".join([block.get("text", "") if isinstance(block, dict) else str(block) for block in text])
        logger.debug(f"Extracted text: {text[:200]}...")
    
    # Robust JSON extraction: handle markdown backticks if present
    json_match = re.search(r'\{.*\}', text, re.DOTALL)
    if json_match:
        try:
            content = json.loads(json_match.group(0))
            logger.info(f"Successfully parsed JSON content. can_proceed={content.get('can_proceed')}")
            logger.debug(f"Full JSON: {json.dumps(content, indent=2)}")
        except json.JSONDecodeError as e:
            logger.error(f"JSON Decode Error: {e}. Raw text: {text}")
            # Fallback: Use raw text as feedback if JSON parse fails
            content = {"can_proceed": False, "feedback": text, "metadata": {}}
    else:
        logger.warning(f"No JSON found in response. Raw text: {text}")
        # Fallback: Use raw text as feedback if no JSON found
        content = {"can_proceed": False, "feedback": text, "metadata": {}}
    
    can_proceed = content.get("can_proceed", False)
    feedback = content.get("feedback", "Sanity check failed to generate feedback.")
    logger.info(f"Sanity check result: can_proceed={can_proceed}, feedback={feedback}")
    
    return {
        **state,
        "can_proceed": can_proceed,
        "feedback": feedback,
        "metadata": content.get("metadata", {"maturity": None, "environment": None}),
        "messages": state.get("messages", []) + [{"role": "ai", "content": "Sanity check completed."}]
    }