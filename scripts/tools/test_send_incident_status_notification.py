import unittest

from scripts.tools import send_incident_status_notification as notif


class TestNotificationHelpers(unittest.TestCase):
    def test_is_failure_enforces_flags(self):
        decision = {"overallStatus": "pass", "summaryAdequate": False, "nextStepsAdequate": True}
        self.assertTrue(notif.is_failure(decision))

        decision_ok = {"overallStatus": "pass", "summaryAdequate": True, "nextStepsAdequate": True}
        self.assertFalse(notif.is_failure(decision_ok))

        decision_fail = {"overallStatus": "fail", "summaryAdequate": True, "nextStepsAdequate": True}
        self.assertTrue(notif.is_failure(decision_fail))

    def test_build_preview_includes_full_text(self):
        status = {"text": "Line one\nLine two with details"}
        preview = notif.build_preview(status)
        self.assertEqual(preview, "Line one Line two with details")

        empty_preview = notif.build_preview({})
        self.assertEqual(empty_preview, "")

    def test_format_analysis_block_renders_lines(self):
        decision = {"notes": ["Summary detail", "Next step detail", "Extra context"]}
        block = notif.format_analysis_block(decision, "✅", "❌")
        self.assertIn("AI Analysis", block)
        self.assertIn("Summary detail", block)
        self.assertIn("Next step detail", block)
        self.assertIn("Extra context", block)
        self.assertIn("✅", block)
        self.assertIn("❌", block)


if __name__ == "__main__":
    unittest.main()
