"""
Disk cache manager for incident data

Handles persistent caching of:
- Individual incidents
- Activity data
- Preview lists (global)
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


class DiskCache:
    """Persistent disk cache for incident data"""

    def __init__(self, cache_dir: str = ".cache/incidents", enabled: bool = True, debug: bool = False):
        self.enabled = enabled
        self.debug = debug
        if not self.enabled:
            return

        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get_incident(self, incident_id: str, modified_time: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Retrieve incident from cache if valid"""
        if not self.enabled:
            return None

        cache_file = self.cache_dir / f"{incident_id}.json"

        if not cache_file.exists():
            return None

        try:
            cached = json.loads(cache_file.read_text())

            # If no modified_time provided, return cache (for closed incidents)
            if modified_time is None:
                return cached.get("data")

            # Check if cache is still valid
            cached_modified = cached.get("modifiedTime")
            if cached_modified and cached_modified >= modified_time:
                return cached.get("data")

            return None  # Cache is stale
        except Exception as e:
            print(f"⚠️  Cache read error for incident {incident_id}: {e}")
            return None

    def save_incident(self, incident_id: str, data: Dict[str, Any], modified_time: str):
        """Save incident to cache"""
        if not self.enabled:
            return

        cache_file = self.cache_dir / f"{incident_id}.json"

        cache_entry = {
            "modifiedTime": modified_time,
            "cachedAt": datetime.now(timezone.utc).isoformat(),
            "data": data
        }

        try:
            cache_file.write_text(json.dumps(cache_entry, indent=2))
        except Exception as e:
            print(f"⚠️  Cache write error for incident {incident_id}: {e}")

    def invalidate_incident(self, incident_id: str):
        """Remove incident from cache"""
        if not self.enabled:
            return

        cache_file = self.cache_dir / f"{incident_id}.json"
        if cache_file.exists():
            try:
                cache_file.unlink()
            except Exception as e:
                print(f"⚠️  Cache invalidation error for incident {incident_id}: {e}")

    def clear_cache(self):
        """Clear all cached incidents"""
        if not self.enabled:
            return

        try:
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()
            print("✅ Cache cleared successfully")
        except Exception as e:
            print(f"⚠️  Cache clear error: {e}")

    def get_activity(self, incident_id: str, modified_time: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Retrieve activity data from cache if valid based on modifiedTime"""
        if not self.enabled:
            return None

        cache_file = self.cache_dir / f"{incident_id}_activity.json"

        if not cache_file.exists():
            return None

        try:
            cached = json.loads(cache_file.read_text())

            # If no modified_time provided, return cache (for closed incidents)
            if modified_time is None:
                return cached.get("data")

            # Check if cache is still valid using modifiedTime
            cached_modified = cached.get("modifiedTime")
            if cached_modified and cached_modified >= modified_time:
                return cached.get("data")

            return None  # Cache is stale (incident was modified)
        except Exception as e:
            print(f"⚠️  Activity cache read error for incident {incident_id}: {e}")
            return None

    def save_activity(self, incident_id: str, data: Dict[str, Any], modified_time: str):
        """Save activity data to cache with modifiedTime for validation"""
        if not self.enabled:
            return

        cache_file = self.cache_dir / f"{incident_id}_activity.json"

        cache_entry = {
            "modifiedTime": modified_time,
            "cachedAt": datetime.now(timezone.utc).isoformat(),
            "data": data
        }

        try:
            cache_file.write_text(json.dumps(cache_entry, indent=2))
        except Exception as e:
            if self.debug:
                print(f"⚠️  Cache write error for incident {incident_id}: {e}")

    def get_preview_list(self, ttl_hours: int = 24) -> Optional[List[Dict[str, Any]]]:
        """Retrieve cached preview list (global, not date-specific) with TTL

        Note: QueryIncidentPreviews API doesn't support date filtering.
        It returns ALL incidents, which we then filter by date in code.
        """
        if not self.enabled:
            return None

        # Single global cache file (API doesn't support date filtering anyway)
        cache_file = self.cache_dir / "preview_list_global.json"

        if not cache_file.exists():
            return None

        try:
            cached = json.loads(cache_file.read_text())
            cached_at = cached.get("cachedAt")

            if cached_at:
                # Check TTL
                cached_time = datetime.fromisoformat(cached_at)
                age_hours = (datetime.now(timezone.utc) - cached_time).total_seconds() / 3600

                if age_hours <= ttl_hours:
                    return cached.get("data")

            return None  # Cache expired or invalid
        except Exception as e:
            print(f"⚠️  Preview list cache read error: {e}")
            return None

    def save_preview_list(self, data: List[Dict[str, Any]]):
        """Save preview list to global cache

        Note: QueryIncidentPreviews API doesn't support date filtering.
        We cache all incidents globally and filter by date in code.
        """
        if not self.enabled:
            return

        # Single global cache file
        cache_file = self.cache_dir / "preview_list_global.json"

        cache_entry = {
            "cachedAt": datetime.now(timezone.utc).isoformat(),
            "data": data
        }

        try:
            cache_file.write_text(json.dumps(cache_entry, indent=2))
        except Exception as e:
            print(f"⚠️  Preview list cache write error: {e}")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if not self.enabled:
            return {"enabled": False}

        try:
            incident_files = list(self.cache_dir.glob("*.json"))
            activity_files = [f for f in incident_files if "_activity.json" in f.name]
            preview_list_files = [f for f in incident_files if "preview_list_" in f.name]
            incident_files = [f for f in incident_files if "_activity.json" not in f.name and "preview_list_" not in f.name]

            total_size = sum(f.stat().st_size for f in self.cache_dir.glob("*.json"))

            return {
                "enabled": True,
                "total_cached": len(incident_files),
                "activity_cached": len(activity_files),
                "preview_lists_cached": len(preview_list_files),
                "cache_size_mb": round(total_size / (1024 * 1024), 2),
                "cache_dir": str(self.cache_dir.absolute())
            }
        except Exception as e:
            return {"enabled": True, "error": str(e)}
