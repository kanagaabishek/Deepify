from langgraph.graph import START, END, StateGraph

from deep.researcher.state import State
import deep.researcher.llm_interface as llm
import deep.researcher.prompts as prompts

MAX_ITERATIONS = 3


def researcher_node(state: State) -> dict:
    iteration = state.get("iteration_count", 0)
    print(f"🔍 [Researcher] pass {iteration + 1}/{MAX_ITERATIONS}")

    critique = state.get("critique")
    follow_ups = (
        f"\n\nFocus on these unanswered questions from the previous pass:\n"
        + "\n".join(f"- {q}" for q in critique.follow_up_questions)
        if critique and critique.follow_up_questions else ""
    )

    result = llm.llm_researcher.invoke([
        {"role": "system", "content": prompts.RESEARCHER_PROMPT},
        {"role": "user",   "content": f"Topic: {state['topic']}{follow_ups}"},
    ])
    return {
        "research":        result,
        "iteration_count": iteration + 1,
        "critique":        None,
    }


def analyst_node(state: State) -> dict:
    print("🧠 [Analyst] synthesizing findings...")
    r = state["research"]

    result = llm.llm_analyst.invoke([
        {"role": "system", "content": prompts.ANALYST_PROMPT},
        {"role": "user",   "content": (
            f"Topic: {state['topic']}\n\n"
            f"Sub-questions investigated:\n" + "\n".join(f"- {q}" for q in r.sub_questions) + "\n\n"
            f"Findings:\n" + "\n".join(f"- {f}" for f in r.findings) + "\n\n"
        )},
    ])
    return {"analysis": result}


def critic_node(state: State) -> dict:
    print("🔎 [Critic] stress-testing analysis...")
    r  = state["research"]
    an = state["analysis"]

    result = llm.llm_critic.invoke([
        {"role": "system", "content": prompts.CRITIC_PROMPT},
        {"role": "user",   "content": (
            f"Topic: {state['topic']}\n\n"
            f"Research findings:\n" + "\n".join(f"- {f}" for f in r.findings) + "\n\n"
            f"Analysis summary:\n{an.summary}\n\n"
            f"Conclusions:\n" + "\n".join(f"- {c}" for c in an.conclusions) + "\n\n"
            f"Limitations already noted:\n" + "\n".join(f"- {l}" for l in an.limitations)
        )},
    ])
    print(f"   gaps={len(result.gaps)} | needs_deeper={result.needs_deeper_research}")
    return {"critique": result}


def factchecker_node(state: State) -> dict:
    print("🛡️  [FactChecker] verifying claims...")
    r  = state["research"]
    an = state["analysis"]

    result = llm.llm_factchecker.invoke([
        {"role": "system", "content": prompts.FACT_CHECKER_PROMPT},
        {"role": "user",   "content": (
            f"Original research data:\n"
            f"Findings: {r.findings}\n"
            f"Data points: {r.data_points}\n\n"
            f"Analysis to verify:\n"
            f"Insights: {an.key_insights}\n"
            f"Conclusions: {an.conclusions}\n"
            f"Summary: {an.summary}"
        )},
    ])
    print(f"   verified={result.is_verified} | confidence={result.confidence_score}/10")

    report = _build_report(state, result)
    return {"fact_check": result, "report": report}


def _build_report(state: State, fc) -> str:
    r  = state["research"]
    an = state["analysis"]

    lines = [
        f"# Deep Research Report",
        f"**Topic:** {state['topic']}",
        f"**Iterations:** {state.get('iteration_count', 1)}  |  "
        f"**Fact-check confidence:** {fc.confidence_score}/10  |  "
        f"**Status:** {'✅ Verified' if fc.is_verified else '⚠️ Unverified'}",
        "",
        "## Summary",
        an.summary,
        "",
        "## Key Insights",
        *[f"- {i}" for i in an.key_insights],
        "",
        "## Patterns & Trends",
        *[f"- {p}" for p in an.patterns],
        "",
        "## Conclusions",
        *[f"- {c}" for c in an.conclusions],
        "",
        "## Limitations",
        *[f"- {l}" for l in an.limitations],
        "",
        "## Raw Findings",
        *[f"- {f}" for f in r.findings],
        "",
        "## Data Points",
        *[f"- {d}" for d in r.data_points],
        "",
        "## Sources",
        *[f"- {s}" for s in r.sources],
    ]

    if not fc.is_verified:
        lines += [
            "",
            "## ⚠️ Fact-Check Flags",
            *[f"- {u}" for u in fc.unverified_claims],
            "",
            "## Corrections",
            *[f"- {c}" for c in fc.corrections],
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
