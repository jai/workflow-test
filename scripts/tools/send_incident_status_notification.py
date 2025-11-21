#!/usr/bin/env python3
import html
import json
import os
from pathlib import Path

import requests

webhook = os.environ.get("WEBHOOK_URL")
if not webhook:
    print("Google Chat webhook not configured; skipping notification.")
    raise SystemExit(0)

window_hours = os.environ["WINDOW_HOURS"]
data = json.loads(Path(os.environ["INCIDENT_DATA_PATH"]).read_text())
decisions = json.loads(Path(os.environ["DECISIONS_PATH"]).read_text())
incident_map = {item["incident_id"]: item for item in data.get("incidents", [])}

def fmt_text(value: str) -> str:
    if not value:
        return "_No status text provided_"
    collapsed = " ".join(value.split())
    return html.escape(collapsed)

pass_count = sum(1 for d in decisions if d.get("overallStatus") == "pass")
failures = []
for decision in decisions:
    inc = incident_map.get(decision["incident_id"])
    if not inc:
        continue
    if decision.get("overallStatus") == "fail":
        failures.append((inc, decision))

def build_failure_section(inc, decision):
    status = inc.get("status_update") or {}
    summary_flag = "✅" if decision.get("summaryAdequate") else "❌"
    next_flag = "✅" if decision.get("nextStepsAdequate") else "❌"
    author = status.get("author_display") or "Responder"
    ts = status.get("timestamp") or "unknown time"
    url = inc.get("overview_url")
    title = html.escape(inc.get('title', inc['incident_id']))
    severity = html.escape(inc.get('severity', 'unknown'))

    header_lines = [
        f"<b>{title}</b> (Severity: {severity})",
        f"{summary_flag} summary | {next_flag} next steps",
        f"{html.escape(author)} — {html.escape(ts)}",
        "",
    ]

    preview_source = status.get('text') or ''
    collapsed_preview = " ".join(preview_source.split())
    preview = collapsed_preview[:200] + ("…" if len(collapsed_preview) > 200 else "")
    preview_html = fmt_text(preview) if preview else "_No preview available_"
    if url:
        preview_html = f"{preview_html} <a href=\"{url}\">↗</a>"

    notes = decision.get("notes") or []
    reason_text = f"<b>Analysis:</b> {html.escape(' '.join(notes))}" if notes else ""

    text = "<br>".join(part for part in [*header_lines, f"<i>{preview_html}</i>", reason_text, ""] if part)
    return {"widgets": [{"textParagraph": {"text": text}}]}

summary_lines = [
    f"Incidents evaluated: {len(decisions)}",
    f"Passing updates: {pass_count}",
    f"Action needed: {len(failures)}",
]
main_sections = [{"widgets": [{"textParagraph": {"text": "<br>".join(summary_lines)}}]}]
if failures:
    for inc, decision in failures:
        main_sections.append(build_failure_section(inc, decision))
else:
    main_sections.append({"widgets": [{"textParagraph": {"text": "✅ All incidents with status updates meet the requirements."}}]})

payload = {
    "cards": [
        {
            "header": {
                "title": f"Incident status quality check — last {window_hours}h",
                "subtitle": "Claude incident status audit",
            },
            "sections": main_sections,
        }
    ]
}

resp = requests.post(webhook, json=payload, timeout=20)
if resp.status_code >= 300:
    raise SystemExit(f"Chat webhook failed: {resp.status_code} {resp.text}")
print("Posted results to Google Chat.")
