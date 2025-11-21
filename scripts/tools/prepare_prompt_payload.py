#!/usr/bin/env python3
import os
from pathlib import Path

payload = Path(os.environ["INCIDENT_PROMPT_PATH"]).read_text()
output = Path(os.environ["GITHUB_OUTPUT"])
with output.open("a", encoding="utf-8") as fh:
    fh.write("payload<<__PROMPT_JSON__\n")
    fh.write(payload)
    if not payload.endswith("\n"):
        fh.write("\n")
    fh.write("__PROMPT_JSON__\n")
