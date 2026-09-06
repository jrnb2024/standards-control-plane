"""Unit test for the conftest target list in `scp_policy_check_run` (lib/policy_check_invocation.sh).

Companion to `test_prepare_manifest_targets.py`, which closed the same class one layer up. In adopter
mode the changed-files manifest comes from `git diff --name-only BASE..HEAD`, which INCLUDES deletions.
The manifest-target step skips a DELETED manifest; the conftest target loop did not, because it selected
purely on file extension. A PR that deleted a `.yaml` / `.json` / `.toml` therefore handed conftest a
path that is not in the checkout, and conftest failed the whole gate:

    Error: running test: parse files: get file info: stat <deleted>.yaml: no such file or directory
    ::error ...SCP-E002::Conftest invocation failed while loading the policy bundle or evaluating the
    changed-file set

Live repro: jrnb2024/adaptive-label #53, deleting `src/adaptive_label_context/` (a package retired on a
product ruling), whose `rules/context_dimensions.yaml` was the file conftest could not stat. That PR is
red on a REQUIRED context for a change whose only fault is that it deletes something.

A deleted file has no surface to evaluate, so it is skipped. The positive case is kept so the skip can
never over-broaden into "evaluate nothing".

Stdlib only (no pytest dependency) so CI runs it with `python <thisfile>`, matching the sibling test;
still pytest-collectable locally.
"""

from __future__ import annotations

import hashlib
import os
import subprocess
import sys
import tempfile
from pathlib import Path

LIB = Path(__file__).resolve().parents[2] / "lib" / "policy_check_invocation.sh"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _run_target_selection(tmp: Path) -> list[str]:
    """Drive `scp_policy_check_run` with fake binaries and return the argv conftest was given."""
    binp = tmp / "bin"
    binp.mkdir()
    argv_log = tmp / "argv.txt"
    conftest = binp / "conftest"
    conftest.write_text(
        "#!/usr/bin/env bash\n"
        f'printf "%s\\n" "$@" >> "{argv_log}"\n'
        'printf "[]\\n"\n'
    )
    opa = binp / "opa"
    opa.write_text("#!/usr/bin/env bash\nexit 0\n")
    for f in (conftest, opa):
        f.chmod(0o755)

    (tmp / "policies").mkdir()
    # `scp_policy_check_run` returns early when the policy dir holds no rego; one no-op rule
    # is enough to reach the target loop, which is what this test is about.
    (tmp / "policies" / "noop.rego").write_text("package main\n\ndeny contains msg if {\n  false\n  msg := \"\"\n}\n")
    (tmp / "output" / "findings").mkdir(parents=True)
    (tmp / "kept.yaml").write_text("kept: true\n")
    # `gone.yaml` is deliberately NOT created: it is the file the PR deleted.
    (tmp / "changed-files.txt").write_text("kept.yaml\ngone.yaml\n")

    env = dict(os.environ)
    env.update(
        {
            "PATH": f"{binp}:{env['PATH']}",
            "SCP_CHANGED_FILES_PATH": "changed-files.txt",
            "SCP_POLICY_CHECK_OUTPUT_DIR": "output/findings",
            "SCP_POLICY_CHECK_POLICY_ROOT": "policies",
            "SCP_POLICY_CHECK_CONFTEST_BIN": str(conftest),
            "SCP_POLICY_CHECK_CONFTEST_SHA256": _sha256(conftest),
            "SCP_POLICY_CHECK_OPA_BIN": str(opa),
            "SCP_POLICY_CHECK_OPA_SHA256": _sha256(opa),
            "SCP_WAIVERS_PATH": "output/findings/waivers.json",
            "SCP_RULE_CONFIG_PATH": ".scp/rule-config.yaml",
        }
    )
    subprocess.run(
        ["bash", "-c", f'source "{LIB}"; scp_policy_check_run'],
        cwd=tmp,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    return argv_log.read_text().splitlines() if argv_log.exists() else []


def test_a_file_deleted_in_the_change_set_is_not_handed_to_conftest() -> None:
    with tempfile.TemporaryDirectory() as raw:
        argv = _run_target_selection(Path(raw))
    assert argv, "conftest was never invoked; the fixture no longer reaches the target loop"
    assert "gone.yaml" not in argv, (
        "a file deleted in the PR was passed to conftest; it will fail with "
        "'stat gone.yaml: no such file or directory' and take the required gate with it"
    )


def test_a_file_that_still_exists_is_still_evaluated() -> None:
    with tempfile.TemporaryDirectory() as raw:
        argv = _run_target_selection(Path(raw))
    assert "kept.yaml" in argv, "the skip over-broadened: a present, parseable file stopped being evaluated"


if __name__ == "__main__":
    failures = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"PASS {name}")
            except AssertionError as exc:
                failures += 1
                print(f"FAIL {name}: {exc}")
    sys.exit(1 if failures else 0)
