"""
Incident Reporter - Grafana IRM Incident Reporting Tool

This package provides modular components for generating incident reports from Grafana IRM.
"""

from .cache_manager import DiskCache
from .grafana_client import GrafanaIRMClient, RateLimitHandler
from .metrics_calculator import MetricsCalculator
from .time_helpers import GMT_PLUS_7, get_yesterday_range, get_last_week_range, get_last_month_range, parse_timestamp
from .incident_stats import is_human_user, sort_active, compute_stats
from .incident_enricher import IncidentEnricher
from .report_formatter import ReportFormatter

__all__ = [
    # Cache
    'DiskCache',

    # API Client
    'GrafanaIRMClient',
    'RateLimitHandler',

    # Metrics
    'MetricsCalculator',

    # Time utilities
    'GMT_PLUS_7',
    'get_yesterday_range',
    'get_last_week_range',
    'get_last_month_range',
    'parse_timestamp',

    # Statistics
    'is_human_user',
    'sort_active',
    'compute_stats',

    # Enrichment
    'IncidentEnricher',

    # Reporting
    'ReportFormatter',
]

__version__ = '2.0.0'
