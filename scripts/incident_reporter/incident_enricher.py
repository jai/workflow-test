"""
Incident enrichment module

Handles:
- Fetching incident details and activity
- Enriching incidents with computed fields
- Building complete incident records
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from .incident_stats import is_human_user


class IncidentEnricher:
    """Enriches incidents with additional data and computed fields"""

    def __init__(self, client, disk_cache, parse_timestamp_func, sla_by_severity: Dict[str, int]):
        """
        Args:
            client: GrafanaIRMClient instance
            disk_cache: DiskCache instance
            parse_timestamp_func: Function to parse timestamp strings
            sla_by_severity: Dict mapping severity to SLA days
        """
        self.client = client
        self.disk_cache = disk_cache
        self.parse_timestamp = parse_timestamp_func
        self.sla_by_severity = sla_by_severity
        self._activity_cache: Dict[str, Tuple[Optional[str], Optional[str], Optional[str]]] = {}
        self._incident_detail_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_hits = 0
        self.cache_misses = 0

    def flatten_incident(self, incident: Dict) -> Dict[str, Any]:
        """Flatten nested incident structure"""
        merged: Dict[str, Any] = {}

        def merge(source: Optional[Dict[str, Any]]):
            if source:
                merged.update(source)

        merge(incident.get("incident"))
        merge(incident.get("incidentPreview"))
        merge(incident.get("data"))  # For cached incident details
        merge(incident)

        # Map severityLabel to severity for compatibility
        if "severityLabel" in merged and "severity" not in merged:
            merged["severity"] = merged["severityLabel"]

        return merged

    def get_incident_membership(self, incident: Dict) -> Dict:
        """Extract assignment info from incident"""
        flat = self.flatten_incident(incident)
        members = flat.get("incidentMembership")

        # If no full membership, check for membership preview
        if not members:
            preview = flat.get("incidentMembershipPreview")
            if preview:
                # Convert importantAssignments to the expected format
                important = preview.get("importantAssignments", [])
                if important:
                    members = {"assignments": important}

        if not members:
            members = {}

        assignees = members.get("users") or members.get("assignments") or []
        teams = members.get("teams") or []

        if teams:
            has_assignee = len(teams) > 0
        else:
            has_assignee = any(is_human_user(u.get("user")) for u in assignees)

        # Extract first assignee name for display (like old format)
        assignee_display = None
        for assignment in assignees:
            user = assignment.get("user") or {}
            user_name = user.get("name")
            if user_name and is_human_user(user):
                # Take first word of name (e.g., "Abenezer" from "Abenezer Shiferaw")
                parts = user_name.strip().split()
                assignee_display = parts[0] if parts else user_name.strip()
                break

        return {
            "has_assignee": has_assignee,
            "teams": teams,
            "assignees": assignees,
            "assignee": assignee_display,
        }

    def fetch_last_update(
        self, incident_id: str, modified_time: Optional[str] = None
    ) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """Fetch most recent human activity for an incident

        Returns:
            Tuple of (last_update_time, last_update_kind, last_update_body)
        """
        # Check disk cache first
        cached_activity = None
        if self.disk_cache.enabled and modified_time:
            cached_activity = self.disk_cache.get_activity(incident_id, modified_time)

        if cached_activity is not None:
            self.cache_hits += 1
            return (
                cached_activity.get("last_update_time"),
                cached_activity.get("last_update_kind"),
                cached_activity.get("last_update_body"),
            )

        self.cache_misses += 1

        # Fetch all activity items (with pagination)
        items = self.client.query_activity_all_pages(
            str(incident_id),
            kinds=None,
            limit_per_page=100,
            order_direction="DESC",
        )

        last_update_time = None
        last_update_kind = None
        last_update_body = None

        # Find first human-generated update
        for item in items:
            created_by = item.get("user") or item.get("createdBy") or {}
            if not is_human_user(created_by):
                continue

            activity_kind = item.get("activityKind") or item.get("eventType") or ""
            event_time = item.get("eventTime") or item.get("createdTime")

            if event_time:
                last_update_time = event_time
                last_update_kind = activity_kind
                last_update_body = item.get("body") or item.get("text") or ""
                break

        # Save to disk cache with all activity items
        if self.disk_cache.enabled and modified_time:
            cache_data = {
                "last_update_time": last_update_time,
                "last_update_kind": last_update_kind,
                "last_update_body": last_update_body,
                "activityItems": items,  # Save all items for MTTD
            }
            self.disk_cache.save_activity(incident_id, cache_data, modified_time)

        return last_update_time, last_update_kind, last_update_body

    def fetch_incident_detail(self, incident_id: str, modified_time: Optional[str] = None) -> Dict[str, Any]:
        """Fetch full incident details with caching"""
        # Check disk cache first
        if self.disk_cache.enabled:
            cached_detail = self.disk_cache.get_incident(incident_id, modified_time)
            if cached_detail is not None:
                self.cache_hits += 1
                return cached_detail

        self.cache_misses += 1

        # Fetch from API
        detail = self.client.get_incident(incident_id)

        # Save to disk cache
        if self.disk_cache.enabled and modified_time:
            self.disk_cache.save_incident(incident_id, detail, modified_time)

        return detail

    def build_incident_record(
        self,
        incident: Dict,
        fetch_detail: bool = False,
        fetch_last_update: bool = False,
        use_resolved_time: bool = False,
        calculation_time: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Build a complete incident record with computed fields

        Args:
            incident: Base incident dictionary
            fetch_detail: Whether to fetch full incident details
            fetch_last_update: Whether to fetch last activity update
            use_resolved_time: Use resolved time instead of current time for age calculation
            calculation_time: Specific time to calculate age relative to (default: now)
        """
        flat = self.flatten_incident(incident)
        incident_id = flat.get("incidentID") or flat.get("id")
        modified_time = flat.get("modifiedTime") or flat.get("updatedAt")

        # Fetch detail if requested
        if fetch_detail:
            detail = self.fetch_incident_detail(str(incident_id), modified_time)
            flat = self.flatten_incident(detail)

        # Parse timestamps
        created_str = flat.get("createdAt") or flat.get("createdTime")
        created = self.parse_timestamp(created_str) if created_str else None

        resolved_str = flat.get("resolvedAt") or flat.get("closedTime")
        resolved = self.parse_timestamp(resolved_str) if resolved_str else None

        # Calculate reference time
        if use_resolved_time and resolved:
            ref_time = resolved
        elif calculation_time:
            ref_time = calculation_time
        else:
            ref_time = datetime.now(timezone.utc)

        # Calculate age
        age_hours = 0.0
        age_days = 0.0
        if created:
            age_hours = (ref_time - created).total_seconds() / 3600
            age_days = age_hours / 24

        # Get severity and SLA
        severity = flat.get("severity") or "Pending"
        sla_days = self.sla_by_severity.get(severity, 999)

        # Calculate SLA status
        days_over_sla = age_days - sla_days
        over_sla = days_over_sla >= 0

        # Get membership info
        membership = self.get_incident_membership(incident)

        # Fetch last update if requested
        last_update_time = None
        last_update_kind = None
        last_update_body = None
        if fetch_last_update:
            last_update_time, last_update_kind, last_update_body = self.fetch_last_update(
                str(incident_id), modified_time
            )

        return {
            **flat,
            "incidentID": incident_id,
            "created_dt": created,
            "resolved_dt": resolved,
            "age_hours": age_hours,
            "age_days": age_days,
            "severity": severity,
            "sla_days": sla_days,
            "days_over_sla": days_over_sla,
            "over_sla": over_sla,
            "has_assignee": membership["has_assignee"],
            "assignee": membership["assignee"],
            "teams": membership["teams"],
            "assignees": membership["assignees"],
            "last_update_time": last_update_time,
            "last_update_kind": last_update_kind,
            "last_update_body": last_update_body,
        }

    def fetch_all_active_incidents(self) -> List[Dict]:
        """Fetch all active incidents from API"""
        response = self.client.query_incidents(
            params={
                "status": ["active"],
            },
            fetch_all=True,
        )
        return response.get("incidents", [])

    def enrich_active_incidents(
        self, active: List[Dict], calculation_time: Optional[datetime] = None
    ) -> List[Dict]:
        """Enrich active incidents with computed fields

        Args:
            active: List of active incident dictionaries
            calculation_time: Specific time to calculate age relative to (default: now)
        """
        return [
            self.build_incident_record(
                inc, fetch_detail=False, fetch_last_update=True, calculation_time=calculation_time
            )
            for inc in active
        ]

    def enrich_recent_incidents(
        self,
        incidents: List[Dict],
        use_resolved_time: bool = False,
        calculation_time: Optional[datetime] = None,
    ) -> List[Dict]:
        """Enrich recent incidents (opened/resolved) with computed fields

        Args:
            incidents: List of incident dictionaries
            use_resolved_time: Use resolved time for age calculation
            calculation_time: Specific time to calculate age relative to
        """
        return [
            self.build_incident_record(
                inc,
                fetch_detail=False,
                fetch_last_update=True,
                use_resolved_time=use_resolved_time,
                calculation_time=calculation_time,
            )
            for inc in incidents
        ]
