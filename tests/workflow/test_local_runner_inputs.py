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
        self.assertEqual(self.steps[1]["name"], "Checkout caller repository")
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


if __name__ == "__main__":
    unittest.main()
