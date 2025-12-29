import os
import json
from typing import Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from src.state import AgentState
from src.persona import SYSTEM_PERSONA, MODEL_NAME

SANITY_CHECK_PROMPT = """
Analyze the following user input for technical specification suitability:
{user_input}

Task:
1. Determine if the input is descriptive enough to start writing a technical spec (at least 5 lines of meaningful text).
2. Extract project metadata if possible.

Return a JSON object with:
- "can_proceed": bool (True if descriptive enough)
- "feedback": str (Constructive feedback for the user in the voice and tone of the System Persona defined above. Use the 'Missing Foundations' structure if rejecting.)
- "metadata": {
    "maturity": "Greenfield" | "Brownfield" | null,
    "environment": "Web" | "Mobile" | "Backend" | null
  }
"""

import re
import logging

logger = logging.getLogger(__name__)

async def sanity_checker_node(state: AgentState) -> AgentState:
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
        response = await llm.ainvoke(messages)
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
            logger.info("Successfully parsed JSON content.")
        except json.JSONDecodeError as e:
            logger.error(f"JSON Decode Error: {e}. Raw text: {text}")
            # Fallback: Use raw text as feedback if JSON parse fails
            content = {"can_proceed": False, "feedback": text, "metadata": {}}
    else:
        logger.warning(f"No JSON found in response. Raw text: {text}")
        # Fallback: Use raw text as feedback if no JSON found
        content = {"can_proceed": False, "feedback": text, "metadata": {}}
    
    return {
        **state,
        "can_proceed": content.get("can_proceed", False),
        "feedback": content.get("feedback", "Sanity check failed to generate feedback."),
        "metadata": content.get("metadata", {"maturity": None, "environment": None}),
        "messages": state.get("messages", []) + [{"role": "ai", "content": "Sanity check completed."}]
    }