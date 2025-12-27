"""
Test script for component_master node with gap detection.
Run: GOOGLE_API_KEY=<key> python test_components.py
"""

import logging
logging.getLogger("streamlit").setLevel(logging.ERROR)

from dotenv import load_dotenv
load_dotenv()

from src.nodes.component_master import component_master_node, detect_gaps, count_words
from src.state import AgentState
from src.knowledge_base import PRD_COMPONENT_NAMES, MIN_WORDS_THRESHOLD


def create_test_state(raw_input: str, existing_components: dict = None) -> AgentState:
    components = existing_components or {name: None for name in PRD_COMPONENT_NAMES}
    return {
        "raw_input": raw_input,
        "current_spec": "",
        "can_proceed": True,
        "metadata": {},
        "feedback": "",
        "ui_queue": [],
        "messages": [],
        "components": components,
        "gaps": detect_gaps(components),
        "last_updated_component": None,
        "is_spec_complete": False,
        "awaiting_user_input": False,
    }


def test_gap_detection():
    """Test the gap detection logic."""
    print("\n" + "=" * 60)
    print("TEST: Gap Detection Logic")
    print("=" * 60)
    
    components = {
        "Goal": "Increase retention by 25%",
        "Problem Statement": None,
        "User Cohort": "Active users aged 18-35 who have completed onboarding but show declining engagement patterns over the first 30 days.",
        "Metrics": "short",
        "Solutions": None,
        "Risks": None,
        "GTM": None,
    }
    
    for name, text in components.items():
        words = count_words(text)
        status = "✓ Complete" if words >= MIN_WORDS_THRESHOLD else f"✗ Incomplete ({words} words)"
        print(f"  {name}: {status}")
    
    gaps = detect_gaps(components)
    print(f"\nDetected gaps: {gaps}")
    print(f"Expected gaps: Goal, Problem Statement, Metrics, Solutions, Risks, GTM")
    
    return gaps


def test_sanity_failure():
    """Test Case 1: One liner draft (too vague)."""
    print("\n" + "=" * 60)
    print("TEST 1: One liner draft")
    print("=" * 60)
    
    raw_input = "Build an app for users"
    state = create_test_state(raw_input)
    result = component_master_node(state)
    
    print(f"\nInput: '{raw_input}'")
    print(f"is_spec_complete: {result.get('is_spec_complete')}")
    print(f"gaps: {result.get('gaps')}")
    print(f"feedback: {result.get('feedback')}")
    
    return result


def test_success_with_complete_prd():
    """Test Case 2: Full PRD with sufficient detail in all components."""
    print("\n" + "=" * 60)
    print("TEST 2: Complete PRD with all components")
    print("=" * 60)
    
    raw_input = """
Goal: Increase user retention by 25% within Q2 2025 by launching a comprehensive gamification system that rewards engagement.

Problem Statement: Our mobile app has a 60-day retention rate of only 15%. Users complete onboarding successfully but disengage within the first two weeks. Exit surveys consistently indicate lack of motivation and engagement as primary reasons for churn.

User Cohort: Active users aged 18-35 who have completed onboarding but show declining engagement patterns over the first 30 days. These are primarily urban professionals using the app for productivity.

Metrics: Primary KPI is 60-day retention rate with a target of 25% improvement. Secondary metrics include daily active users, average session duration, and feature adoption rate. We will also track streak completion rates.

Solutions: Implement a points and badges system for daily activities. Add daily streaks with escalating rewards for consecutive days of use. Create leaderboards for social competition among friends. Introduce milestone achievements for long-term engagement.

Risks: Over-gamification may alienate power users who prefer simplicity. Badge fatigue could reduce long-term effectiveness after initial novelty wears off. Development timeline may slip due to backend complexity of real-time leaderboards.

GTM: Soft launch to 10% of users in week 1 to gather feedback. Iterate on feedback for two weeks. Full rollout with in-app announcements and targeted push notification campaign. Partner with influencers for social proof.
"""
    
    state = create_test_state(raw_input)
    result = component_master_node(state)
    
    print(f"\nInput length: {len(raw_input)} chars")
    print(f"is_spec_complete: {result.get('is_spec_complete')}")
    print(f"gaps: {result.get('gaps')}")
    print(f"\nExtracted Components:")
    for key, value in result.get('components', {}).items():
        words = count_words(value)
        preview = value[:60] + "..." if value and len(value) > 60 else value
        print(f"  {key} ({words} words): {preview}")
    
    return result


def test_partial_prd():
    """Test Case 3: Partial PRD missing some components."""
    print("\n" + "=" * 60)
    print("TEST 3: Partial PRD (missing Metrics, Risks, GTM)")
    print("=" * 60)
    
    raw_input = """
Goal: Build a dark mode feature to improve user experience and reduce eye strain for our application users.

Problem Statement: Users have been requesting dark mode through support tickets. Many users work at night and find the bright interface uncomfortable.

User Cohort: Power users who spend more than 2 hours per day in the app, particularly those who work in low-light environments.

Solutions: Add a dark mode toggle in settings. Create alternate color palette with dark backgrounds. Update all UI components to support theme switching.
"""
    
    state = create_test_state(raw_input)
    result = component_master_node(state)
    
    print(f"\nInput length: {len(raw_input)} chars")
    print(f"is_spec_complete: {result.get('is_spec_complete')}")
    print(f"gaps: {result.get('gaps')}")
    print(f"\nExtracted Components:")
    for key, value in result.get('components', {}).items():
        words = count_words(value)
        status = "✓" if words >= MIN_WORDS_THRESHOLD else "✗"
        preview = value[:60] + "..." if value and len(value) > 60 else (value or "None")
        print(f"  {status} {key} ({words} words): {preview}")
    
    return result


def test_incremental_update():
    """Test Case 4: Adding to existing components."""
    print("\n" + "=" * 60)
    print("TEST 4: Incremental update (adding Metrics to partial spec)")
    print("=" * 60)
    
    existing_components = {
        "Goal": "Build a dark mode feature to improve user experience and reduce eye strain for our application users.",
        "Problem Statement": "Users have been requesting dark mode through support tickets. Many users work at night and find the bright interface uncomfortable.",
        "User Cohort": "Power users who spend more than 2 hours per day in the app, particularly those who work in low-light environments.",
        "Metrics": None,
        "Solutions": "Add a dark mode toggle in settings. Create alternate color palette with dark backgrounds.",
        "Risks": None,
        "GTM": None,
    }
    
    raw_input = """
Metrics: Track dark mode adoption rate with a target of 40% within 30 days. Measure user satisfaction through in-app surveys. Monitor session duration changes for dark mode users vs light mode users.
"""
    
    state = create_test_state(raw_input, existing_components)
    result = component_master_node(state)
    
    print(f"\nAdded Metrics input")
    print(f"is_spec_complete: {result.get('is_spec_complete')}")
    print(f"gaps: {result.get('gaps')}")
    print(f"\nMetrics now: {result.get('components', {}).get('Metrics')}")
    
    return result


if __name__ == "__main__":
    print("\n" + "#" * 60)
    print("# COMPONENT MASTER NODE - TEST SUITE (v2)")
    print("#" * 60)
    
    test_gap_detection()
    
    results = {
        "one_liner": test_sanity_failure(),
        "complete_prd": test_success_with_complete_prd(),
        "partial_prd": test_partial_prd(),
        "incremental": test_incremental_update(),
    }
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    for test_name, result in results.items():
        is_complete = result.get('is_spec_complete', False)
        gaps_count = len(result.get('gaps', []))
        status = "✓ Complete" if is_complete else f"✗ {gaps_count} gaps"
        print(f"{test_name}: {status}")
    
    print("\n" + "#" * 60)
    print("# TEST SUITE COMPLETE")
    print("#" * 60 + "\n")
