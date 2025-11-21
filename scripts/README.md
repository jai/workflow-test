# Scripts

## incident-reporter.py

Incident reporter that fetches incidents from Grafana IRM and sends formatted reports to Google Chat.

### Features
- **Daily Reports**: Reports incidents opened and resolved in the previous day
- **Weekly Reports**: Tuesday-Monday week with metrics (MTTR, oldest active, daily breakdown)
- **Monthly Reports**: Full month reports with comprehensive statistics
- Fetches all active incidents with age breakdown
- Sends formatted card messages to Google Chat webhook
- Supports local testing with custom dates
- Disk caching for performance (with modifiedTime-based invalidation)
- Historical report generation with offset parameters

### Timezone Behavior
- Anchors the reporting window to GMT+7 (Bangkok/Jakarta).
- Displays all human-readable times as GMT+7 and labels sections accordingly.
- Interprets `--date` as a GMT+7 calendar day (00:00–23:59:59 GMT+7).
- Performs calculations and API queries in UTC; only presentation is localized.

### Installation
```bash
pip install requests python-dateutil
```

### Usage

#### Daily Reports
```bash
# Use environment variables
export GRAFANA_TOKEN=<token>
export GRAFANA_URL=https://finnapp.grafana.net
export GOOGLE_CHAT_WEBHOOK_URL=<webhook_url>
python incident-reporter.py

# Or use command line arguments
python incident-reporter.py \
  --token YOUR_TOKEN \
  --url https://finnapp.grafana.net \
  --webhook YOUR_WEBHOOK_URL

# Test specific date
python incident-reporter.py --date 2025-09-08  # Interpreted as a GMT+7 calendar day

# Debug mode
python incident-reporter.py --debug

# Skip Google Chat (local testing only)
python incident-reporter.py --no-chat
```

#### Weekly Reports
```bash
# Generate last week's report (Tuesday-Monday)
python incident-reporter.py --weekly --no-chat

# Generate report for 1 week ago
python incident-reporter.py --weekly --week-offset 1 --no-chat

# Save to Markdown file
python incident-reporter.py --weekly --save-md --no-chat
# Creates: report/REPORT_WEEKLY_2025-10-21_2025-10-27.md
```

#### Monthly Reports
```bash
# Generate last month's report
python incident-reporter.py --monthly --no-chat

# Generate report for 2 months ago
python incident-reporter.py --monthly --month-offset 2 --no-chat

# Save to Markdown file
python incident-reporter.py --monthly --save-md --no-chat
# Creates: report/REPORT_MONTHLY_2025-09.md
```

#### Cache Management
```bash
# View cache statistics
python incident-reporter.py --cache-stats

# Clear cache
python incident-reporter.py --clear-cache

# Disable cache (fetch fresh data)
python incident-reporter.py --no-cache --weekly

# Build cache for entire year
python incident-reporter.py --fetch-all --no-chat
```

#### GitHub Actions
Runs automatically daily at 6 AM GMT+7 (11 PM UTC) via `.github/workflows/daily-incident-report.yml` in the **production** environment.

### Required Environment Variables
- `GRAFANA_TOKEN`: Grafana IRM service account token
- `GRAFANA_URL`: Grafana instance URL (e.g., https://finnapp.grafana.net)
- `GOOGLE_CHAT_WEBHOOK_URL`: Google Chat webhook URL

**Note**: When running via GitHub Actions, these variables are automatically provided from the production environment secrets.

### Report Contents

#### Daily Reports
- **All Active Incidents**: Total count with age distribution
- **Opened Yesterday**: Incidents created in the previous day
- **Resolved Yesterday**: Incidents closed in the previous day
- **Statistics**: Daily metrics and average resolution time

#### Weekly Reports (Tuesday-Monday)
- **Summary Metrics**: Total active, opened, resolved
- **MTTR**: Mean Time To Resolve (in hours/days)
- **Oldest Active**: Age of longest-running incident
- **Daily Breakdown**: Incidents per day for the week
- **Without Assignee / Over SLA**: Key metrics
- **Detailed Lists**: Active, opened, and resolved incidents

#### Monthly Reports
- Same structure as weekly reports but for full calendar month
- All metrics calculated as of end of month

### Documentation

For detailed documentation, see:
- **[INCIDENT_REPORTER.md](INCIDENT_REPORTER.md)** - Complete user guide
- **[OFFSET_OPTIONS.md](OFFSET_OPTIONS.md)** - Week/month offset feature
- **[FILENAME_PATTERN_UPDATE.md](FILENAME_PATTERN_UPDATE.md)** - Report filename format
- **[MISSING_STATS_DISPLAY.md](MISSING_STATS_DISPLAY.md)** - Summary statistics rules
- **[WEEKLY_REPORT_FIXES.md](WEEKLY_REPORT_FIXES.md)** - Bug fixes documentation

## incident_status_quality.py

Collects recently updated incidents plus their most recent human-authored status updates for the Claude status-quality workflow.

### Features
- Filters Grafana IRM incidents by a configurable look-back window (`--window-hours`, default 24h).
- Captures the latest human activity entry per incident (text, author, timestamp, age) and flags when it is missing or outside the window.
- Outputs two JSON artifacts:
  - `incident-status-data.json` — detailed dataset with raw text for auditing.
  - `incident-status-prompt.json` — trimmed payload consumed by Claude in GitHub Actions.
- Respects the existing disk cache (`.cache/incidents`) to minimize API calls.
- Supports optional limits (`--max-incidents`) for local testing/debugging.

### Usage

```bash
export GRAFANA_TOKEN=<token>
export GRAFANA_URL=https://finnapp.grafana.net

# Collect 24h of data (default)
python scripts/incident_status_quality.py

# Use a 6-hour window with limited output paths
python scripts/incident_status_quality.py \
  --window-hours 6 \
  --max-incidents 10 \
  --output-json /tmp/status-data.json \
  --prompt-output /tmp/status-prompt.json

# Disable cache and enable verbose logging
python scripts/incident_status_quality.py --no-cache --debug
```

### Required Environment Variables
- `GRAFANA_TOKEN` or `GRAFANA_SERVICE_ACCOUNT_TOKEN`
- `GRAFANA_URL`

### Outputs
- `incident-status-data.json`: contains metadata + raw status update text for every incident in the window.
- `incident-status-prompt.json`: minimized JSON array used directly inside Claude prompts (includes truncated status text and metadata).

These files are consumed by the scheduled GitHub Action that evaluates the quality of each status update and posts the aggregate result to Google Chat.

When opening a pull request against this repo you can trigger the workflow early by commenting `/run incident-status-quality`, which runs the same job against the current branch.

Notes:
- All Markdown reports are saved to `report/` directory
- Filenames follow pattern: `REPORT_<TYPE>_<DURATION>.md`
- Cache directory: `.cache/incidents/` (automatically managed)
