#!/usr/bin/env python3
import json
import os
from pathlib import Path

data_path = Path(os.environ["INCIDENT_DATA_PATH"])
out_path = Path(os.environ["GITHUB_OUTPUT"])

data = json.loads(data_path.read_text())
count = len(data.get("incidents", []))
print(f"Incidents collected: {count}")
with out_path.open("a", encoding="utf-8") as fh:
    fh.write(f"incident_count={count}\n")
