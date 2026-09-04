from pathlib import Path
import subprocess

path = Path("backend/tests/integration/test_endpoint_matrix.py")
base = subprocess.run(
    ["git", "show", f"origin/main:{path.as_posix()}"],
    check=True,
    capture_output=True,
    text=True,
).stdout
marker = '    Endpoint("GET", "/api/v1/spaces/{spaceId}"),\n'
addition = '    Endpoint("POST", "/api/v1/spaces/{spaceId}/membership/leave"),\n'
if base.count(marker) != 1:
    raise SystemExit(f"Expected one Space endpoint marker, found {base.count(marker)}")
if addition in base:
    raise SystemExit("Self-leave endpoint is already present on main")
path.write_text(base.replace(marker, marker + addition, 1), encoding="utf-8")
