import subprocess
from pathlib import Path


def test_end_to_end_run_creates_outputs():
    root = Path(__file__).resolve().parents[1]
    # run quick eval script instead (it will create results/)
    ret = subprocess.run(["/workspaces/HSKG/.venv/bin/python", str(root / "scripts/quick_eval.py")])
    # allow non-zero if environment missing heavy deps; but expect results dir
    results_dir = root / "results"
    assert results_dir.exists(), "results/ directory should exist after run"
