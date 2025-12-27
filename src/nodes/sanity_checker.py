import os
import json
from typing import Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from src.state import AgentState
from src.persona import SYSTEM_PERSONA, MODEL_NAME

SANITY_CHECK_PROMPT = """
You are a sanity checker for technical specifications. 
Analyze the following user input:
{user_input}

Determine if the input is descriptive enough to start writing a technical spec (at least 5 lines of meaningful text).
Also, try to extract project metadata if possible:
- "maturity": "Greenfield" or "Brownfield"
- "environment": "Web", "Mobile", "Backend", etc.

Return a JSON object with:
- "can_proceed": bool (True if descriptive enough)
- "feedback": str (constructive feedback for the user)
- "metadata": {
    "maturity": str or null,
    "environment": str or null
  }
"""

import re
import logging

logger = logging.getLogger(__name__)

# Module-level LLM client (created once at import time)
_llm = ChatGoogleGenerativeAI(model=MODEL_NAME)

async def sanity_checker_node(state: AgentState) -> AgentState:
    """True implementation of sanity checker using centralized model name."""
    
    logger.info("Sanity Checker Node started.")
    
    llm = _llm
    
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
            content = {"can_proceed": False, "feedback": f"Failed to parse JSON. Raw: {text[:100]}...", "metadata": {}}
    else:
        logger.warning(f"No JSON found in response. Raw text: {text}")
        content = {"can_proceed": False, "feedback": f"No JSON found in response. Raw: {text[:100]}...", "metadata": {}}
    
    return {
        **state,
        "can_proceed": content.get("can_proceed", False),
        "feedback": content.get("feedback", "Sanity check failed to generate feedback."),
        "metadata": content.get("metadata", {"maturity": None, "environment": None}),
        "messages": state.get("messages", []) + [{"role": "ai", "content": "Sanity check completed."}]
    }