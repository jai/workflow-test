#!/usr/bin/env python3
import argparse
import html
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import requests


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Send incident status quality Chat card")
    parser.add_argument(
        "--include-passing",
        dest="include_passing",
        action="store_true",
        help="Include passing incidents in the Chat card",
    )
    parser.add_argument(
        "--exclude-passing",
        dest="include_passing",
        action="store_false",
        help="Exclude passing incidents from the Chat card",
    )
    parser.set_defaults(include_passing=None)
    return parser.parse_args()


def env_flag(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    normalized = value.strip().lower()
    return normalized in {"1", "true", "yes", "on", "y"}


SEVERITY_ICONS = {"Critical": "🔴", "Major": "🟠", "Minor": "🟡"}

def fmt_text(value: str) -> str:
    if not value:
        return "No status text provided"
    collapsed = " ".join(value.split())
    return html.escape(collapsed)


def is_failure(decision: dict) -> bool:
    if decision.get("overallStatus") == "fail":
        return True
    if decision.get("summaryAdequate") is False:
        return True
    if decision.get("nextStepsAdequate") is False:
        return True
    return False


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

def split_decisions(decisions, incident_map, include_passing):
    failures = []
    passes = []
    for decision in decisions:
        inc = incident_map.get(decision.get("incident_id"))
        if not inc:
            continue
        if is_failure(decision):
            failures.append((inc, decision))
        elif include_passing:
            passes.append((inc, decision))

    fail_count = sum(1 for d in decisions if is_failure(d))
    pass_count = len(decisions) - fail_count
    return pass_count, failures, passes

def build_preview(status):
    preview_source = status.get("text") or ""
    collapsed_preview = " ".join(preview_source.split())
    return collapsed_preview

def format_analysis_block(decision, summary_flag, next_flag):
    notes = decision.get("notes") or []
    summary_text = html.escape(notes[0]) if notes else "No summary commentary provided."
    next_text = html.escape(notes[1]) if len(notes) > 1 else "No next-steps commentary provided."
    extra = [html.escape(note) for note in notes[2:]]

    lines = [
        "🤖 <b>AI Analysis:</b>",
        f"{summary_flag} <b>Summary and impact:</b> {summary_text}",
        f"{next_flag} <b>Next steps:</b> {next_text}",
    ]
    lines.extend(extra)
    return "<br>".join(lines)

def build_failure_section(inc, decision, idx):
    status = inc.get("status_update") or {}
    summary_flag = "✅" if decision.get("summaryAdequate") else "❌"
    next_flag = "✅" if decision.get("nextStepsAdequate") else "❌"
    author = status.get("author_display") or "Responder"
    ts = status.get("timestamp") or ""
    url = inc.get("overview_url")
    title = html.escape(inc.get("title", inc["incident_id"]))
    severity = html.escape(inc.get("severity", "unknown"))
    sev_icon = SEVERITY_ICONS.get(inc.get("severity"), "⚪️")

    header_line = f"{sev_icon} <b>{title}</b>"
    rel_time = relative_time(ts)

    preview = build_preview(status)
    preview_html = fmt_text(preview) if preview else "_No preview available_"
    status_line = f"🧭 <b>Status:</b> <i>{preview_html}</i>"
    if status.get("missing"):
        status_line += " — <i>no recent human update</i>"
    if url:
        status_line += f" <a href=\"{url}\">↗</a>"

    actor_line = f"👤 {html.escape(author)} • {rel_time}"
    analysis_block = format_analysis_block(decision, summary_flag, next_flag)

    text = "<br>".join([header_line, "", status_line, actor_line, "", analysis_block])
    return {"widgets": [{"textParagraph": {"text": text}}]}


def build_pass_sections(pass_items):
    sections = []
    for inc, decision in pass_items:
        status = inc.get("status_update") or {}
        author = status.get("author_display") or "Responder"
        ts = status.get("timestamp") or inc.get("modified_time") or ""
        url = inc.get("overview_url")
        title = html.escape(inc.get("title", inc["incident_id"]))
        sev_icon = SEVERITY_ICONS.get(inc.get("severity"), "⚪️")
        rel_time = relative_time(ts)

        preview = build_preview(status)
        preview_html = fmt_text(preview) if preview else "_No preview available_"
        status_line = f"🧭 <b>Status:</b> <i>{preview_html}</i>"
        if url:
            status_line += f" <a href=\"{url}\">↗</a>"
        actor_line = f"👤 {html.escape(author)} • {rel_time}"

        summary_flag = "✅" if decision.get("summaryAdequate") else "❌"
        next_flag = "✅" if decision.get("nextStepsAdequate") else "❌"
        analysis_block = format_analysis_block(decision, summary_flag, next_flag)

        text = "<br>".join([f"{sev_icon} <b>{title}</b>", "", status_line, actor_line, "", analysis_block])
        sections.append({"widgets": [{"textParagraph": {"text": text}}]})

    return sections

def build_payload(decisions, incident_map, include_passing):
    pass_count, failures, passes = split_decisions(decisions, incident_map, include_passing)

    summary_lines = [
        f"📊 <b>Incidents evaluated:</b> {len(decisions)}",
        f"✅ <b>Passing:</b> {pass_count}",
        f"⚠️ <b>Needs attention:</b> {len(failures)}",
    ]
    main_sections = [{"widgets": [{"textParagraph": {"text": "<br>".join(summary_lines)}}]}]
    main_sections.append({"widgets": [{"textParagraph": {"text": " "}}]})
    if failures:
        for idx, (inc, decision) in enumerate(failures, start=1):
            main_sections.append(build_failure_section(inc, decision, idx))
    else:
        main_sections.append({"widgets": [{"textParagraph": {"text": "✅ All incidents with status updates meet the requirements."}}]})

    if include_passing:
        pass_sections = build_pass_sections(passes)
        if pass_sections:
            pass_sections[0]["header"] = "Passing incidents"
            main_sections.extend(pass_sections)
        else:
            main_sections.append({"widgets": [{"textParagraph": {"text": "ℹ️ Passing incidents requested, but none to display."}}]})

    payload = {
        "cards": [
            {
                "header": {
                    "title": "Incident status quality check",
                    "subtitle": "Claude incident status audit",
                },
                "sections": main_sections,
            }
        ]
    }
    return payload


def main():
    args = parse_args()
    webhook = os.environ.get("WEBHOOK_URL")
    if not webhook:
        print("Google Chat webhook not configured; skipping notification.")
        raise SystemExit(0)

    include_passing = args.include_passing
    if include_passing is None:
        include_passing = env_flag("INCLUDE_PASSING", default=True)

    data = json.loads(Path(os.environ["INCIDENT_DATA_PATH"]).read_text())
    decisions = json.loads(Path(os.environ["DECISIONS_PATH"]).read_text())
    incident_map = {item["incident_id"]: item for item in data.get("incidents", [])}

    payload = build_payload(decisions, incident_map, include_passing)
    resp = requests.post(webhook, json=payload, timeout=20)
    if resp.status_code >= 300:
        raise SystemExit(f"Chat webhook failed: {resp.status_code} {resp.text}")
    print("Posted results to Google Chat.")


if __name__ == "__main__":
    main()
