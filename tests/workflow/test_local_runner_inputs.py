"""Runner-label and routing inputs on the reusable policy check (12cb538 compatibility line).

A caller that routes its CI to local runners passes the selected labels as JSON
(`runner-labels-json`) and its router job's result (`ci-route-result`). Such a
caller runs its policy-check job with `always()` and a local bootstrap runner so
that a routing failure still reaches this workflow: GitHub counts a skipped
required check as passed, so `scp/policy-check` must FAIL, before any checkout or
App-token exchange, whenever routing did not succeed. Callers that pass neither
input keep exactly today's hosted `ubuntu-24.04` behaviour.

On this line five summary and publication steps run on `always()`, one of them an
authenticated SCP checkout with a `github.token` fallback. Each keeps its original
predicate and additionally requires the routing guard to have succeeded, so a
failed route does nothing after the guard, while a routed run that fails its
policy check still builds, validates, uploads and posts its summary.

After a successful route, the job creates its own Python environment in a new directory under
RUNNER_TEMP and puts it first on PATH, and the job requires pip to run inside a virtual
environment, so the hash-pinned installs never touch the runner's system Python.
"""

import json
import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

import yaml

WORKFLOW = Path(__file__).resolve().parents[2] / ".github" / "workflows" / "policy-check.yml"
RUNS_ON = "${{ fromJSON(inputs.runner-labels-json) }}"
GUARD = "Require successful CI host routing"
SETUP = "Create isolated Python environment"
VENV = re.compile(r"scp-policy-check-venv\.[A-Za-z0-9]{8}")
LOCKFILE_INSTALL = 'python3 -m pip install --require-hashes -r "${SCP_RUNTIME_ROOT}/requirements/policy-check.txt" '
# Nothing may reach the system or user site, or switch off managed-environment protection.
BYPASSES = ("--user", "--break-system-packages", "PIP_BREAK_SYSTEM_PACKAGES", "--system-site-packages",
            "EXTERNALLY-MANAGED", "actions/setup-python")
ROUTED = "steps.ci-route.outcome == 'success'"
# Each always() step's predicate as it stands at 12cb538, before the routing conjunct.
ALWAYS_STEPS = {
    "Build policy-check summary": "always()",
    "Check out SCP repo at workflow ref for schema lookup": "always()",
    "Validate policy-check summary schema": "always()",
    "Upload policy-check summary artifact": "always() && steps.validate-summary.outcome == 'success'",
    "Post policy-check read-back commit status":
        "always() && steps.validate-summary.outcome == 'success' && github.event_name == 'pull_request'",
}


def runner_labels(runs_on, labels_json):
    """Evaluate the runs-on expression as GitHub does: fromJSON of the input, nothing else."""
    match = re.fullmatch(r"\$\{\{ fromJSON\(inputs\.runner-labels-json\) \}\}", runs_on)
    assert match, runs_on
    return json.loads(labels_json)


def predicate(expression, values):
    """Evaluate the `&&`/`==` subset these step predicates use; always() is true."""
    expression = re.sub(r"\b(?:steps\.[\w-]+\.outcome|github\.event_name)\b",
                        lambda match: repr(values[match[0]]), expression)
    expression = expression.replace("always()", "True").replace("&&", " and ")
    return eval(expression, {"__builtins__": {}})  # noqa: S307


class LocalRunnerInputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workflow = yaml.safe_load(WORKFLOW.read_text())
        cls.inputs = cls.workflow["on"]["workflow_call"]["inputs"]  # the workflow quotes "on"
        cls.jobs = cls.workflow["jobs"]
        cls.steps = cls.jobs["policy-check"]["steps"]

    def test_inputs_are_optional_and_default_to_todays_hosted_runner(self):
        labels = self.inputs["runner-labels-json"]
        self.assertEqual((labels["type"], labels["required"], labels["default"]), ("string", False, '"ubuntu-24.04"'))
        route = self.inputs["ci-route-result"]
        self.assertEqual((route["type"], route["required"], route["default"]), ("string", False, "success"))

    def test_both_jobs_run_on_the_labels_and_keep_their_names(self):
        self.assertEqual(set(self.jobs), {"policy-check", "attest-scorecard"})
        self.assertEqual(self.jobs["policy-check"]["name"], "scp/policy-check")
        self.assertEqual(self.jobs["attest-scorecard"]["name"], "scp/attest-scorecard")
        self.assertEqual(self.jobs["attest-scorecard"]["needs"], "policy-check")
        self.assertEqual(self.jobs["attest-scorecard"]["if"], "inputs.scorecard-emit")
        for name in self.jobs:
            with self.subTest(job=name):
                self.assertEqual(self.jobs[name]["runs-on"], RUNS_ON)

    def test_default_and_local_labels_resolve_and_malformed_json_does_not_fall_back(self):
        runs_on = self.jobs["policy-check"]["runs-on"]
        self.assertEqual(runner_labels(runs_on, self.inputs["runner-labels-json"]["default"]), "ubuntu-24.04")
        for labels in (["self-hosted", "ci-dell-pim-s"], ["self-hosted", "ci-pim-s"]):
            with self.subTest(labels=labels):
                self.assertEqual(runner_labels(runs_on, json.dumps(labels)), labels)
        for malformed in ('["self-hosted", "ci-dell-pim-s"', "ubuntu-24.04", ""):
            with self.subTest(malformed=malformed), self.assertRaises(ValueError):
                runner_labels(runs_on, malformed)

    def test_the_route_guard_is_the_first_step_before_checkout_and_tokens(self):
        guard = self.steps[0]
        self.assertEqual((guard["name"], guard["id"]), (GUARD, "ci-route"))
        self.assertNotIn("if", guard)
        self.assertNotIn("continue-on-error", guard)
        self.assertEqual(guard["env"], {"SCP_CI_ROUTE_RESULT": "${{ inputs.ci-route-result }}"})
        self.assertNotIn("${{", guard["run"])  # the value reaches the shell only as an environment variable
        self.assertEqual(self.steps[1]["name"], SETUP)  # local only, before any checkout or token
        self.assertEqual(self.steps[2]["name"], "Checkout caller repository")
        self.assertIn("actions/create-github-app-token", json.dumps(self.steps[1:]))

    def test_the_route_guard_fails_unless_routing_succeeded(self):
        for result in ("success", "failure", "cancelled", "skipped", ""):
            with self.subTest(result=result):
                run = subprocess.run(
                    ["bash", "--noprofile", "--norc", "-c", self.steps[0]["run"]],
                    env={"PATH": "/usr/bin:/bin", "SCP_CI_ROUTE_RESULT": result},
                    capture_output=True, text=True,
                )
                if result == "success":
                    self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
                else:
                    self.assertNotEqual(run.returncode, 0)
                    self.assertIn("CI host routing did not succeed", run.stdout)

    def test_every_always_step_keeps_its_predicate_and_requires_the_route(self):
        found = {step["name"]: step["if"] for step in self.steps if "always()" in str(step.get("if", ""))}
        self.assertEqual(set(found), set(ALWAYS_STEPS))
        for name, original in ALWAYS_STEPS.items():
            with self.subTest(step=name):
                self.assertEqual(found[name], f"{original} && {ROUTED}")
        # No other step can run after a failed guard: none uses failure() or cancelled().
        self.assertNotRegex(json.dumps([step.get("if", "") for step in self.steps]), r"failure\(\)|cancelled\(\)")
        schema = next(step for step in self.steps if step["name"] == "Check out SCP repo at workflow ref for schema lookup")
        self.assertEqual(schema["with"]["token"], "${{ steps.scp-app-token.outputs.token || github.token }}")

    def test_a_failed_route_runs_none_of_them_and_a_routed_failed_policy_still_publishes(self):
        for name, original in ALWAYS_STEPS.items():
            for summary, event in (("success", "pull_request"), ("failure", "pull_request"), ("success", "push")):
                values = {"steps.validate-summary.outcome": summary, "github.event_name": event}
                with self.subTest(step=name, summary=summary, event=event):
                    guarded = f"{original} && {ROUTED}"
                    self.assertFalse(predicate(guarded, {**values, "steps.ci-route.outcome": "failure"}))
                    # Routed: exactly the original behaviour, whatever the policy outcome.
                    self.assertEqual(predicate(guarded, {**values, "steps.ci-route.outcome": "success"}),
                                     predicate(original, values))

    def bootstrap(self, runner_temp, github_path, path=None):
        """Run the workflow's own setup script with only the variables a runner provides."""
        env = {"PATH": path or os.environ["PATH"], "GITHUB_PATH": str(github_path),
               "PIP_REQUIRE_VIRTUALENV": self.jobs["policy-check"]["env"]["PIP_REQUIRE_VIRTUALENV"]}
        if runner_temp is not None:
            env["RUNNER_TEMP"] = str(runner_temp)
        return subprocess.run(["bash", "--noprofile", "--norc", "-c", self.steps[1]["run"]],
                              env=env, capture_output=True, text=True)

    def test_the_environment_is_created_after_the_guard_and_before_any_python_or_token(self):
        setup = self.steps[1]
        self.assertEqual((setup["name"], setup["id"], setup["shell"]), (SETUP, "python-venv", "bash"))
        self.assertNotIn("if", setup)  # runs only after the guard succeeded
        self.assertNotIn("continue-on-error", setup)
        self.assertNotIn("env", setup)
        self.assertNotIn("${{", setup["run"])
        token = [index for index, step in enumerate(self.steps)
                 if str(step.get("uses", "")).startswith("actions/create-github-app-token")]
        self.assertTrue(token)
        self.assertGreater(min(token), 1)
        python_steps = [index for index, step in enumerate(self.steps) if "python3" in str(step.get("run", ""))]
        self.assertEqual(min(python_steps), 1)  # the setup step itself is the first to use Python

    def test_every_pip_install_in_the_job_requires_a_virtual_environment(self):
        self.assertEqual(self.jobs["policy-check"]["env"]["PIP_REQUIRE_VIRTUALENV"], "true")
        for step in self.steps:
            with self.subTest(step=step.get("name")):
                self.assertNotIn("PIP_REQUIRE_VIRTUALENV", json.dumps(step))  # no step relaxes it
        self.assertEqual(WORKFLOW.read_text().count("PIP_REQUIRE_VIRTUALENV"), 1)

    def test_the_bootstrap_creates_a_new_isolated_environment_first_on_github_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp).resolve()
            created = []
            for attempt in range(2):  # the same RUNNER_TEMP twice: each run owns a new directory
                github_path = tmp / f"github_path_{attempt}"
                github_path.write_text("")
                run = self.bootstrap(tmp, github_path)
                self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
                (entry,) = github_path.read_text().splitlines()
                venv = Path(entry).parent
                self.assertEqual((venv.parent, Path(entry).name), (tmp, "bin"))
                self.assertRegex(venv.name, VENV)
                created.append(venv)
            self.assertNotEqual(created[0], created[1])
            for venv in created:  # neither run deleted or reused the other's environment
                self.assertIn("include-system-site-packages = false", (venv / "pyvenv.cfg").read_text())
            venv = created[1]
            # A later step's `python3`, with the GITHUB_PATH entry first on PATH, is the environment's.
            probe = subprocess.run(
                ["bash", "--noprofile", "--norc", "-c",
                 "python3 -c 'import json, site, sys; print(json.dumps([sys.prefix, sys.base_prefix, site.ENABLE_USER_SITE]))'"],
                env={"PATH": f"{venv / 'bin'}:{os.environ['PATH']}"}, capture_output=True, text=True,
            )
            self.assertEqual(probe.returncode, 0, probe.stderr)
            prefix, base_prefix, user_site = json.loads(probe.stdout)
            self.assertEqual(Path(prefix).resolve(), venv)
            self.assertNotEqual(Path(base_prefix).resolve(), venv)
            self.assertFalse(user_site)

    def test_a_malformed_bootstrap_fails_without_publishing_a_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            not_a_directory = tmp / "file"
            not_a_directory.write_text("")
            broken = tmp / "broken-bin"
            broken.mkdir()
            (broken / "python3").write_text("#!/bin/sh\nexit 1\n")
            (broken / "python3").chmod(0o755)
            runner_temp = tmp / "temp"
            runner_temp.mkdir()
            cases = {
                "RUNNER_TEMP unset": (None, None),
                "RUNNER_TEMP is a file": (not_a_directory, None),
                "python3 cannot create it": (runner_temp, f"{broken}:/usr/bin:/bin"),
            }
            for name, (runner_temp, path) in cases.items():
                with self.subTest(name):
                    github_path = tmp / "github_path"
                    github_path.write_text("")
                    run = self.bootstrap(runner_temp, github_path, path)
                    self.assertNotEqual(run.returncode, 0)
                    self.assertEqual(github_path.read_text(), "")
                    self.assertIn("unable to create the isolated Python environment", run.stdout)

    def test_every_install_is_hash_pinned_into_the_environment_without_bypasses(self):
        installs = [(index, step) for index, step in enumerate(self.steps) if "pip install" in str(step.get("run", ""))]
        self.assertEqual(len(installs), 3)
        for index, step in installs:
            with self.subTest(step=step["name"]):
                self.assertGreater(index, 1)
                lines = [line.strip() for line in step["run"].splitlines() if "pip install" in line]
                self.assertEqual(len(lines), 1)
                self.assertTrue(lines[0].startswith(LOCKFILE_INSTALL), lines[0])
                self.assertIn('jsonschema.__version__ == "4.23.0"', step["run"])
        self.assertIn('yaml.__version__ == "6.0.2"', installs[0][1]["run"])
        text = WORKFLOW.read_text()
        for bypass in BYPASSES:
            with self.subTest(bypass=bypass):
                self.assertNotIn(bypass, text)


if __name__ == "__main__":
    unittest.main()
