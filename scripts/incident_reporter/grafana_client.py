"""
Grafana IRM API client

Handles all communication with Grafana IRM API including:
- Rate limiting and retries
- Incident queries with pagination
- Activity queries with pagination
- Preview list queries with caching
"""

import time
from typing import Any, Callable, Dict, List, Optional

import requests


class RateLimitHandler:
    """Handles rate limiting with exponential backoff"""

    def __init__(self, max_retries: int = 3, base_delay: float = 1.0):
        self.max_retries = max_retries
        self.base_delay = base_delay

    def execute_with_retry(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with exponential backoff on rate limit"""
        for attempt in range(self.max_retries):
            try:
                response = func(*args, **kwargs)
                return response
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429:  # Rate limited
                    retry_after = e.response.headers.get('Retry-After')
                    if retry_after:
                        delay = int(retry_after)
                    else:
                        delay = self.base_delay * (2 ** attempt)  # Exponential backoff

                    if attempt < self.max_retries - 1:
                        print(f"⚠️  Rate limited. Retrying in {delay}s... (attempt {attempt + 1}/{self.max_retries})")
                        time.sleep(delay)
                        continue
                raise
            except requests.exceptions.RequestException as e:
                # For network errors, also retry
                if attempt < self.max_retries - 1:
                    delay = self.base_delay * (2 ** attempt)
                    print(f"⚠️  Request failed: {e}. Retrying in {delay}s... (attempt {attempt + 1}/{self.max_retries})")
                    time.sleep(delay)
                    continue
                raise
        raise Exception(f"Failed after {self.max_retries} retries")


class GrafanaIRMClient:
    """Client for interacting with Grafana IRM API"""

    def __init__(self, instance_url: str, token: str, rate_limit_handler: Optional[RateLimitHandler] = None, debug: bool = False):
        self.instance_url = instance_url.rstrip('/')
        self.token = token
        self.api_base = f"{self.instance_url}/api/plugins/grafana-irm-app/resources/api/v1"
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
        self.rate_limiter = rate_limit_handler or RateLimitHandler()
        self.debug = debug
        self.api_call_count = 0

    def _post(self, path: str, payload: Dict) -> Dict:
        """Execute POST request with rate limiting and timing"""

        def _do_request():
            url = f"{self.api_base}/{path}"

            if self.debug:
                self.api_call_count += 1
                start_time = time.time()
                print(f"🔵 API Call #{self.api_call_count}: {path}")

            resp = requests.post(url, headers=self.headers, json=payload, timeout=30)
            resp.raise_for_status()
            result = resp.json()

            if self.debug:
                elapsed = time.time() - start_time
                print(f"✅ API Call #{self.api_call_count}: {path} completed in {elapsed:.2f}s")

            return result

        return self.rate_limiter.execute_with_retry(_do_request)

    def query_incidents(self, params: Dict = None, fetch_all: bool = True) -> Dict:
        """Query incidents with optional pagination support

        Args:
            params: Query parameters
            fetch_all: If True, automatically fetch all pages

        Returns:
            Dict with 'incidents' key containing all results
        """
        default_params = {
            "query": {
                "limit": 100,
                "orderDirection": "DESC",
                "orderBy": "createdAt",
            }
        }
        if params:
            default_params["query"].update(params)

        if not fetch_all:
            return self._post("IncidentsService.QueryIncidents", default_params)

        # Fetch all pages using cursor-based pagination
        all_incidents = []
        page_count = 0

        while True:
            response = self._post("IncidentsService.QueryIncidents", default_params)
            incidents = response.get("incidents", [])
            all_incidents.extend(incidents)
            page_count += 1

            # Check cursor for next page
            cursor = response.get("cursor", {})
            has_more = cursor.get("hasMore", False)
            next_value = cursor.get("nextValue")

            if not has_more or not next_value:
                break

            # Add cursor to request for next page
            default_params["cursor"] = {
                "nextValue": next_value
            }

        if page_count > 1:
            print(f"📄 Fetched {len(all_incidents)} incidents across {page_count} pages")

        return {"incidents": all_incidents}

    def query_incident_previews(self, params: Dict = None, fetch_all: bool = True, disk_cache=None, cache_ttl_hours: int = 24, include_membership: bool = False) -> Dict:
        """Query incident previews with optional pagination support and caching

        Args:
            params: Query parameters (must include dateFrom and dateTo for caching)
            fetch_all: If True, automatically fetch all pages
            disk_cache: Optional DiskCache instance for preview list caching
            cache_ttl_hours: Cache TTL in hours (default: 24)
            include_membership: If True, include membership preview data

        Returns:
            Dict with 'incidentPreviews' key containing all results
        """
        default_params = {
            "query": {
                "limit": 100,
                "orderDirection": "DESC",
                "orderBy": "createdAt",
            },
            "includeMembershipPreview": include_membership,
        }
        if params:
            default_params["query"].update(params)

        if not fetch_all:
            return self._post("IncidentsService.QueryIncidentPreviews", default_params)

        # Check global cache (API doesn't support date filtering)
        if disk_cache:
            cached_previews = disk_cache.get_preview_list(ttl_hours=cache_ttl_hours)
            if cached_previews is not None:
                if self.debug:
                    print(f"✅ Using cached preview list (global cache, {len(cached_previews)} incidents)")
                return {"incidentPreviews": cached_previews}

        # Fetch all pages using cursor-based pagination
        all_previews = []
        page_count = 0

        while True:
            response = self._post("IncidentsService.QueryIncidentPreviews", default_params)
            previews = response.get("incidentPreviews") or response.get("previews", [])
            all_previews.extend(previews)
            page_count += 1

            # Check cursor for next page
            cursor = response.get("cursor", {})
            has_more = cursor.get("hasMore", False)
            next_value = cursor.get("nextValue")

            if not has_more or not next_value:
                break

            # Add cursor to request for next page
            default_params["cursor"] = {
                "nextValue": next_value
            }

        if page_count > 1 and self.debug:
            print(f"📄 Fetched {len(all_previews)} incident previews across {page_count} pages (global, will filter by date in code)")

        # Save to global cache
        if disk_cache and len(all_previews) > 0:
            disk_cache.save_preview_list(all_previews)
            if self.debug:
                print(f"💾 Cached {len(all_previews)} incident previews to global cache")

        return {"incidentPreviews": all_previews}

    def query_activity(self, incident_id: str, kinds: Optional[List[str]] = None, limit: int = 1,
                        order_direction: str = "DESC", cursor: Optional[str] = None) -> Dict:
        """Query activity with optional pagination cursor"""
        query = {
            "incidentID": incident_id,
            "limit": limit,
            "orderDirection": order_direction,
        }
        if kinds:
            query["activityKind"] = kinds
        if cursor:
            query["cursor"] = cursor
        return self._post("ActivityService.QueryActivity", {"query": query})

    def query_activity_all_pages(self, incident_id: str, kinds: Optional[List[str]] = None,
                                  limit_per_page: int = 100, order_direction: str = "DESC") -> List[Dict]:
        """Fetch all activity items across all pages (similar to query_incident_previews pagination)

        Returns:
            List of all activity items from all pages combined
        """
        all_items = []
        cursor = None
        page_count = 0

        while True:
            page_count += 1
            resp = self.query_activity(
                incident_id=incident_id,
                kinds=kinds,
                limit=limit_per_page,
                order_direction=order_direction,
                cursor=cursor
            )

            items = (
                resp.get("activityItems")
                or resp.get("items")
                or resp.get("activities")
                or []
            )
            all_items.extend(items)

            # Check for more pages
            cursor_info = resp.get("cursor") or {}
            has_more = cursor_info.get("hasMore", False)
            next_value = cursor_info.get("nextValue")

            if not has_more or not next_value:
                break

            cursor = next_value

        if page_count > 1 and self.debug:
            print(f"📄 Fetched {len(all_items)} activity items across {page_count} pages for incident {incident_id}")

        return all_items

    def get_incident(self, incident_id: str) -> Dict:
        """Get full incident details by ID"""
        return self._post("IncidentsService.GetIncident", {"incidentID": incident_id})
