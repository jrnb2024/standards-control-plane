"""Runner-label and routing inputs on the reusable policy check.

A caller that routes its CI to local runners passes the selected labels as JSON
(`runner-labels-json`) and its router job's result (`ci-route-result`). Such a
caller runs its policy-check job with `always()` and a local bootstrap runner so
that a routing failure still reaches this workflow: GitHub counts a skipped
required check as passed, so `scp/policy-check` must FAIL, before any checkout or
App-token exchange, whenever routing did not succeed. Callers that pass neither
input keep exactly today's hosted `ubuntu-24.04` behaviour.
"""

import json
import re
import subprocess
import unittest
from pathlib import Path

import yaml

WORKFLOW = Path(__file__).resolve().parents[2] / ".github" / "workflows" / "policy-check.yml"
RUNS_ON = "${{ fromJSON(inputs.runner-labels-json) }}"
GUARD = "Require successful CI host routing"


def runner_labels(runs_on, labels_json):
    """Evaluate the runs-on expression as GitHub does: fromJSON of the input, nothing else."""
    match = re.fullmatch(r"\$\{\{ fromJSON\(inputs\.runner-labels-json\) \}\}", runs_on)
    assert match, runs_on
    return json.loads(labels_json)


class LocalRunnerInputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workflow = yaml.safe_load(WORKFLOW.read_text())
        cls.inputs = cls.workflow["on"]["workflow_call"]["inputs"]  # the workflow quotes "on"
        cls.jobs = cls.workflow["jobs"]

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
        steps = self.jobs["policy-check"]["steps"]
        guard = steps[0]
        self.assertEqual(guard["name"], GUARD)
        self.assertNotIn("if", guard)
        self.assertNotIn("continue-on-error", guard)
        self.assertEqual(guard["env"], {"SCP_CI_ROUTE_RESULT": "${{ inputs.ci-route-result }}"})
        self.assertNotIn("${{", guard["run"])  # the value reaches the shell only as an environment variable
        self.assertEqual(steps[1]["name"], "Checkout caller repository")
        later = json.dumps(steps[1:])
        self.assertIn("actions/create-github-app-token", later)  # tokens are only minted after the guard

    def test_the_route_guard_fails_unless_routing_succeeded(self):
        guard = self.jobs["policy-check"]["steps"][0]
        for result in ("success", "failure", "cancelled", "skipped", ""):
            with self.subTest(result=result):
                run = subprocess.run(
                    ["bash", "--noprofile", "--norc", "-c", guard["run"]],
                    env={"PATH": "/usr/bin:/bin", "SCP_CI_ROUTE_RESULT": result},
                    capture_output=True, text=True,
                )
                if result == "success":
                    self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
                else:
                    self.assertNotEqual(run.returncode, 0)
                    self.assertIn("CI host routing did not succeed", run.stdout)


if __name__ == "__main__":
    unittest.main()
