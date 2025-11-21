#!/usr/bin/env python3
"""
Grafana IRM Incident Reporter (Refactored)
Consolidated view of active incidents with over-SLA flags and latest updates.
"""

import os
import sys
import json
import argparse
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple, Callable
from pathlib import Path
import requests

# Import from incident_reporter package
from incident_reporter import (
    DiskCache,
    GrafanaIRMClient,
    RateLimitHandler,
    MetricsCalculator,
    GMT_PLUS_7,
    get_yesterday_range,
    get_last_week_range,
    get_last_month_range,
    parse_timestamp,
    is_human_user,
    sort_active,
    compute_stats,
    IncidentEnricher,
    ReportFormatter,
)


class IncidentReporterCompact:
    """Orchestrates incident reporting using modular components"""
    
    def __init__(self, client: GrafanaIRMClient, max_active: Optional[int] = None, disk_cache: Optional[DiskCache] = None):
        self.client = client
        self.max_active = max_active
        self.disk_cache = disk_cache or DiskCache(enabled=False)
        self.sla_by_severity = {"Critical": 1, "Major": 2, "Minor": 3}

        # Initialize enricher
        self.enricher = IncidentEnricher(
            client=self.client,
            disk_cache=self.disk_cache,
            parse_timestamp_func=parse_timestamp,
            sla_by_severity=self.sla_by_severity,
        )

        # Initialize metrics calculator
        self.metrics_calc = MetricsCalculator(
            parse_timestamp_func=parse_timestamp,
            disk_cache=self.disk_cache,
            fetch_last_update_func=self.enricher.fetch_last_update,
        )

        # Initialize formatter  
        self.formatter = ReportFormatter(
            metrics_calc=self.metrics_calc,
            max_active=self.max_active,
        )

    @property
    def cache_hits(self):
        return self.enricher.cache_hits

    @property
    def cache_misses(self):
        return self.enricher.cache_misses
def main():
    parser = argparse.ArgumentParser(description="Grafana IRM Incident Reporter (Compact)")
    parser.add_argument("--token", help="Grafana token (or set GRAFANA_TOKEN/GRAFANA_SERVICE_ACCOUNT_TOKEN)")
    parser.add_argument("--url", help="Grafana instance URL (or set GRAFANA_URL)")
    parser.add_argument("--date", help="Report date (YYYY-MM-DD, default: yesterday)")
    parser.add_argument("--start-date", help="Start date for date range (YYYY-MM-DD, use with --end-date)")
    parser.add_argument("--end-date", help="End date for date range (YYYY-MM-DD, use with --start-date)")
    parser.add_argument("--weekly", action="store_true", help="Generate weekly report (Tuesday to Monday)")
    parser.add_argument("--week-offset", type=int, default=0, help="Weeks back from last completed week (0=last week, 1=week before, etc.)")
    parser.add_argument("--monthly", action="store_true", help="Generate monthly report (1st to last day of previous month)")
    parser.add_argument("--month-offset", type=int, default=0, help="Months back from last completed month (0=last month, 1=month before, etc.)")
    parser.add_argument("--max-active", type=int, default=0, help="Max active incidents to display (0 = all)")
    parser.add_argument("--webhook", help="Google Chat webhook URL (or set GOOGLE_CHAT_WEBHOOK_URL)")
    parser.add_argument("--no-chat", action="store_true", help="Do not send to Google Chat")
    parser.add_argument("--save-md", action="store_true", help="Write Markdown report to disk (opt-in)")
    parser.add_argument("--md-path", help="Custom Markdown output path (used only with --save-md)")
    parser.add_argument("--debug", action="store_true", help="Verbose debug output")

    # Cache management options
    parser.add_argument("--cache-dir", default=".cache/incidents", help="Cache directory path (default: .cache/incidents)")
    parser.add_argument("--no-cache", action="store_true", help="Disable disk caching (fetch fresh data)")
    parser.add_argument("--clear-cache", action="store_true", help="Clear all cached data before running")
    parser.add_argument("--cache-stats", action="store_true", help="Display cache statistics and exit")

    # Data fetching options
    parser.add_argument("--fetch-all", action="store_true", help="Fetch all incidents from 2025-01-01 to now (for cache building)")

    args = parser.parse_args()

    # Initialize disk cache
    disk_cache = DiskCache(cache_dir=args.cache_dir, enabled=not args.no_cache, debug=args.debug)

    # Handle cache-only operations
    if args.cache_stats:
        stats = disk_cache.get_cache_stats()
        print("📊 Cache Statistics")
        print("-" * 40)
        if stats.get("enabled"):
            print(f"Status: Enabled")
            print(f"Location: {stats.get('cache_dir', 'N/A')}")
            print(f"Cached Incidents: {stats.get('total_cached', 0)}")
            print(f"Cached Activity: {stats.get('activity_cached', 0)}")
            print(f"Total Cache Size: {stats.get('cache_size_mb', 0)} MB")
            if "error" in stats:
                print(f"Error: {stats['error']}")
        else:
            print("Status: Disabled")
        sys.exit(0)

    if args.clear_cache:
        print("🗑️  Clearing cache...")
        disk_cache.clear_cache()

    token = (
        args.token
        or os.environ.get("GRAFANA_TOKEN")
        or os.environ.get("GRAFANA_SERVICE_ACCOUNT_TOKEN")
    )
    url = args.url or os.environ.get("GRAFANA_URL")
    webhook = args.webhook or os.environ.get("GOOGLE_CHAT_WEBHOOK_URL")
    if not token or not url:
        print("❌ Error: provide --token/--url or set GRAFANA_SERVICE_ACCOUNT_TOKEN and GRAFANA_URL")
        sys.exit(1)

    # Initialize client with rate limiting
    rate_limiter = RateLimitHandler(max_retries=3, base_delay=1.0)
    client = GrafanaIRMClient(url, token, rate_limit_handler=rate_limiter, debug=args.debug)

    max_active = None if (not args.max_active or args.max_active <= 0) else args.max_active
    reporter = IncidentReporterCompact(client, max_active=max_active, disk_cache=disk_cache)

    # Determine report type and date range (priority: weekly/monthly > start/end-date > date > yesterday)
    report_type = "daily"  # Default report type

    if args.weekly and args.monthly:
        print("❌ Error: Cannot use both --weekly and --monthly at the same time")
        sys.exit(1)

    if args.weekly:
        # Weekly report mode (Tuesday to Monday)
        report_type = "weekly"
        date_start, date_end = get_last_week_range(weeks_ago=args.week_offset)
        if args.debug:
            start_local = date_start.astimezone(GMT_PLUS_7)
            end_local = date_end.astimezone(GMT_PLUS_7)
            offset_info = f" ({args.week_offset} week{'s' if args.week_offset != 1 else ''} ago)" if args.week_offset > 0 else ""
            print(f"📅 Weekly report{offset_info}: {start_local.strftime('%Y-%m-%d')} to {end_local.strftime('%Y-%m-%d')}")
    elif args.monthly:
        # Monthly report mode (1st to last day of previous month)
        report_type = "monthly"
        date_start, date_end = get_last_month_range(months_ago=args.month_offset)
        if args.debug:
            start_local = date_start.astimezone(GMT_PLUS_7)
            end_local = date_end.astimezone(GMT_PLUS_7)
            offset_info = f" ({args.month_offset} month{'s' if args.month_offset != 1 else ''} ago)" if args.month_offset > 0 else ""
            print(f"📅 Monthly report{offset_info}: {start_local.strftime('%Y-%m-%d')} to {end_local.strftime('%Y-%m-%d')}")
    elif args.start_date and args.end_date:
        # Date range mode
        try:
            start_local = datetime.strptime(args.start_date, "%Y-%m-%d").replace(tzinfo=GMT_PLUS_7)
            start_local = datetime.combine(start_local.date(), datetime.min.time()).replace(tzinfo=GMT_PLUS_7)

            end_local = datetime.strptime(args.end_date, "%Y-%m-%d").replace(tzinfo=GMT_PLUS_7)
            end_local = datetime.combine(end_local.date(), datetime.max.time()).replace(tzinfo=GMT_PLUS_7)

            if start_local > end_local:
                print("❌ Error: start-date must be before or equal to end-date")
                sys.exit(1)

            date_start = start_local.astimezone(timezone.utc)
            date_end = end_local.astimezone(timezone.utc)
        except ValueError:
            print("❌ Error: Invalid date format. Use YYYY-MM-DD for both --start-date and --end-date")
            sys.exit(1)
    elif args.start_date or args.end_date:
        # Error: need both start and end date
        print("❌ Error: Both --start-date and --end-date must be provided together")
        sys.exit(1)
    elif args.date:
        # Single date mode (existing behavior)
        try:
            target_local = datetime.strptime(args.date, "%Y-%m-%d").replace(tzinfo=GMT_PLUS_7)
            start_local = datetime.combine(
                target_local.date(),
                datetime.min.time(),
            ).replace(tzinfo=GMT_PLUS_7)
            end_local = datetime.combine(
                target_local.date(),
                datetime.max.time(),
            ).replace(tzinfo=GMT_PLUS_7)
            date_start = start_local.astimezone(timezone.utc)
            date_end = end_local.astimezone(timezone.utc)
        except ValueError:
            print("❌ Error: Invalid date format. Use YYYY-MM-DD")
            sys.exit(1)
    else:
        # Default: yesterday
        date_start, date_end = get_yesterday_range()

    # Fetch opened/resolved using the original incidents query + local filters
    try:
        # Choose fetch window based on --fetch-all flag
        if args.fetch_all:
            # Broad window (2025-01-01 to yesterday midnight) for building comprehensive cache
            # Use yesterday midnight instead of "now" to ensure stable cache key throughout the day
            fetch_start_date = datetime(2025, 1, 1, 0, 0, 0, tzinfo=GMT_PLUS_7).astimezone(timezone.utc)
            yesterday_midnight = datetime.combine(
                (datetime.now(GMT_PLUS_7) - timedelta(days=1)).date(),
                datetime.max.time()
            ).replace(tzinfo=GMT_PLUS_7).astimezone(timezone.utc)
            fetch_end_date = yesterday_midnight
            if args.debug:
                print(f"📥 Fetching all incidents from 2025-01-01 to yesterday midnight (--fetch-all enabled)")
        else:
            # Use report date range for targeted fetching (default)
            # Fewer pages, faster for single reports
            fetch_start_date = date_start
            fetch_end_date = date_end
            if args.debug:
                date_start_local = date_start.astimezone(GMT_PLUS_7)
                date_end_local = date_end.astimezone(GMT_PLUS_7)
                print(f"📥 Fetching incidents from {date_start_local.strftime('%Y-%m-%d')} to {date_end_local.strftime('%Y-%m-%d')}")

        params = {
            "dateFrom": fetch_start_date.isoformat(),
            "dateTo": fetch_end_date.isoformat()
        }

        try:
            resp = client.query_incident_previews(params, disk_cache=disk_cache, cache_ttl_hours=24, include_membership=True)
            incs = resp.get("incidentPreviews") or resp.get("previews") or []
        except Exception as e:
            # Fallback: if date params don't work, fetch all incidents
            if args.debug:
                print(f"⚠️  Error with date params, falling back: {e}")
            resp = client.query_incident_previews(disk_cache=disk_cache, cache_ttl_hours=24, include_membership=True)
            incs = resp.get("incidentPreviews") or resp.get("previews") or []
            if not incs:
                resp = client.query_incidents()
                incs = resp.get("incidents", [])

        def parse_ts(s: Optional[str]) -> Optional[datetime]:
            return parse_timestamp(s) if s else None

        # Filter incidents from the same cached data
        opened, resolved, raw_active = [], [], []
        for inc in incs:
            created = parse_ts(inc.get("createdAt") or inc.get("createdTime"))
            closed = parse_ts(inc.get("resolvedAt") or inc.get("closedTime"))
            status = (inc.get("status") or "").lower()

            # Opened in date range
            if created and date_start <= created <= date_end:
                opened.append(inc)

            # Resolved in date range
            if closed and date_start <= closed <= date_end:
                resolved.append(inc)

            # Active at the END of the report period
            # For weekly/monthly reports: incidents that were still open at date_end
            # An incident is "active at date_end" if:
            # 1. Created before or during period (created <= date_end)
            # 2. Either never resolved OR resolved AFTER date_end (closed is None or closed > date_end)
            if created and created <= date_end:
                # Check if it was still open at the end of the report period
                if not closed or closed > date_end:
                    raw_active.append(inc)
            elif not created and status in ("active", "open"):
                # Edge case: no created date but currently active, include it
                raw_active.append(inc)

        # Enrich active incidents
        # For weekly/monthly reports, calculate age relative to end of period for accurate historical data
        # This is an improvement over the original code which used NOW
        calc_time = date_end if report_type in ("weekly", "monthly") else None
        active = reporter.enricher.enrich_active_incidents(raw_active, calculation_time=calc_time)

        # Enrich opened/resolved data for consistent formatting/stats
        opened = reporter.enricher.enrich_recent_incidents(
            opened, use_resolved_time=False, calculation_time=calc_time
        )
        resolved = reporter.enricher.enrich_recent_incidents(resolved, use_resolved_time=True)

        # Generate report based on type
        if report_type == "weekly":
            report = reporter.formatter.generate_weekly_report(
                opened, resolved, active, date_start, date_end, current_active_count=len(raw_active)
            )
        elif report_type == "monthly":
            report = reporter.formatter.generate_monthly_report(
                opened, resolved, active, date_start, date_end, current_active_count=len(raw_active)
            )
        else:
            report = reporter.formatter.generate_report(opened, resolved, active)
        print("\n" + report)

        # Show cache statistics if debug mode
        if args.debug:
            print("\n" + "=" * 40)
            print("📊 Performance Summary")
            print("-" * 40)
            print(f"• Total API Calls: {client.api_call_count}")

            if disk_cache.enabled:
                total_requests = reporter.cache_hits + reporter.cache_misses
                hit_rate = (reporter.cache_hits / total_requests * 100) if total_requests > 0 else 0
                print(f"• Cache Hits: {reporter.cache_hits}")
                print(f"• Cache Misses: {reporter.cache_misses}")
                print(f"• Cache Hit Rate: {hit_rate:.1f}%")
                cache_stats = disk_cache.get_cache_stats()
                print(f"• Incidents Cached: {cache_stats.get('total_cached', 0)}")
                print(f"• Activity Cached: {cache_stats.get('activity_cached', 0)}")
                print(f"• Preview Lists Cached: {cache_stats.get('preview_lists_cached', 0)}")
                print(f"• Cache Size: {cache_stats.get('cache_size_mb', 0):.2f} MB")
                print(f"• Cache Dir: {cache_stats.get('cache_dir', 'N/A')}")
            print("=" * 40)

        # Optionally save Markdown (opt-in)
        if args.save_md:
            start_utc = date_start.astimezone(timezone.utc)
            end_utc = date_end.astimezone(timezone.utc)

            # Create report directory if it doesn't exist
            report_dir = "report"
            os.makedirs(report_dir, exist_ok=True)

            if report_type == "weekly":
                filename = f"REPORT_WEEKLY_{start_utc.strftime('%Y-%m-%d')}_{end_utc.strftime('%Y-%m-%d')}.md"
                title = "Weekly Incident Report (UTC)"
                date_info = f"Week: {start_utc.strftime('%Y-%m-%d')} to {end_utc.strftime('%Y-%m-%d')} (UTC)"
            elif report_type == "monthly":
                filename = f"REPORT_MONTHLY_{end_utc.strftime('%Y-%m')}.md"
                title = "Monthly Incident Report (UTC)"
                date_info = f"Month: {end_utc.strftime('%B %Y')} (UTC)"
            else:
                # Keep daily report as GMT+7 (as requested)
                start_local = date_start.astimezone(GMT_PLUS_7)
                end_local = date_end.astimezone(GMT_PLUS_7)
                filename = f"REPORT_DAILY_{start_local.strftime('%Y-%m-%d')}.md"
                title = "Daily Incident Report (GMT+7)"
                date_info = f"Report date: {start_local.strftime('%Y-%m-%d')} (GMT+7)"

            # Save to report directory unless custom path specified
            if args.md_path:
                md_path = args.md_path
            else:
                md_path = os.path.join(report_dir, filename)
            with open(md_path, "w") as f:
                f.write(f"# {title}\n\n")
                f.write(f"{date_info}\n\n")
                f.write("```\n")
                f.write(report)
                f.write("\n```\n")
            print(f"\n💾 Report saved to: {md_path}")

        # Optionally send to Google Chat as plain text
        if webhook and not args.no_chat:
            try:
                # Bold "Missing status update" in Chat card body
                chat_text = report.replace('⚠️ Missing status update', '⚠️ <b>Missing status update</b>')
                # Do not bold the header's Missing Status Updates line; keep row-level bold only
                payload = {
                    "cards": [
                        {
                            "sections": [
                                {
                                    "widgets": [
                                        {"textParagraph": {"text": chat_text}}
                                    ]
                                }
                            ]
                        }
                    ]
                }
                resp = requests.post(
                    webhook,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=20,
                )
                if resp.status_code == 200:
                    print("✅ Sent compact report to Google Chat")
                else:
                    print(f"⚠️  Google Chat webhook returned {resp.status_code}: {resp.text}")
            except Exception as e:
                print(f"⚠️  Failed to send to Google Chat: {e}")

    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
