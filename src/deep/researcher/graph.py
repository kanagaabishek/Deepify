from langgraph.graph import START, END, StateGraph

from deep.researcher.state import State
import deep.researcher.llm_interface as llm
import deep.researcher.prompts as prompts
from deep.researcher.tools import search_web, format_search_results

MAX_ITERATIONS = 3


def researcher_node(state: State) -> dict:
    iteration = state.get("iteration_count", 0)
    topic = state["topic"]
    print(f"🔍 [Researcher] pass {iteration + 1}/{MAX_ITERATIONS}")

    critique = state.get("critique")
    
    # Formulate search queries
    if critique and critique.follow_up_questions:
        query = f"{topic} " + " ".join(critique.follow_up_questions[:2])
    else:
        query = f"{topic} research overview latest facts"

    print(f"   🌐 DuckDuckGo Search: '{query[:60]}...'")
    search_data = search_web(query, max_results=5)
    formatted_web_context = format_search_results(search_data)

    follow_ups = (
        f"\n\nAddress these specific questions identified by peer critique:\n"
        + "\n".join(f"- {q}" for q in critique.follow_up_questions)
        if critique and critique.follow_up_questions else ""
    )

    result = llm.llm_researcher.invoke([
        {"role": "system", "content": prompts.RESEARCHER_PROMPT},
        {"role": "user",   "content": (
            f"Topic: {topic}\n"
            f"{follow_ups}\n\n"
            f"=== DuckDuckGo Web Search Context ===\n"
            f"{formatted_web_context}\n"
            f"====================================="
        )},
    ])
    return {
        "research":        result,
        "iteration_count": iteration + 1,
        "critique":        None,
    }


def analyst_node(state: State) -> dict:
    print("🧠 [Analyst] synthesizing findings...")
    r = state["research"]

    sub_q = r.sub_questions if r and r.sub_questions else []
    findings = r.findings if r and r.findings else []

    result = llm.llm_analyst.invoke([
        {"role": "system", "content": prompts.ANALYST_PROMPT},
        {"role": "user",   "content": (
            f"Topic: {state['topic']}\n\n"
            f"Sub-questions investigated:\n" + "\n".join(f"- {q}" for q in sub_q) + "\n\n"
            f"Findings:\n" + "\n".join(f"- {f}" for f in findings) + "\n\n"
        )},
    ])
    return {"analysis": result}


def critic_node(state: State) -> dict:
    print("🔎 [Critic] stress-testing analysis...")
    r  = state.get("research")
    an = state["analysis"]

    findings = r.findings if r and r.findings else []
    conclusions = an.conclusions if an and an.conclusions else []
    limitations = an.limitations if an and an.limitations else []

    result = llm.llm_critic.invoke([
        {"role": "system", "content": prompts.CRITIC_PROMPT},
        {"role": "user",   "content": (
            f"Topic: {state['topic']}\n\n"
            f"Research findings:\n" + "\n".join(f"- {f}" for f in findings) + "\n\n"
            f"Analysis summary:\n{an.summary}\n\n"
            f"Conclusions:\n" + "\n".join(f"- {c}" for c in conclusions) + "\n\n"
            f"Limitations already noted:\n" + "\n".join(f"- {l}" for l in limitations)
        )},
    ])
    gaps_count = len(result.gaps) if result and result.gaps else 0
    needs_deeper = result.needs_deeper_research if result else False
    print(f"   gaps={gaps_count} | needs_deeper={needs_deeper}")
    return {"critique": result}


def factchecker_node(state: State) -> dict:
    print("🛡️  [FactChecker] verifying claims with DuckDuckGo...")
    r  = state.get("research")
    an = state["analysis"]

    topic = state["topic"]
    # Run a targeted verification search for the core claims
    verify_query = f"{topic} fact check statistics verification"
    print(f"   🌐 Verification Search: '{verify_query[:60]}...'")
    verification_results = search_web(verify_query, max_results=4)
    formatted_verify_context = format_search_results(verification_results)

    findings = r.findings if r and r.findings else []
    data_points = r.data_points if r and r.data_points else []
    insights = an.key_insights if an and an.key_insights else []
    conclusions = an.conclusions if an and an.conclusions else []

    result = llm.llm_factchecker.invoke([
        {"role": "system", "content": prompts.FACT_CHECKER_PROMPT},
        {"role": "user",   "content": (
            f"Original research findings:\n{findings}\n\n"
            f"Data points:\n{data_points}\n\n"
            f"Analysis to verify:\n"
            f"Insights: {insights}\n"
            f"Conclusions: {conclusions}\n"
            f"Summary: {an.summary}\n\n"
            f"=== Real-Time Web Verification Context ===\n"
            f"{formatted_verify_context}\n"
            f"=========================================="
        )},
    ])
    print(f"   verified={result.is_verified} | confidence={result.confidence_score}/10")

    report = _build_report(state, result)
    return {"fact_check": result, "report": report}


def _build_report(state: State, fc) -> str:
    r  = state.get("research")
    an = state["analysis"]

    key_insights = an.key_insights if an and an.key_insights else []
    patterns = an.patterns if an and an.patterns else []
    conclusions = an.conclusions if an and an.conclusions else []
    limitations = an.limitations if an and an.limitations else []
    findings = r.findings if r and r.findings else []
    data_points = r.data_points if r and r.data_points else []
    sources = r.sources if r and r.sources else []

    lines = [
        f"# Deep Research Report",
        f"**Topic:** {state['topic']}",
        f"**Iterations:** {state.get('iteration_count', 1)}  |  "
        f"**Fact-check confidence:** {fc.confidence_score}/10  |  "
        f"**Status:** {'✅ Verified' if fc.is_verified else '⚠️ Unverified'}",
        "",
        "## Summary",
        an.summary if an else "",
        "",
        "## Key Insights",
        *[f"- {i}" for i in key_insights],
        "",
        "## Patterns & Trends",
        *[f"- {p}" for p in patterns],
        "",
        "## Conclusions",
        *[f"- {c}" for c in conclusions],
        "",
        "## Limitations",
        *[f"- {l}" for l in limitations],
        "",
        "## Raw Findings (Grounded in Web Search)",
        *[f"- {f}" for f in findings],
        "",
        "## Extracted Data Points",
        *[f"- {d}" for d in data_points],
        "",
        "## Sources & References",
        *[f"- {s}" for s in sources],
    ]

    if not fc.is_verified:
        unverified = fc.unverified_claims if fc and fc.unverified_claims else []
        corrections = fc.corrections if fc and fc.corrections else []
        lines += [
            "",
            "## ⚠️ Fact-Check Flags",
            *[f"- {u}" for u in unverified],
            "",
            "## Corrections",
            *[f"- {c}" for c in corrections],
        ]

    return "\n".join(lines)


def route_critic(state: State) -> str:
    critique   = state.get("critique")
    iterations = state.get("iteration_count", 0)

    if critique and critique.needs_deeper_research and iterations < MAX_ITERATIONS:
        print(f"🔄 [route] gaps found → Researcher (iter {iterations}/{MAX_ITERATIONS})")
        return "Researcher"

    return "FactChecker"


def route_factchecker(state: State) -> str:
    fc         = state.get("fact_check")
    iterations = state.get("iteration_count", 0)

    if fc and fc.is_verified:
        print("✅ [route] fully verified → END")
        return END

    if iterations >= MAX_ITERATIONS:
        print(f"⚠️  [route] max iterations reached → END")
        return END

    print(f"🔄 [route] unverified claims → Researcher (iter {iterations}/{MAX_ITERATIONS})")
    return "Researcher"


builder = StateGraph(State)
builder.add_node("Researcher",  researcher_node)
builder.add_node("Analyst",     analyst_node)
builder.add_node("Critic",      critic_node)
builder.add_node("FactChecker", factchecker_node)

builder.add_edge(START,        "Researcher")
builder.add_edge("Researcher", "Analyst")
builder.add_edge("Analyst",    "Critic")
builder.add_conditional_edges("Critic",      route_critic,       {"Researcher": "Researcher", "FactChecker": "FactChecker"})
builder.add_conditional_edges("FactChecker", route_factchecker,  {"Researcher": "Researcher", END: END})

graph = builder.compile()
