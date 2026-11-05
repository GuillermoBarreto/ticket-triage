# Ticket-Triage Assistant (scaffold)

A small command-line tool that takes an IT support ticket, sorts it
into a category with transparent rules, suggests which team should
handle it, and drafts a reply for the reporter.

Built as Guillermo Barreto's entry scaffold for the Meta Global AI
Developer Hackathon (Indie track, "Build for Your World" theme).
Submission deadline: Wednesday, November 4, 2026, 8:00 PM Chicago time.

## How it works

No model, no network calls, no paid API. Triage is a keyword score
over the ticket's title and description:

- **Categories:** network, hardware, access, software, other.
- Each category has a curated keyword list (`KEYWORDS` in `triage.py`).
- A keyword counts once per ticket, no matter how often it appears.
- The highest score wins; ties break by a fixed priority order
  (network, hardware, access, software), so results are deterministic.
- If nothing matches, the ticket goes to `other`.
- Every result reports its scores and matched keywords, so a human can
  audit why a ticket landed where it did.

Routing is a fixed map from category to team queue, and the draft
reply is assembled from templates. Nothing is sent anywhere — the
draft is for a human agent to review before sending.

## Synthetic tickets only

Every ticket in `sample_tickets.json` is invented: fake titles,
descriptions, reporter names, and systems, written for demo and
testing. Never use real work tickets, real customer data, or anything
resembling an actual job ticket with this tool.

## Run it

Requires Python 3 (standard library only, no dependencies to install).

Triage one ticket:

```sh
python3 cli.py triage --title "Wi-Fi down" --description "The internet is offline." --reporter "Alex"
```

Run all sample tickets:

```sh
python3 cli.py demo
python3 cli.py demo --show-reply
```

Triage a batch from a JSON file (a list of tickets with `title`,
`description`, and optional `id`/`reporter`/`expected_category`):

```sh
python3 cli.py batch --file sample_tickets.json
python3 cli.py batch --file tickets.json --output results.json
```

Confidence: each result carries a `confidence` label — `high` for a
clear lead, `medium` for a narrow lead, `low` for a tie (close call)
or no matches — so a human knows when to double-check before routing.

## Run the tests

```sh
python3 -m unittest test_triage -v
```

## Files

- `triage.py` — scoring, routing, and draft-reply logic.
- `cli.py` — command-line interface (`triage` and `demo` commands).
- `sample_tickets.json` — 6 invented sample tickets with expected categories.
- `test_triage.py` — unit tests for categories, ties, routing, replies, and samples.

## Next steps

- A small demo script that walks through one ticket end to end.
- Submission packaging: demo video and write-up, closer to November 4.
- Weekend build (Oct 31–Nov 1): polish, then demo video and submission
  draft Mon–Tue, submit Wed Nov 4 by 8:00 PM Chicago.
