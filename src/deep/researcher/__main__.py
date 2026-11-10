import argparse
from deep.researcher.graph import graph


def main():
    parser = argparse.ArgumentParser(description="Deep Research AI Agent")
    parser.add_argument("topic", type=str, help="Topic to research")
    args = parser.parse_args()

    print(f"\n🚀 Deep Research Agent starting...\n   Topic: \"{args.topic}\"\n")

    final_state = {}
    for step in graph.stream({"topic": args.topic, "iteration_count": 0}, stream_mode="updates"):
        for node_name, update in step.items():
            print(f"   ✅ [{node_name}] done")
            final_state.update(update)

    report = final_state.get("report", "No report generated.")
    print("\n" + "=" * 70)
    print(report)
    print("=" * 70)


if __name__ == "__main__":
    main()
