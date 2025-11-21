#!/usr/bin/env python3
"""
Weekly Grafana IRM incident metrics reporter.

Metrics:
  - Incidents opened during the target ISO week window (Mon 00:00 – Sun 23:59:59 UTC)
  - Mean time to resolve (MTTR) for incidents resolved during that window
  - Incidents open at the start of the window (Monday 00:00 UTC)

Usage:
  export GRAFANA_SERVICE_ACCOUNT_TOKEN=...
  export GRAFANA_URL=https://your-stack.grafana.net
  export ENGINEERING_METRICS_GOOGLE_CHAT_WEBHOOK_URL=https://chat.googleapis.com/...
  python scripts/weekly-incident-metrics.py

Flags:
  --week-start YYYY-MM-DD   Anchor week start (Monday in UTC). Defaults to the previous completed week.
  --no-chat                 Skip sending to Google Chat.
  --debug                   Verbose logging.
  --token/--url/--webhook   Override environment variables (for local testing).
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List, Optional, Tuple

import requests

UTC = timezone.utc
MAX_QUERY_LIMIT = 100


def parse_timestamp(value: Optional[str]) -> Optional[datetime]:
    """Parse Grafana IRM timestamp strings."""
    if not value:
        return None
    candidates = [
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S%z",
    ]
    for fmt in candidates:
        try:
            dt = datetime.strptime(value, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=UTC)
            return dt.astimezone(UTC)
        except ValueError:
            continue
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt.astimezone(UTC)
    except Exception:
        return None


def flatten_incident(incident: Dict[str, Any]) -> Dict[str, Any]:
    """Collapse incident/previews payload into a single dict."""
    merged: Dict[str, Any] = {}

    def merge(source: Optional[Dict[str, Any]]) -> None:
        if not isinstance(source, dict):
            return
        for key, value in source.items():
            if key not in merged or merged[key] in (None, "", [], {}):
                merged[key] = value

    merge(incident)
    nested = incident.get("incident")
    merge(nested)
    if isinstance(nested, dict):
        merge(nested.get("incident"))
    preview = incident.get("incidentPreview")
    merge(preview)
    return merged


def extract_incident_id(flat: Dict[str, Any]) -> Optional[str]:
    """Best-effort incident ID extraction."""
    raw = (
        flat.get("incidentID")
        or flat.get("incidentId")
        or flat.get("id")
        or flat.get("incident_id")
    )
    if raw is None:
        return None
    return str(raw)


def iso_or_none(dt: Optional[datetime]) -> Optional[str]:
    return dt.astimezone(UTC).isoformat(timespec="seconds") if dt else None


def humanize_duration(seconds: float) -> str:
    if seconds <= 0:
        return "0h"
    minutes = int(seconds // 60)
    hours, rem_minutes = divmod(minutes, 60)
    days, rem_hours = divmod(hours, 24)
    parts: List[str] = []
    if days:
        parts.append(f"{days}d")
    if rem_hours:
        parts.append(f"{rem_hours}h")
    if rem_minutes and not days:
        parts.append(f"{rem_minutes}m")
    if not parts:
        parts.append("0h")
    return " ".join(parts)


class GrafanaIRMClient:
    """Minimal client for Grafana IRM API."""

    def __init__(self, instance_url: str, token: str, debug: bool = False):
        self.instance_url = instance_url.rstrip("/")
        self.token = token
        self.debug = debug
        self.api_base = f"{self.instance_url}/api/plugins/grafana-irm-app/resources/api/v1"
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    def _post(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.api_base}/{path}"
        if self.debug:
            print(f"POST {url} -> {json.dumps(payload)}")
        resp = requests.post(url, headers=self.headers, json=payload, timeout=45)
        resp.raise_for_status()
        return resp.json()

    def fetch_incident_previews(
        self,
        date_from: datetime,
        date_to: datetime,
        limit: int = 200,
    ) -> List[Dict[str, Any]]:
        effective_limit = min(limit, MAX_QUERY_LIMIT)
        query = {
            "limit": effective_limit,
            "orderDirection": "DESC",
            "orderBy": "createdAt",
            "dateFrom": date_from.isoformat(),
            "dateTo": date_to.isoformat(),
        }
        try:
            resp = self._post("IncidentsService.QueryIncidentPreviews", {"query": query})
            return resp.get("incidentPreviews") or resp.get("previews") or []
        except requests.HTTPError as exc:
            if self.debug:
                body = exc.response.text if exc.response is not None else ""
                print(
                    f"⚠️  QueryIncidentPreviews failed ({exc}). Falling back to QueryIncidents. "
                    f"Response body: {body}",
                    file=sys.stderr,
                )
        except Exception as exc:  # pragma: no cover - defensive
            if self.debug:
                print(
                    f"⚠️  QueryIncidentPreviews failed ({exc}). Falling back to QueryIncidents.",
                    file=sys.stderr,
                )

        query["limit"] = effective_limit
        resp = self._post("IncidentsService.QueryIncidents", {"query": query})
        return resp.get("incidents") or resp.get("items") or []

    def fetch_incidents(
        self,
        *,
        page_size: int = 200,
        max_pages: int = 20,
    ) -> List[Dict[str, Any]]:
        """Pull incidents in descending created order."""
        incidents: Dict[str, Dict[str, Any]] = {}
        seen_ids: set[str] = set()
        current_date_to: Optional[datetime] = None

        for _ in range(max_pages):
            effective_limit = min(page_size, MAX_QUERY_LIMIT)
            query: Dict[str, Any] = {
                "limit": effective_limit,
                "orderDirection": "DESC",
                "orderBy": "createdAt",
            }
            if current_date_to:
                query["dateTo"] = current_date_to.isoformat()
            resp = self._post("IncidentsService.QueryIncidents", {"query": query})
            items = resp.get("incidents") or resp.get("items") or []
            if not items:
                break

            earliest_created: Optional[datetime] = None
            for inc in items:
                flat = flatten_incident(inc)
                inc_id = extract_incident_id(flat)
                if not inc_id or inc_id in seen_ids:
                    continue
                incidents[inc_id] = inc
                seen_ids.add(inc_id)
                created_dt = parse_timestamp(
                    flat.get("createdAt")
                    or flat.get("createdTime")
                    or flat.get("created_at")
                )
                if created_dt and (
                    earliest_created is None or created_dt < earliest_created
                ):
                    earliest_created = created_dt

            if earliest_created:
                current_date_to = earliest_created - timedelta(seconds=1)

            if len(items) < effective_limit:
                break

        return list(incidents.values())


def determine_week_window(week_start_str: Optional[str]) -> Tuple[datetime, datetime]:
    """Return Monday 00:00 UTC start and Sunday 23:59:59 end."""
    if week_start_str:
        try:
            week_start_date = datetime.strptime(week_start_str, "%Y-%m-%d").date()
        except ValueError as exc:
            raise SystemExit(f"Invalid --week-start format: {exc}") from exc
        week_start = datetime.combine(week_start_date, datetime.min.time(), tzinfo=UTC)
    else:
        now = datetime.now(UTC)
        current_week_start_date = now.date() - timedelta(days=now.weekday())
        week_start_date = current_week_start_date - timedelta(days=7)
        week_start = datetime.combine(week_start_date, datetime.min.time(), tzinfo=UTC)

    week_end = week_start + timedelta(days=7) - timedelta(seconds=1)
    return week_start, week_end


def build_incident_summary(flat: Dict[str, Any]) -> Dict[str, Any]:
    incident_id = extract_incident_id(flat)
    title_raw = flat.get("title") or flat.get("name") or ""
    title = title_raw.strip() if isinstance(title_raw, str) else None
    severity = flat.get("severity") or flat.get("incidentSeverity")
    status_raw = flat.get("status") or ""
    status = status_raw.lower() if isinstance(status_raw, str) else status_raw
    created_dt = parse_timestamp(
        flat.get("createdAt") or flat.get("createdTime") or flat.get("created_at")
    )
    resolved_dt = parse_timestamp(
        flat.get("resolvedAt")
        or flat.get("closedTime")
        or flat.get("resolved_at")
        or flat.get("closedAt")
    )
    assignee = None
    membership = flat.get("incidentMembership") or {}
    if isinstance(membership, dict):
        assignee_info = membership.get("assignee")
        if isinstance(assignee_info, dict):
            assignee_name = assignee_info.get("name") or assignee_info.get("displayName")
            if assignee_name:
                assignee = assignee_name.strip()

    return {
        "incident_id": incident_id,
        "title": title,
        "severity": severity,
        "status": status,
        "assignee": assignee,
        "created_at": iso_or_none(created_dt),
        "resolved_at": iso_or_none(resolved_dt),
    }


def collect_weekly_lists(
    previews: Iterable[Dict[str, Any]],
    window_start: datetime,
    window_end: datetime,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    opened: List[Dict[str, Any]] = []
    resolved: List[Dict[str, Any]] = []

    for raw in previews:
        flat = flatten_incident(raw)
        created_dt = parse_timestamp(
            flat.get("createdAt") or flat.get("createdTime") or flat.get("created_at")
        )
        resolved_dt = parse_timestamp(
            flat.get("resolvedAt")
            or flat.get("closedTime")
            or flat.get("resolved_at")
            or flat.get("closedAt")
        )
        if created_dt and window_start <= created_dt <= window_end:
            opened.append(build_incident_summary(flat))
        if resolved_dt and window_start <= resolved_dt <= window_end:
            resolved.append(build_incident_summary(flat))
    return opened, resolved


def collect_open_as_of(
    incidents: Iterable[Dict[str, Any]],
    snapshot_time: datetime,
) -> List[Dict[str, Any]]:
    open_list: List[Dict[str, Any]] = []
    for raw in incidents:
        flat = flatten_incident(raw)
        created_dt = parse_timestamp(
            flat.get("createdAt") or flat.get("createdTime") or flat.get("created_at")
        )
        resolved_dt = parse_timestamp(
            flat.get("resolvedAt")
            or flat.get("closedTime")
            or flat.get("resolved_at")
            or flat.get("closedAt")
        )
        if created_dt and created_dt <= snapshot_time:
            if not resolved_dt or resolved_dt >= snapshot_time:
                open_list.append(build_incident_summary(flat))
    return open_list


def compute_mean_resolution_seconds(records: Iterable[Dict[str, Any]]) -> Optional[float]:
    durations: List[float] = []
    for rec in records:
        created = parse_timestamp(rec.get("created_at"))
        resolved = parse_timestamp(rec.get("resolved_at"))
        if created and resolved and resolved >= created:
            durations.append((resolved - created).total_seconds())
    if not durations:
        return None
    return sum(durations) / len(durations)


def send_to_google_chat(webhook: str, summary: List[str]) -> None:
    payload = {"text": "\n".join(summary)}
    resp = requests.post(
        webhook,
        headers={"Content-Type": "application/json"},
        json=payload,
        timeout=30,
    )
    if resp.status_code != 200:
        print(
            f"⚠️  Google Chat webhook returned {resp.status_code}: {resp.text}",
            file=sys.stderr,
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Weekly incident metrics reporter")
    parser.add_argument("--week-start", help="Week start in YYYY-MM-DD (UTC Monday)")
    parser.add_argument("--token", help="Grafana IRM service account token")
    parser.add_argument("--url", help="Grafana IRM base URL")
    parser.add_argument("--webhook", help="Google Chat webhook override")
    parser.add_argument("--no-chat", action="store_true", help="Skip Google Chat")
    parser.add_argument(
        "--page-size",
        type=int,
        default=200,
        help="Incidents page size when backfilling (default: 200)",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=20,
        help="Maximum incident pages to fetch (default: 20)",
    )
    parser.add_argument("--debug", action="store_true", help="Verbose API logging")
    args = parser.parse_args()

    token = (
        args.token
        or os.environ.get("GRAFANA_TOKEN")
        or os.environ.get("GRAFANA_SERVICE_ACCOUNT_TOKEN")
    )
    url = args.url or os.environ.get("GRAFANA_URL")
    webhook = (
        args.webhook
        or os.environ.get("ENGINEERING_METRICS_GOOGLE_CHAT_WEBHOOK_URL")
    )

    if not token or not url:
        print(
            "❌ Provide --token/--url or set GRAFANA_SERVICE_ACCOUNT_TOKEN and GRAFANA_URL",
            file=sys.stderr,
        )
        sys.exit(1)

    week_start, week_end = determine_week_window(args.week_start)
    if args.debug:
        print(
            f"Week window: {week_start.isoformat()} to {week_end.isoformat()} (UTC)",
            file=sys.stderr,
        )

    client = GrafanaIRMClient(url, token, debug=args.debug)

    previews = client.fetch_incident_previews(week_start, week_end)
    opened, resolved = collect_weekly_lists(previews, week_start, week_end)

    all_incidents = client.fetch_incidents(
        page_size=max(1, args.page_size),
        max_pages=max(1, args.max_pages),
    )
    open_as_of = collect_open_as_of(all_incidents, week_start)

    mean_seconds = compute_mean_resolution_seconds(resolved)
    mttr_human = humanize_duration(mean_seconds) if mean_seconds else None

    metrics = {
        "week_start_utc": week_start.isoformat(),
        "week_end_utc": week_end.isoformat(),
        "incidents_opened_count": len(opened),
        "incidents_resolved_count": len(resolved),
        "mean_time_to_resolve_seconds": (
            round(mean_seconds, 2) if mean_seconds is not None else None
        ),
        "mean_time_to_resolve_human": mttr_human,
        "open_at_week_start_count": len(open_as_of),
        "generated_at_utc": datetime.now(UTC).isoformat(timespec="seconds"),
    }

    payload = {
        "metrics": metrics,
        "opened_incidents": opened,
        "resolved_incidents": resolved,
        "open_as_of_week_start": open_as_of,
    }

    print(json.dumps(payload, indent=2))

    if webhook and not args.no_chat:
        summary_lines = [
            f"Weekly Incident Metrics ({metrics['week_start_utc']} – {metrics['week_end_utc']})",
            f"- Opened: {metrics['incidents_opened_count']}",
            f"- Resolved: {metrics['incidents_resolved_count']}",
            f"- MTTR: {metrics['mean_time_to_resolve_human'] or 'n/a'}",
            f"- Open at week start: {metrics['open_at_week_start_count']}",
        ]
        try:
            send_to_google_chat(webhook, summary_lines)
            print("✅ Sent weekly metrics to Google Chat")
        except Exception as exc:
            print(f"⚠️  Failed to send to Google Chat: {exc}", file=sys.stderr)


if __name__ == "__main__":
    main()
