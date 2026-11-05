"""Tests for the rule-based ticket triage (stdlib unittest only)."""

import json
import os
import unittest

from triage import (
    CATEGORIES,
    KEYWORDS,
    PRIORITY,
    ROUTING,
    batch_triage,
    score_ticket,
    triage,
)

HERE = os.path.dirname(os.path.abspath(__file__))


class TestCategories(unittest.TestCase):
    def test_network_keywords(self):
        result = triage("Wi-Fi down", "The internet connection is offline.")
        self.assertEqual(result["category"], "network")

    def test_hardware_keywords(self):
        result = triage("Broken monitor", "The screen flickers and the laptop fan is loud.")
        self.assertEqual(result["category"], "hardware")

    def test_access_keywords(self):
        result = triage("Can't log in", "My password reset never arrived and I'm locked out.")
        self.assertEqual(result["category"], "access")

    def test_software_keywords(self):
        result = triage("App keeps crashing", "It freezes on save and shows an error.")
        self.assertEqual(result["category"], "software")

    def test_unknown_falls_back_to_other(self):
        result = triage("Spare headset request", "Could we get one more for the training room?")
        self.assertEqual(result["category"], "other")

    def test_empty_ticket_falls_back_to_other(self):
        result = triage("", "")
        self.assertEqual(result["category"], "other")

    def test_matching_is_case_insensitive(self):
        result = triage("WIFI DOWN", "ROUTER keeps rebooting.")
        self.assertEqual(result["category"], "network")

    def test_tie_breaks_by_priority_order(self):
        # One network keyword and one hardware keyword: network wins
        # because it comes first in PRIORITY.
        result = triage("wifi printer", "wifi printer")
        self.assertEqual(result["category"], "network")

    def test_repeated_keyword_counts_once(self):
        scores = score_ticket("wifi wifi wifi", "")
        self.assertEqual(scores["network"]["score"], 1)

    def test_matched_keywords_are_reported(self):
        result = triage("VPN drops", "The vpn drops every few minutes.")
        self.assertIn("vpn", result["scores"]["network"]["matched"])
        self.assertIn("drops", result["scores"]["network"]["matched"])

    def test_every_category_has_a_route(self):
        for category in CATEGORIES:
            self.assertIn(category, ROUTING)
            self.assertTrue(ROUTING[category])

    def test_draft_reply_names_title_category_and_route(self):
        result = triage("Wi-Fi down", "The internet is offline.", reporter="Alex")
        reply = result["draft_reply"]
        self.assertIn("Wi-Fi down", reply)
        self.assertIn("network", reply)
        self.assertIn(result["routing"], reply)
        self.assertIn("Alex", reply)

    def test_sample_tickets_match_expected_categories(self):
        path = os.path.join(HERE, "sample_tickets.json")
        with open(path, "r", encoding="utf-8") as handle:
            samples = json.load(handle)
        self.assertGreaterEqual(len(samples), 6)
        for sample in samples:
            with self.subTest(sample=sample["id"]):
                result = triage(sample["title"], sample["description"])
                self.assertEqual(result["category"], sample["expected_category"])

    def test_keyword_lists_are_nonempty(self):
        for category in PRIORITY:
            self.assertTrue(KEYWORDS[category])

    def test_tie_is_low_confidence_close_call(self):
        result = triage("wifi printer", "wifi printer")
        self.assertEqual(result["confidence"], "low")
        self.assertIn("Close call", result["confidence_note"])

    def test_clear_lead_is_high_confidence(self):
        result = triage("Wi-Fi down", "The internet connection is offline.")
        self.assertEqual(result["confidence"], "high")

    def test_no_matches_is_low_confidence(self):
        result = triage("Spare headset request", "Could we get one more?")
        self.assertEqual(result["confidence"], "low")

    def test_batch_triage_preserves_ids_and_categories(self):
        results = batch_triage([
            {"id": "b1", "title": "Wi-Fi down",
             "description": "The internet is offline."},
            {"id": "b2", "title": "Spare headset request",
             "description": "Could we get one more?"},
        ])
        self.assertEqual([r["id"] for r in results], ["b1", "b2"])
        self.assertEqual(results[0]["category"], "network")
        self.assertEqual(results[1]["category"], "other")

    def test_batch_triage_rejects_missing_description(self):
        with self.assertRaises(ValueError):
            batch_triage([{"id": "b1", "title": "Wi-Fi down"}])


if __name__ == "__main__":
    unittest.main()
