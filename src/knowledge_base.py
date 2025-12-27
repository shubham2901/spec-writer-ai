"""
PRD Components Knowledge Base
Shared definitions accessible by all nodes in the workflow.
"""

from typing import TypedDict, Optional, Dict, List

PRD_COMPONENT_NAMES: List[str] = [
    "Goal",
    "Problem Statement",
    "User Cohort",
    "Metrics",
    "Solutions",
    "Risks",
    "GTM",
]

MIN_WORDS_THRESHOLD = 10

PRD_COMPONENT_DESCRIPTIONS: Dict[str, str] = {
    "Goal": "The primary objective or outcome the product/feature aims to achieve. Should be clear, measurable, and time-bound if possible.",
    "Problem Statement": "The pain point, challenge, or gap that the product/feature addresses. Describes what is broken or missing.",
    "User Cohort": "The target audience or user segments who will benefit from this product/feature. Includes personas, demographics, or behavioral traits.",
    "Metrics": "Key Performance Indicators (KPIs) and success criteria to measure the impact. Includes quantitative targets or at least formulas to calculate the impact.",
    "Solutions": "Proposed approaches, features, or technical implementations to solve the problem and achieve the goal.",
    "Risks": "Potential obstacles, dependencies, technical debt, or uncertainties that could impact delivery or success.",
    "GTM": "Go-To-Market strategy including launch plans, marketing, sales enablement, and rollout phases.",
    "Others": "Catch-all bucket for Legal, Compliance, Finance, or any other details that don't fit the above categories.",
}


class PRDComponents(TypedDict):
    Goal: Optional[str]
    Problem_Statement: Optional[str]
    User_Cohort: Optional[str]
    Metrics: Optional[str]
    Solutions: Optional[str]
    Risks: Optional[str]
    GTM: Optional[str]
    Others: Optional[str]


class ComponentMasterOutput(TypedDict):
    components: Dict[str, Optional[str]]
    gaps: List[str]
    is_spec_complete: bool


COMPONENT_EXTRACTION_PROMPT = """You are a PRD (Product Requirements Document) analyst. Analyze the user's input and extract components into specific buckets.

## Component Definitions:
{component_descriptions}

## Instructions:
1. **Component Extraction**: Map every piece of the user's input into the 7 PRD components. Do NOT lose any information.
2. **Distribution Rule**: Every piece of information must be assigned to at least one component.

## Current Components State:
{current_components}

## New User Input to Integrate:
{raw_input}

## Output Format:
Return a JSON object with this exact structure:
{{
  "components": {{
    "Goal": "merged/updated text or null if empty",
    "Problem Statement": "merged/updated text or null",
    "User Cohort": "merged/updated text or null",
    "Metrics": "merged/updated text or null",
    "Solutions": "merged/updated text or null",
    "Risks": "merged/updated text or null",
    "GTM": "merged/updated text or null"
  }}
}}

Merge new input with existing components. Preserve existing content and add new details.
"""


def get_component_descriptions_text() -> str:
    return "\n".join(
        f"- **{name}**: {desc}" for name, desc in PRD_COMPONENT_DESCRIPTIONS.items()
    )
