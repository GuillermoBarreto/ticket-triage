"""Command-line interface for the ticket-triage assistant.

Usage:
    python3 cli.py triage --title "..." --description "..." [--reporter "..."]
    python3 cli.py demo [--show-reply]
    python3 cli.py batch --file tickets.json [--output results.json]

`triage` classifies one ticket and prints its category, scores,
routing, and draft reply. `demo` runs every synthetic sample ticket
in sample_tickets.json and prints a one-line summary each.
"""

import argparse
import json
import os
import sys

from triage import batch_triage, triage

HERE = os.path.dirname(os.path.abspath(__file__))
SAMPLES_PATH = os.path.join(HERE, "sample_tickets.json")


def _print_result(title, result, show_reply=True):
    print("Title: {}".format(title))
    print("Category: {}".format(result["category"]))
    print("Routing: {}".format(result["routing"]))
    print("Confidence: {} — {}".format(
        result["confidence"], result["confidence_note"]))
    scored = {
        cat: info["score"]
        for cat, info in result["scores"].items()
        if info["score"] > 0
    }
    print("Scores: {}".format(scored if scored else "no keyword matches"))
    matched = {
        cat: info["matched"]
        for cat, info in result["scores"].items()
        if info["matched"]
    }
    if matched:
        print("Matched keywords: {}".format(matched))
    if show_reply:
        print("--- draft reply ---")
        print(result["draft_reply"])
        print("-------------------")


def cmd_triage(args):
    result = triage(args.title, args.description, reporter=args.reporter)
    _print_result(args.title, result)
    return 0


def cmd_batch(args):
    with open(args.file, "r", encoding="utf-8") as handle:
        tickets = json.load(handle)
    try:
        results = batch_triage(tickets)
    except ValueError as exc:
        print("batch error: {}".format(exc), file=sys.stderr)
        return 1
    expected = {}
    if isinstance(tickets, list):
        for ticket in tickets:
            if isinstance(ticket, dict) and "expected_category" in ticket:
                expected[ticket.get("id")] = ticket["expected_category"]
    for result in results:
        line = "{} -> {} | routing: {} | confidence: {}".format(
            result["id"] or result["title"],
            result["category"],
            result["routing"],
            result["confidence"],
        )
        if result["id"] in expected:
            want = expected[result["id"]]
            line += " (expected {} {})".format(
                want, "OK" if result["category"] == want else "MISMATCH")
        print(line)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            json.dump(results, handle, indent=2)
        print("Wrote {} results to {}".format(len(results), args.output))
    return 0


def cmd_demo(args):
    with open(SAMPLES_PATH, "r", encoding="utf-8") as handle:
        samples = json.load(handle)
    for sample in samples:
        result = triage(
            sample["title"],
            sample["description"],
            reporter=sample.get("reporter", "Reporter"),
        )
        expected = sample.get("expected_category", "?")
        mark = "OK " if result["category"] == expected else "MISMATCH"
        print(
            "[{}] {} -> {} (expected {}) | routing: {}".format(
                mark, sample["id"], result["category"], expected,
                result["routing"],
            )
        )
        if args.show_reply:
            print(result["draft_reply"])
            print()
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Rule-based ticket triage (synthetic tickets only)."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_triage = sub.add_parser("triage", help="Triage one ticket.")
    p_triage.add_argument("--title", required=True)
    p_triage.add_argument("--description", required=True)
    p_triage.add_argument("--reporter", default="Reporter")
    p_triage.set_defaults(func=cmd_triage)

    p_batch = sub.add_parser("batch", help="Triage tickets from a JSON file.")
    p_batch.add_argument("--file", required=True, help="JSON list of tickets")
    p_batch.add_argument("--output", help="Optional JSON file for results")
    p_batch.set_defaults(func=cmd_batch)

    p_demo = sub.add_parser("demo", help="Triage all sample tickets.")
    p_demo.add_argument("--show-reply", action="store_true")
    p_demo.set_defaults(func=cmd_demo)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
