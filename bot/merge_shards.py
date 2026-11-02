"""Gathers the parts of a check split across machines (bite --shard K/N, one bite_proof/ folder per machine) into
one bite_proof/ for bot/self_check.py: every part's remembered ✅ checks (checked.json), the changes no test noticed from every part's FREE_REPORT.md, numbered
again, and every part's missing_tests/. Prints the short shas of those changes, comma-separated (for --only).
Standard library only.

    python bot/merge_shards.py <folder holding one bite_proof copy per part> [<out folder, default bite_proof>]
"""

import json
import re
import shutil
import sys
from pathlib import Path


def merge(parts: Path, out: Path) -> list:
    memo = {}  # every part's remembered ✅ checks, so next week's parts can skip them
    for f in sorted(parts.rglob("checked.json")):
        try:
            memo.update(json.loads(f.read_text(encoding="utf-8")))
        except ValueError:
            pass
    if memo:
        out.mkdir(parents=True, exist_ok=True)
        (out / "checked.json").write_text(json.dumps(memo, indent=1), encoding="utf-8")
    sections, shas = [], []
    for report in sorted(parts.rglob("FREE_REPORT.md")):
        text = report.read_text(encoding="utf-8")
        for m in re.finditer(r"^## \d+\. ([0-9a-f]{8}) .*?(?=^## \d+\. |\Z)", text, re.M | re.S):
            if m[1] not in shas:
                shas.append(m[1])
                sections.append(m[0].rstrip() + "\n")
        tests = report.parent / "missing_tests"
        if tests.is_dir():
            shutil.copytree(tests, out / "missing_tests", dirs_exist_ok=True)
    if sections:
        out.mkdir(parents=True, exist_ok=True)
        body = [re.sub(r"^## \d+\. ", f"## {i}. ", s, count=1, flags=re.M) for i, s in enumerate(sections, 1)]
        (out / "FREE_REPORT.md").write_text("# Bite: changes no test noticed\n\n" + "\n".join(body), encoding="utf-8")
    return shas


if __name__ == "__main__":
    found = merge(Path(sys.argv[1]), Path(sys.argv[2] if len(sys.argv) > 2 else "bite_proof"))
    print(",".join(found))
