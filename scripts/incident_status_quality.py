#!/usr/bin/env python3
"""
Incident status quality data collector.

Fetches recently updated Grafana IRM incidents, captures the most recent
human-authored status updates, and prepares structured JSON payloads for
Claude-based quality evaluation workflows.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import re

from incident_reporter import (
    DiskCache,
    GrafanaIRMClient,
    IncidentEnricher,
    RateLimitHandler,
    is_human_user,
    parse_timestamp,
)

TEXTUAL_ACTIVITY_KINDS = {
    "keyupdateadded",
    "incidentupdatecreated",
    "statusupdateadded",
    "messageadded",
    "timelinecommentadded",
}

DEFAULT_OUTPUT_JSON = "incident-status-data.json"
DEFAULT_PROMPT_JSON = "incident-status-prompt.json"
MAX_STATUS_CHARS = 1800


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Collect recent incidents and latest status updates for Claude evaluation."
    )
    parser.add_argument("--token", help="Grafana token (or set GRAFANA_TOKEN / GRAFANA_SERVICE_ACCOUNT_TOKEN)")
    parser.add_argument("--url", help="Grafana base URL (or set GRAFANA_URL)")
    parser.add_argument(
        "--window-hours",
        type=int,
        default=24,
        help="Look-back window in hours for modified incidents (default: 24)",
    )
    parser.add_argument(
        "--max-incidents",
        type=int,
        default=0,
        help="Optional limit on number of incidents to process (default: 0 = unlimited)",
    )
    parser.add_argument(
        "--output-json",
        default=DEFAULT_OUTPUT_JSON,
        help=f"Path to write raw incident data (default: {DEFAULT_OUTPUT_JSON})",
    )
    parser.add_argument(
        "--prompt-output",
        default=DEFAULT_PROMPT_JSON,
        help=f"Path to write minimized prompt payload (default: {DEFAULT_PROMPT_JSON})",
    )
    parser.add_argument(
        "--cache-dir",
        default=".cache/incidents",
        help="Disk cache directory (default: .cache/incidents)",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Disable disk cache usage",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Verbose logging",
    )
    return parser.parse_args()


def get_env(var_name: str, fallback: Optional[str] = None) -> Optional[str]:
    value = os.environ.get(var_name)
    if value:
        return value
    return fallback


def require_credentials(token: Optional[str], url: Optional[str]) -> Tuple[str, str]:
    if not token:
        print("❌ Missing Grafana token. Provide --token or set GRAFANA_TOKEN/GRAFANA_SERVICE_ACCOUNT_TOKEN.")
        sys.exit(1)
    if not url:
        print("❌ Missing Grafana URL. Provide --url or set GRAFANA_URL.")
        sys.exit(1)
    return token, url.rstrip("/")


def grafana_incident_url(base_url: str, incident: Dict[str, Any]) -> str:
    slug = incident.get("overviewURL")
    if slug:
        if slug.startswith("http"):
            return slug
        return f"{base_url}{slug}"
    incident_id = incident.get("incidentID") or incident.get("id")
    return f"{base_url}/a/grafana-irm-app/incidents/{incident_id}"


def truncate_text(text: str, limit: int = MAX_STATUS_CHARS) -> Tuple[str, bool]:
    if len(text) <= limit:
        return text, False
    truncated = text[:limit].rstrip()
    suffix = f"... (truncated, original length {len(text)} chars)"
    return f"{truncated} {suffix}", True


def is_textual_update(kind: Optional[str], text: str) -> bool:
    kind_normalized = (kind or "").lower()
    if kind_normalized not in TEXTUAL_ACTIVITY_KINDS:
        return False
    return bool(text.strip())


ANSI_ESCAPE = re.compile(r"\x1B\[[0-9;]*[A-Za-z]")


def clean_status_text(text: str) -> str:
    if not text:
        return ""

    without_ansi = ANSI_ESCAPE.sub("", text)
    cleaned = without_ansi.strip()
    lower_clean = cleaned.lower()
    if lower_clean.startswith("status update added by"):
        marker_idx = cleaned.find("\n")
        if marker_idx != -1:
            cleaned = cleaned[marker_idx + 1 :]
        else:
            cleaned = ""

    if "<<<" in cleaned or ">>>" in cleaned:
        cleaned = cleaned.split(">>>", 1)[-1]

    cleaned = cleaned.strip().strip("*_")
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned


def load_activity_items(
    client: GrafanaIRMClient,
    disk_cache: DiskCache,
    incident_id: str,
    modified_time: Optional[str],
    debug: bool = False,
) -> List[Dict[str, Any]]:
    cached_items: Optional[List[Dict[str, Any]]] = None
    if disk_cache.enabled and modified_time:
        cached_activity = disk_cache.get_activity(incident_id, modified_time)
        if cached_activity:
            cached_items = cached_activity.get("activityItems") or cached_activity.get("items")
            if cached_items and debug:
                print(f"💾 Activity cache hit for incident {incident_id}")

    if cached_items is None:
        if debug:
            print(f"🌐 Fetching activity for incident {incident_id}")
        cached_items = client.query_activity_all_pages(
            incident_id,
            kinds=None,
            limit_per_page=100,
            order_direction="DESC",
        )
        if disk_cache.enabled and modified_time:
            disk_cache.save_activity(
                incident_id,
                {"activityItems": cached_items},
                modified_time,
            )
    return cached_items or []


def extract_latest_human_update(
    items: List[Dict[str, Any]]
) -> Optional[Dict[str, Any]]:
    for item in items:
        user = item.get("user") or item.get("createdBy") or {}
        if not is_human_user(user):
            continue

        raw_time = item.get("eventTime") or item.get("createdTime") or item.get("timestamp")
        if not raw_time:
            continue

        parsed_time = parse_timestamp(raw_time)
        if not parsed_time:
            continue

        kind = item.get("activityKind") or item.get("eventType")
        content = (item.get("body") or item.get("text") or "").strip()
        if not is_textual_update(kind, content):
            continue
        return {
            "timestamp_raw": raw_time,
            "timestamp": parsed_time,
            "text": content,
            "activity_kind": kind,
            "author": {
                "name": user.get("name"),
                "email": user.get("email"),
                "username": user.get("login") or user.get("username"),
            },
            "raw_item": item,
        }
    return None


def format_author(author: Dict[str, Any]) -> str:
    name = author.get("name")
    username = author.get("username")
    email = author.get("email")
    if name:
        first = name.strip().split()[0]
        return first
    return username or email or "Responder"


def incident_metadata(
    incident: Dict[str, Any],
    base_url: str,
    membership: Dict[str, Any],
) -> Dict[str, Any]:
    incident_id = str(incident.get("incidentID") or incident.get("id"))
    severity = incident.get("severityLabel") or incident.get("severity") or "Unknown"
    status = incident.get("status") or incident.get("state") or "unknown"
    created_at = incident.get("createdAt") or incident.get("createdTime")
    modified_time = incident.get("modifiedTime") or incident.get("updatedAt")

    teams = []
    for team in membership.get("teams") or []:
        team_obj = team.get("team") or team
        if not isinstance(team_obj, dict):
            continue
        team_name = team_obj.get("name")
        if team_name:
            teams.append(team_name)

    return {
        "incident_id": incident_id,
        "title": incident.get("title") or incident.get("name") or "(untitled incident)",
        "severity": severity,
        "status": status,
        "created_at": created_at,
        "modified_time": modified_time,
        "overview_url": grafana_incident_url(base_url, incident),
        "has_assignee": membership.get("has_assignee", False),
        "assignee": membership.get("assignee"),
        "teams": teams,
    }


def build_records(
    incidents: List[Dict[str, Any]],
    client: GrafanaIRMClient,
    disk_cache: DiskCache,
    base_url: str,
    window_start: datetime,
    window_hours: int,
    debug: bool = False,
) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    sla_by_severity = {"Critical": 1, "Major": 2, "Minor": 3}
    enricher = IncidentEnricher(
        client=client,
        disk_cache=disk_cache,
        parse_timestamp_func=parse_timestamp,
        sla_by_severity=sla_by_severity,
    )

    now = datetime.now(timezone.utc)

    for incident in incidents:
        flat = enricher.flatten_incident(incident)
        metadata = incident_metadata(flat, base_url, enricher.get_incident_membership(flat))
        incident_id = metadata["incident_id"]
        modified_time = metadata["modified_time"]

        items = load_activity_items(client, disk_cache, incident_id, modified_time, debug=debug)
        update = extract_latest_human_update(items)

        if not update:
            continue

        clean_text = clean_status_text(update["text"])
        if not clean_text:
            continue

        update_timestamp_iso = update["timestamp"].astimezone(timezone.utc).isoformat()
        update_age_hours = round((now - update["timestamp"]).total_seconds() / 3600, 2)
        within_window = update["timestamp"] >= window_start
        update_text_prompt, truncated = truncate_text(clean_text)

        status_update = {
            "missing": False,
            "within_window": within_window,
            "timestamp": update_timestamp_iso,
            "age_hours": update_age_hours,
            "author": update["author"],
            "author_display": format_author(update["author"]),
            "activity_kind": update["activity_kind"],
            "text": clean_text,
            "text_prompt": update_text_prompt,
            "text_truncated": truncated,
        }

        record = {
            **metadata,
            "window_hours": window_hours,
            "window_start": window_start.astimezone(timezone.utc).isoformat(),
            "status_update": status_update,
        }
        records.append(record)

    return records


def prepare_prompt_payload(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    prompt_incidents = []
    for record in records:
        status_update = record["status_update"]
        prompt_incidents.append(
            {
                "incident_id": record["incident_id"],
                "title": record["title"],
                "severity": record["severity"],
                "status": record["status"],
                "assignee": record.get("assignee"),
                "has_assignee": record.get("has_assignee"),
                "teams": record.get("teams"),
                "grafana_url": record["overview_url"],
                "status_update_missing": status_update["missing"],
                "status_update_within_window": status_update["within_window"],
                "status_update_timestamp": status_update["timestamp"],
                "status_update_age_hours": status_update["age_hours"],
                "status_update_author": status_update.get("author_display"),
                "status_update_kind": status_update.get("activity_kind"),
                "status_update_text": status_update.get("text_prompt"),
                "status_update_truncated": status_update.get("text_truncated"),
            }
        )

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "incident_count": len(records),
        "incidents": prompt_incidents,
    }


def write_json(path: str, payload: Dict[str, Any]) -> None:
    Path(path).write_text(json.dumps(payload, indent=2))


def main() -> None:
    args = parse_args()

    token = args.token or get_env("GRAFANA_TOKEN", get_env("GRAFANA_SERVICE_ACCOUNT_TOKEN"))
    url = args.url or get_env("GRAFANA_URL")
    token, base_url = require_credentials(token, url)

    disk_cache = DiskCache(cache_dir=args.cache_dir, enabled=not args.no_cache, debug=args.debug)
    rate_limiter = RateLimitHandler(max_retries=3, base_delay=1.0)
    client = GrafanaIRMClient(base_url, token, rate_limit_handler=rate_limiter, debug=args.debug)

    now = datetime.now(timezone.utc)
    window_hours = max(1, args.window_hours)
    window_start = now - timedelta(hours=window_hours)

    params = {
        "dateFrom": window_start.isoformat(),
        "dateTo": now.isoformat(),
    }

    incidents: List[Dict[str, Any]] = []
    try:
        resp = client.query_incident_previews(
            params,
            disk_cache=disk_cache,
            cache_ttl_hours=4,
            include_membership=True,
        )
        incidents = resp.get("incidentPreviews") or resp.get("previews") or resp.get("incidents") or []
    except Exception as exc:  # pragma: no cover - defensive
        print(f"⚠️  Failed to fetch filtered previews ({exc}); falling back to global list")
        resp = client.query_incident_previews(disk_cache=disk_cache, cache_ttl_hours=4, include_membership=True)
        incidents = resp.get("incidentPreviews") or resp.get("previews") or resp.get("incidents") or []

    filtered: List[Tuple[Dict[str, Any], datetime]] = []
    for incident in incidents:
        modified_raw = incident.get("modifiedTime") or incident.get("updatedAt")
        modified_dt = parse_timestamp(modified_raw) if modified_raw else None
        if not modified_dt:
            continue
        if modified_dt < window_start:
            continue
        filtered.append((incident, modified_dt))

    filtered.sort(key=lambda pair: pair[1], reverse=True)
    if args.max_incidents and args.max_incidents > 0:
        filtered = filtered[: args.max_incidents]

    filtered_incidents = [item[0] for item in filtered]

    print(
        f"📈 Window start: {window_start.isoformat()} — found {len(filtered_incidents)} incidents "
        f"updated in last {window_hours}h"
    )

    records = build_records(
        filtered_incidents,
        client=client,
        disk_cache=disk_cache,
        base_url=base_url,
        window_start=window_start,
        window_hours=window_hours,
        debug=args.debug,
    )

    raw_payload = {
        "generated_at": now.isoformat(),
        "window_hours": window_hours,
        "window_start": window_start.isoformat(),
        "incident_count": len(records),
        "incidents": records,
    }
    prompt_payload = prepare_prompt_payload(records)

    write_json(args.output_json, raw_payload)
    write_json(args.prompt_output, prompt_payload)

    print(f"💾 Wrote raw dataset to {args.output_json}")
    print(f"📝 Wrote prompt payload to {args.prompt_output}")

    if args.debug:
        missing = sum(1 for rec in records if rec["status_update"]["missing"])
        stale = sum(1 for rec in records if not rec["status_update"]["within_window"])
        print(f"🔍 Debug: {missing} incidents missing human updates; {stale} newest updates outside window")


if __name__ == "__main__":
    main()
