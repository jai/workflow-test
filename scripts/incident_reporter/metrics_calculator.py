"""
Metrics calculator for incident reports

Calculates key metrics:
- MTTR (Mean Time To Resolve)
- MTTD (Mean Time To De-escalation)
- Oldest active incident age
- Daily breakdown
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional


class MetricsCalculator:
    """Calculator for incident metrics"""

    def __init__(self, parse_timestamp_func, disk_cache=None, fetch_last_update_func=None):
        """
        Args:
            parse_timestamp_func: Function to parse timestamp strings to datetime
            disk_cache: Optional DiskCache instance for activity data
            fetch_last_update_func: Optional function to fetch last update (for MTTD)
        """
        self.parse_timestamp = parse_timestamp_func
        self.disk_cache = disk_cache
        self.fetch_last_update = fetch_last_update_func

    def calculate_mttr(self, resolved_incidents: List[Dict], opened_incidents: List[Dict] = None,
                       start_date: datetime = None, end_date: datetime = None) -> Optional[float]:
        """Calculate Mean Time To Resolve in hours

        If opened_incidents, start_date, and end_date are provided, only calculates MTTR
        for incidents that were both opened AND resolved in the same period.
        Otherwise, calculates for all resolved incidents (legacy behavior).
        """
        durations = []

        # If filtering by opened+resolved in period
        if opened_incidents is not None and start_date and end_date:
            # Get IDs of incidents opened in this period
            opened_ids = {inc.get("incidentID") or inc.get("id") for inc in opened_incidents}

            for inc in resolved_incidents:
                incident_id = inc.get("incidentID") or inc.get("id")

                # Only include if also opened in this period
                if incident_id not in opened_ids:
                    continue

                # Try enriched format first, then raw format
                created = inc.get("created_dt")
                if not created:
                    created_str = inc.get("createdAt") or inc.get("createdTime")
                    if created_str:
                        created = self.parse_timestamp(created_str)

                resolved = inc.get("resolved_dt")
                if not resolved:
                    resolved_str = inc.get("resolvedAt") or inc.get("closedTime")
                    if resolved_str:
                        resolved = self.parse_timestamp(resolved_str)

                if created and resolved:
                    duration_hours = (resolved - created).total_seconds() / 3600
                    durations.append(duration_hours)
        else:
            # Legacy behavior: all resolved incidents
            for inc in resolved_incidents:
                # Try enriched format first, then raw format
                created = inc.get("created_dt")
                if not created:
                    created_str = inc.get("createdAt") or inc.get("createdTime")
                    if created_str:
                        created = self.parse_timestamp(created_str)

                resolved = inc.get("resolved_dt")
                if not resolved:
                    resolved_str = inc.get("resolvedAt") or inc.get("closedTime")
                    if resolved_str:
                        resolved = self.parse_timestamp(resolved_str)

                if created and resolved:
                    duration_hours = (resolved - created).total_seconds() / 3600
                    durations.append(duration_hours)

        if not durations:
            return None

        return sum(durations) / len(durations)

    def is_deescalation(self, old_severity: str, new_severity: str) -> bool:
        """Check if severity change is a de-escalation

        De-escalation = Critical/Major → Minor/Low
        """
        if not old_severity or not new_severity:
            return False

        old = old_severity.lower()
        new = new_severity.lower()

        # Critical/Major → Minor/Low is de-escalation
        high_severities = ['critical', 'major']
        low_severities = ['minor', 'low']

        return old in high_severities and new in low_severities

    def find_first_deescalation(self, incident_id: str, created_at: datetime, modified_time: Optional[str] = None) -> Optional[float]:
        """Find time to first de-escalation for an incident

        Uses cached activity items from fetch_last_update() - no separate API call needed

        Returns:
            Hours from creation to first de-escalation, or None if no de-escalation found
        """
        if not self.disk_cache or not self.fetch_last_update:
            return None

        try:
            # Get cached activity data (same cache used by fetch_last_update)
            cached_activity = None
            if self.disk_cache.enabled and modified_time:
                cached_activity = self.disk_cache.get_activity(incident_id, modified_time)

            if cached_activity is None:
                # No cached activity - call fetch_last_update to populate cache
                # This will fetch activity items and cache them
                self.fetch_last_update(incident_id, modified_time)
                # Try to get from cache again
                if self.disk_cache.enabled and modified_time:
                    cached_activity = self.disk_cache.get_activity(incident_id, modified_time)

            if cached_activity is None:
                return None

            # Get activity items from cache
            items = cached_activity.get("activityItems") or []

            # Sort chronologically (oldest first) to find FIRST de-escalation
            items_sorted = sorted(items, key=lambda x: x.get("eventTime") or x.get("createdTime") or "")

            # Look for first severity downgrade
            for item in items_sorted:
                event_type = item.get("eventType") or item.get("activityKind") or ""

                # Check if this is a severity change event
                if "severity" in event_type.lower() or event_type == "incidentFieldsUpdated":
                    # Try to extract old and new severity
                    field_updates = item.get("fieldUpdates") or item.get("updates") or []

                    for update in field_updates:
                        field_name = update.get("fieldName") or update.get("field") or ""
                        if "severity" in field_name.lower():
                            old_severity = update.get("previousValue") or update.get("oldValue")
                            new_severity = update.get("newValue") or update.get("value")

                            if self.is_deescalation(old_severity, new_severity):
                                event_time_str = item.get("eventTime") or item.get("createdTime") or item.get("createdAt")
                                if event_time_str:
                                    event_time = self.parse_timestamp(event_time_str)
                                    deescalation_hours = (event_time - created_at).total_seconds() / 3600
                                    return deescalation_hours

            return None

        except Exception as e:
            # On error, return None
            return None

    def calculate_mttd(self, incidents: List[Dict]) -> Optional[float]:
        """Calculate Mean Time To De-escalation in hours

        De-escalation = First downgrade from Critical/Major to Minor/Low
        """
        deescalation_times = []

        for inc in incidents:
            # Get incident ID and created time
            incident_id = inc.get("incidentID") or inc.get("id")
            if not incident_id:
                continue

            # Get created time
            created = inc.get("created_dt")
            if not created:
                created_str = inc.get("createdAt") or inc.get("createdTime")
                if created_str:
                    created = self.parse_timestamp(created_str)

            if not created:
                continue

            # Get modified time for cache validation
            modified_time = inc.get("modifiedTime") or inc.get("updatedAt")

            # Find first de-escalation
            deescalation_hours = self.find_first_deescalation(str(incident_id), created, modified_time)

            if deescalation_hours is not None:
                deescalation_times.append(deescalation_hours)

        if not deescalation_times:
            return None

        return sum(deescalation_times) / len(deescalation_times)

    def calculate_oldest_active_age(self, active_incidents: List[Dict], calculation_time: Optional[datetime] = None) -> Optional[float]:
        """Calculate age of oldest open incident in hours

        Args:
            active_incidents: List of active incident dictionaries
            calculation_time: Time to calculate age relative to (default: now)
        """
        if not active_incidents:
            return None

        reference_time = calculation_time or datetime.now(timezone.utc)
        oldest_age_hours = 0

        for inc in active_incidents:
            # Try enriched format first, then raw format
            created = inc.get("created_dt")
            if not created:
                created_str = inc.get("createdAt") or inc.get("createdTime")
                if created_str:
                    created = self.parse_timestamp(created_str)

            if created:
                age_hours = (reference_time - created).total_seconds() / 3600
                if age_hours > oldest_age_hours:
                    oldest_age_hours = age_hours

        return oldest_age_hours if oldest_age_hours > 0 else None

    def calculate_daily_breakdown(self, opened_incidents: List[Dict], start_date: datetime, end_date: datetime) -> Dict[str, int]:
        """Calculate incidents per day for the date range (UTC)"""
        daily_counts = {}

        # Initialize all days with 0 (UTC)
        current = start_date.astimezone(timezone.utc)
        end = end_date.astimezone(timezone.utc)
        while current <= end:
            date_key = current.strftime('%Y-%m-%d')
            daily_counts[date_key] = 0
            current += timedelta(days=1)

        # Count incidents per day (UTC)
        for inc in opened_incidents:
            # Try enriched format first (created_dt), then raw format (createdAt/createdTime)
            created = inc.get("created_dt")
            if not created:
                created_str = inc.get("createdAt") or inc.get("createdTime")
                if created_str:
                    created = self.parse_timestamp(created_str)

            if created:
                created_utc = created.astimezone(timezone.utc)
                date_key = created_utc.strftime('%Y-%m-%d')
                if date_key in daily_counts:
                    daily_counts[date_key] += 1

        return daily_counts
