"""
Report formatting module

Handles:
- Generating daily, weekly, and monthly reports
- Formatting incident entries
- Severity emojis and display helpers
"""

from datetime import datetime
from html import escape
from typing import Dict, List, Optional

from .time_helpers import GMT_PLUS_7, parse_timestamp
from .incident_stats import compute_stats, sort_active


class ReportFormatter:
    """Formats incident reports for display"""

    def __init__(self, metrics_calc, max_active: Optional[int] = None):
        """
        Args:
            metrics_calc: MetricsCalculator instance
            max_active: Maximum number of active incidents to display
        """
        self.metrics_calc = metrics_calc
        self.max_active = max_active

    def severity_emoji(self, severity: str) -> str:
        """Get emoji for severity level"""
        severity = (severity or "").lower()
        if severity == "critical":
            return "🔴"
        elif severity == "major":
            return "🟠"
        elif severity == "minor":
            return "🟡"
        elif severity == "low":
            return "🟢"
        else:
            return "❓"

    def clean_title(self, title: str) -> str:
        """Clean incident title for display"""
        if not title:
            return ""
        title = (
            title.replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace("&", "&amp;")
        )
        max_len = 65
        if len(title) > max_len:
            title = title[:max_len] + "..."
        return title

    def format_age(self, age_days: float) -> str:
        """Format age in days"""
        if age_days < 1:
            return "< 1 day"
        elif age_days < 2:
            return f"{age_days:.1f} day"
        else:
            return f"{round(age_days)} days"

    def format_last_update(self, last_time: Optional[str], last_kind: Optional[str]) -> str:
        """Format last update time"""
        if not last_time:
            return "⚠️ Missing status update"
        dt = parse_timestamp(last_time)
        if not dt:
            return "⚠️ Missing status update"
        # Relative time from local now
        now_local = datetime.now(GMT_PLUS_7)
        delta = now_local - dt.astimezone(GMT_PLUS_7)
        secs = int(max(delta.total_seconds(), 0))
        if secs < 60:
            rel = "just now"
        elif secs < 3600:
            rel = f"{secs // 60}m ago"
        elif secs < 86400:
            rel = f"{secs // 3600}h ago"
        else:
            rel = f"{secs // 86400}d ago"
        return f"📝 {rel}"

    def format_incident_entry(self, incident: Dict) -> str:
        """Format a single incident entry for display"""
        emoji = self.severity_emoji(incident.get("severity", ""))
        title = self.clean_title(incident.get("title", "Untitled"))
        slug = incident.get("slug", "")
        incident_id = incident.get("incidentID") or incident.get("id")
        age_str = self.format_age(incident.get("age_days", 0))

        # Show assignee name or unassigned indicator
        if incident.get("has_assignee") and incident.get("assignee"):
            assignee_str = f"👤 {escape(str(incident['assignee']))}"
        else:
            assignee_str = "❌👤"

        # Build URL
        url = f"https://finnapp.grafana.net/a/grafana-irm-app/incidents/{incident_id}/{slug}"
        link = f'<a href="{url}">{title}</a>'

        # SLA info
        sla_str = ""
        if incident.get("over_sla"):
            days_over = incident.get("days_over_sla", 0)
            sla_str = f"⏰ <b>+{round(days_over)}d</b>"

        # Last update
        last_update_str = self.format_last_update(
            incident.get("last_update_time"),
            incident.get("last_update_kind"),
        )

        # Build entry
        parts = [emoji, link, "|", age_str, "|", assignee_str]
        if sla_str:
            parts.append("|")
            parts.append(sla_str)
        if last_update_str:
            parts.append("|")
            parts.append(last_update_str)

        return "  " + " ".join(parts)
    def generate_report(self, opened: List[Dict], resolved: List[Dict], active: List[Dict]) -> str:
        today_gmt7 = datetime.now(GMT_PLUS_7)
        date_str = f"{today_gmt7.day}-{today_gmt7.strftime('%b-%Y')}"

        active_stats = compute_stats(active)
        opened_total = len(opened)
        resolved_total = len(resolved)

        report = []
        report.append("=" * 40)
        report.append("📊 <b>Daily Incident Report</b>")
        report.append(f"📅 {date_str} (GMT+7)")
        report.append("=" * 40)
        report.append("")
        report.append("📋 <b>Summary</b>")
        report.append("-" * 40)
        report.append(f"• 🔥 Total Active: {active_stats['total']}")
        if active_stats["without_severity"] > 0:
            report.append(f"• ❓ Without Severity: {active_stats['without_severity']}")
        if active_stats["without_assignee"] > 0:
            report.append(f"• ❌👤 Without Assignee: {active_stats['without_assignee']}")
        if active_stats["missing_updates"] > 0:
            report.append(f"• 📝 Missing Status Updates: {active_stats['missing_updates']}")
        report.append(f"• ⏰ Over SLA: {active_stats['over_sla']}")
        report.append(f"• 🆕 Opened Yesterday: {opened_total}")
        report.append(f"• ✅ Resolved Yesterday: {resolved_total}")
        report.append("")

        # Consolidated active section
        sorted_items = sort_active(active)
        top = sorted_items if self.max_active is None else sorted_items[: self.max_active]
        if self.max_active is None:
            report.append("🔥 <b>Active Incidents</b>")
        else:
            report.append(f"🔥 <b>Active Incidents</b> — showing {len(top)} of {len(active)}")
        report.append("-" * 40)
        if not top:
            report.append("  No active incidents")
        else:
            for inc in top:
                report.append(self.format_incident_entry(inc))
        report.append("")

        # Opened yesterday section
        report.append(f"🔴 <b>Opened Yesterday</b>: {opened_total}")
        report.append("-" * 40)
        if opened_total > 0:
            for inc in opened:
                report.append(self.format_incident_entry(inc))
        else:
            report.append("  None")
        report.append("")

        # Resolved yesterday section
        report.append(f"✅ <b>Resolved Yesterday</b>: {resolved_total}")
        report.append("-" * 40)
        if resolved_total > 0:
            for inc in resolved:
                report.append(self.format_incident_entry(inc))
        else:
            report.append("  None")
        # No trailing separator line to keep message tight
        return "\n".join(report)

    def generate_weekly_report(self, opened: List[Dict], resolved: List[Dict], active: List[Dict],
                               start_date: datetime, end_date: datetime, current_active_count: Optional[int] = None) -> str:
        """Generate weekly report (Tuesday to Monday)

        Args:
            opened: Incidents opened during the week
            resolved: Incidents resolved during the week
            active: Currently active incidents (as of end of week)
            start_date: Start of week (Monday 00:00:00 UTC)
            end_date: End of week (Sunday 23:59:59 UTC)
            current_active_count: Current number of open incidents (as of report generation time)
        """
        # Use end_date as calculation time for all metrics
        calculation_time = end_date

        # Dates are already in UTC
        start_utc = start_date
        end_utc = end_date

        # Format: "21-27 Oct 2025"
        if start_utc.year == end_utc.year and start_utc.month == end_utc.month:
            date_range = f"{start_utc.day}-{end_utc.day} {end_utc.strftime('%b %Y')}"
        elif start_utc.year == end_utc.year:
            date_range = f"{start_utc.day} {start_utc.strftime('%b')} - {end_utc.day} {end_utc.strftime('%b %Y')}"
        else:
            date_range = f"{start_utc.strftime('%d %b %Y')} - {end_utc.strftime('%d %b %Y')}"

        # Calculate metrics
        active_stats = compute_stats(active)
        opened_total = len(opened)
        resolved_total = len(resolved)

        # Calculate opened+resolved count (incidents with complete lifecycle in this period)
        opened_ids = {inc.get("incidentID") or inc.get("id") for inc in opened}
        opened_and_resolved = [inc for inc in resolved if (inc.get("incidentID") or inc.get("id")) in opened_ids]
        opened_and_resolved_total = len(opened_and_resolved)

        # Calculate both MTTR metrics
        mttr_opened_and_resolved = self.metrics_calc.calculate_mttr(resolved, opened_incidents=opened, start_date=start_date, end_date=end_date)
        mttr_all_resolved = self.metrics_calc.calculate_mttr(resolved)  # Legacy: all resolved incidents

        # Calculate both MTTD metrics
        mttd_opened_and_resolved = self.metrics_calc.calculate_mttd(opened_and_resolved) if opened_and_resolved else None
        mttd_all_resolved = self.metrics_calc.calculate_mttd(resolved)

        oldest_age = self.metrics_calc.calculate_oldest_active_age(active, calculation_time=calculation_time)
        daily_breakdown = self.metrics_calc.calculate_daily_breakdown(opened, start_date, end_date)

        report = []
        report.append("=" * 40)
        report.append("📊 <b>Weekly Incident Report</b>")
        report.append(f"📅 {date_range} (UTC)")
        report.append("=" * 40)
        report.append("")

        # Count critical incidents opened
        critical_opened = sum(1 for inc in opened if (inc.get("severity") or "").lower() == "critical")

        # Calculate carry over and net change
        # Carry over = incidents that existed at start of week
        # Formula: end_active - opened + resolved = start_active
        carry_over = active_stats['total'] - opened_total + resolved_total
        net_change = active_stats['total'] - carry_over

        # Summary section - Option B layout
        report.append("📋 <b>Summary</b>")
        report.append("-" * 40)

        # 📊 Current Status section
        report.append("📊 <b>Current Status</b>")
        if current_active_count is not None:
            report.append(f"• 🔥 Current Open Incidents: {current_active_count}")
        sign = "+" if net_change >= 0 else ""
        report.append(f"• 🔥 Total Active (end of week): {active_stats['total']} ({sign}{net_change} from last week)")

        # Oldest Active - show "-" if no active incidents, otherwise show the calculated value
        if active_stats['total'] == 0:
            report.append(f"• ⏳ Oldest Active: -")
        elif oldest_age is not None:
            if oldest_age < 24:
                report.append(f"• ⏳ Oldest Active: {oldest_age:.1f} hours")
            else:
                report.append(f"• ⏳ Oldest Active: {oldest_age/24:.1f} days")
        else:
            report.append(f"• ⏳ Oldest Active: -")

        report.append(f"• ⏰ Over SLA: {active_stats['over_sla']}")
        report.append(f"• ❌👤 Without Assignee: {active_stats['without_assignee']}")
        report.append("")

        # 📈 Weekly Activity section
        report.append("📈 <b>Weekly Activity</b>")
        report.append(f"• 🔄 Started with: {carry_over} incident{'s' if carry_over != 1 else ''}")
        report.append(f"• 🆕 Opened This Week: {opened_total}")
        report.append(f"  ↳ 🔴 Critical: {critical_opened}")
        report.append(f"• ✅ Resolved This Week: {resolved_total}")
        report.append(f"  ↳ Opened & Resolved in Week: {opened_and_resolved_total}")
        report.append("")

        # ⏱️ Performance Metrics section
        report.append("⏱️ <b>Performance Metrics</b>")

        # MTTR - show only all resolved (always in hours for consistency)
        if resolved_total == 0:
            report.append(f"• MTTR: -")
        else:
            if mttr_all_resolved is not None:
                report.append(f"• MTTR: {mttr_all_resolved:.1f}h")
            else:
                report.append(f"• MTTR: -")

        # MTTD - show only all resolved (always in hours for consistency)
        if resolved_total == 0:
            report.append(f"• MTTD: -")
        else:
            if mttd_all_resolved is not None:
                report.append(f"• MTTD: {mttd_all_resolved:.1f}h")
            else:
                report.append(f"• MTTD: -")

        report.append("")

        # Daily breakdown
        report.append("📅 <b>Daily Breakdown</b>")
        report.append("-" * 40)
        for date_key in sorted(daily_breakdown.keys()):
            count = daily_breakdown[date_key]
            # Format: "Mon 30 Sep: 5 incidents"
            dt = datetime.strptime(date_key, '%Y-%m-%d').replace(tzinfo=GMT_PLUS_7)
            day_label = dt.strftime('%a %d %b')
            report.append(f"  {day_label}: {count} incident{'s' if count != 1 else ''}")
        report.append("")

        # Active incidents section
        sorted_items = sort_active(active)
        top = sorted_items if self.max_active is None else sorted_items[:self.max_active]
        if self.max_active is None:
            report.append("🔥 <b>Active Incidents</b>")
        else:
            report.append(f"🔥 <b>Active Incidents</b> — showing {len(top)} of {len(active)}")
        report.append("-" * 40)
        if not top:
            report.append("  No active incidents")
        else:
            for inc in top:
                report.append(self.format_incident_entry(inc))
        report.append("")

        # Opened this week section
        report.append(f"🔴 <b>Opened This Week</b>: {opened_total}")
        report.append("-" * 40)
        if opened_total > 0:
            for inc in opened:
                report.append(self.format_incident_entry(inc))
        else:
            report.append("  None")
        report.append("")

        # Resolved this week section
        report.append(f"✅ <b>Resolved This Week</b>: {resolved_total}")
        report.append("-" * 40)
        if resolved_total > 0:
            for inc in resolved:
                report.append(self.format_incident_entry(inc))
        else:
            report.append("  None")

        return "\n".join(report)


    def generate_monthly_report(self, opened: List[Dict], resolved: List[Dict], active: List[Dict],
                                start_date: datetime, end_date: datetime, current_active_count: Optional[int] = None) -> str:
        """Generate monthly report (1st to last day of month)

        Args:
            opened: Incidents opened during the month
            resolved: Incidents resolved during the month
            active: Currently active incidents (as of end of month)
            start_date: Start of month (1st 00:00:00 UTC)
            end_date: End of month (last day 23:59:59 UTC)
            current_active_count: Current number of open incidents (as of report generation time)
        """
        # Use end_date as calculation time for all metrics
        calculation_time = end_date

        # Dates are already in UTC
        start_utc = start_date
        end_utc = end_date

        # Format: "September 2025" or "Sep 2025"
        month_year = end_utc.strftime('%B %Y')

        # Calculate metrics
        active_stats = compute_stats(active)
        opened_total = len(opened)
        resolved_total = len(resolved)

        # Calculate opened+resolved count (incidents with complete lifecycle in this period)
        opened_ids = {inc.get("incidentID") or inc.get("id") for inc in opened}
        opened_and_resolved = [inc for inc in resolved if (inc.get("incidentID") or inc.get("id")) in opened_ids]
        opened_and_resolved_total = len(opened_and_resolved)

        # Calculate both MTTR metrics
        mttr_opened_and_resolved = self.metrics_calc.calculate_mttr(resolved, opened_incidents=opened, start_date=start_date, end_date=end_date)
        mttr_all_resolved = self.metrics_calc.calculate_mttr(resolved)  # Legacy: all resolved incidents

        # Calculate both MTTD metrics
        mttd_opened_and_resolved = self.metrics_calc.calculate_mttd(opened_and_resolved) if opened_and_resolved else None
        mttd_all_resolved = self.metrics_calc.calculate_mttd(resolved)

        oldest_age = self.metrics_calc.calculate_oldest_active_age(active, calculation_time=calculation_time)

        report = []
        report.append("=" * 40)
        report.append("📊 <b>Monthly Incident Report</b>")
        report.append(f"📅 {month_year} (UTC)")
        report.append("=" * 40)
        report.append("")

        # Count critical incidents opened
        critical_opened = sum(1 for inc in opened if (inc.get("severity") or "").lower() == "critical")

        # Calculate carry over and net change
        # Carry over = incidents that existed at start of month
        # Formula: end_active - opened + resolved = start_active
        carry_over = active_stats['total'] - opened_total + resolved_total
        net_change = active_stats['total'] - carry_over

        # Summary section - Option B layout
        report.append("📋 <b>Summary</b>")
        report.append("-" * 40)

        # 📊 Current Status section
        report.append("📊 <b>Current Status</b>")
        if current_active_count is not None:
            report.append(f"• 🔥 Current Open Incidents: {current_active_count}")
        sign = "+" if net_change >= 0 else ""
        report.append(f"• 🔥 Total Active (end of month): {active_stats['total']} ({sign}{net_change} from last month)")

        # Oldest Active - show "-" if no active incidents, otherwise show the calculated value
        if active_stats['total'] == 0:
            report.append(f"• ⏳ Oldest Active: -")
        elif oldest_age is not None:
            if oldest_age < 24:
                report.append(f"• ⏳ Oldest Active: {oldest_age:.1f} hours")
            else:
                report.append(f"• ⏳ Oldest Active: {oldest_age/24:.1f} days")
        else:
            report.append(f"• ⏳ Oldest Active: -")

        report.append(f"• ⏰ Over SLA: {active_stats['over_sla']}")
        report.append(f"• ❌👤 Without Assignee: {active_stats['without_assignee']}")
        report.append("")

        # 📈 Monthly Activity section
        report.append("📈 <b>Monthly Activity</b>")
        report.append(f"• 🔄 Started with: {carry_over} incident{'s' if carry_over != 1 else ''}")
        report.append(f"• 🆕 Opened This Month: {opened_total}")
        report.append(f"  ↳ 🔴 Critical: {critical_opened}")
        report.append(f"• ✅ Resolved This Month: {resolved_total}")
        report.append(f"  ↳ Opened & Resolved in Month: {opened_and_resolved_total}")
        report.append("")

        # ⏱️ Performance Metrics section
        report.append("⏱️ <b>Performance Metrics</b>")

        # MTTR - show only all resolved (always in hours for consistency)
        if resolved_total == 0:
            report.append(f"• MTTR: -")
        else:
            if mttr_all_resolved is not None:
                report.append(f"• MTTR: {mttr_all_resolved:.1f}h")
            else:
                report.append(f"• MTTR: -")

        # MTTD - show only all resolved (always in hours for consistency)
        if resolved_total == 0:
            report.append(f"• MTTD: -")
        else:
            if mttd_all_resolved is not None:
                report.append(f"• MTTD: {mttd_all_resolved:.1f}h")
            else:
                report.append(f"• MTTD: -")

        report.append("")

        # Active incidents section
        sorted_items = sort_active(active)
        top = sorted_items if self.max_active is None else sorted_items[:self.max_active]
        if self.max_active is None:
            report.append("🔥 <b>Active Incidents</b>")
        else:
            report.append(f"🔥 <b>Active Incidents</b> — showing {len(top)} of {len(active)}")
        report.append("-" * 40)
        if not top:
            report.append("  No active incidents")
        else:
            for inc in top:
                report.append(self.format_incident_entry(inc))
        report.append("")

        # Opened this month section
        report.append(f"🔴 <b>Opened This Month</b>: {opened_total}")
        report.append("-" * 40)
        if opened_total > 0:
            for inc in opened:
                report.append(self.format_incident_entry(inc))
        else:
            report.append("  None")
        report.append("")

        # Resolved this month section
        report.append(f"✅ <b>Resolved This Month</b>: {resolved_total}")
        report.append("-" * 40)
        if resolved_total > 0:
            for inc in resolved:
                report.append(self.format_incident_entry(inc))
        else:
            report.append("  None")

        return "\n".join(report)
