#!/usr/bin/env python3
import html
import json
import os
from datetime import datetime, timezone
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


def relative_time(iso_ts: str) -> str:
    if not iso_ts:
        return "unknown time"
    safe_ts = iso_ts.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(safe_ts)
    except ValueError:
        return html.escape(iso_ts)
    now = datetime.now(timezone.utc)
    delta = now - dt
    seconds = int(delta.total_seconds())
    if seconds < 60:
        return "just now"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes}m ago"
    hours = minutes // 60
    if hours < 24:
        return f"{hours}h ago"
    days = hours // 24
    if days < 7:
        return f"{days}d ago"
    weeks = days // 7
    return f"{weeks}w ago"

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
    ts = status.get("timestamp") or ""
    url = inc.get("overview_url")
    title = html.escape(inc.get('title', inc['incident_id']))
    severity = html.escape(inc.get('severity', 'unknown'))

    header_line = f"<b>{title}</b> (Severity: {severity})"
    rel_time = relative_time(ts)

    preview_source = status.get('text') or ''
    collapsed_preview = " ".join(preview_source.split())
    preview = collapsed_preview[:200] + ("…" if len(collapsed_preview) > 200 else "")
    preview_html = fmt_text(preview) if preview else "_No preview available_"
    if url:
        preview_html = f"{preview_html} <a href=\"{url}\">↗</a>"

    notes = decision.get("notes") or []
    reason = html.escape(" ".join(notes)) if notes else ""

    lines = [
        header_line,
        "",
        f"<i>{preview_html}</i>",
        f"{html.escape(author)} — {rel_time}",
        "",
        "<b>Analysis:</b>",
        f"Status update contains: {summary_flag} summary | {next_flag} next steps",
        reason,
        "",
    ]
    text = "<br>".join(part for part in lines if part)
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
