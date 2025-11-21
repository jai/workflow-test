#!/usr/bin/env python3
import json
import os
import re
from pathlib import Path

exec_file = Path(os.environ["EXECUTION_FILE"])
marker = re.compile(r"STATUS_DECISIONS::(\[.*\])", re.DOTALL)
turns = json.loads(exec_file.read_text())

decisions = None
total_input = 0
total_output = 0
duration_ms = 0
cost = 0.0

for turn in turns:
    if turn.get("type") == "result":
        duration_ms = max(duration_ms, turn.get("duration_ms") or 0)
        cost = max(cost, turn.get("total_cost_usd") or 0.0)
        continue
    if turn.get("type") != "assistant":
        continue
    message = turn.get("message") or {}
    usage = message.get("usage") or {}
    total_input += (
        (usage.get("input_tokens") or 0)
        + (usage.get("cache_creation_input_tokens") or 0)
        + (usage.get("cache_read_input_tokens") or 0)
    )
    total_output += usage.get("output_tokens") or 0
    if decisions is not None:
        continue
    for content in message.get("content", []):
        text = content.get("text")
        if not text:
            continue
        match = marker.search(text)
        if match:
            decisions = json.loads(match.group(1))
            break
if decisions is None:
    raise SystemExit("Claude output missing STATUS_DECISIONS marker.")

fail_count = sum(1 for item in decisions if item.get("overallStatus") == "fail")
pass_count = len(decisions) - fail_count

Path(os.environ["DECISIONS_PATH"]).write_text(json.dumps(decisions, indent=2))

with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as fh:
    fh.write(f"fail_count={fail_count}\n")
    fh.write(f"pass_count={pass_count}\n")
    fh.write(f"decision_file={os.environ['DECISIONS_PATH']}\n")
    fh.write(f"token_input={total_input}\n")
    fh.write(f"token_output={total_output}\n")
    fh.write(f"duration_ms={duration_ms}\n")
    fh.write(f"total_cost_usd={cost}\n")
