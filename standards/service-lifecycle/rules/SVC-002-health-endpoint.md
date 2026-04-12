# SVC-002 — Health Endpoint Must Follow Platform Schema

**Domain:** service-lifecycle  
**Version:** 1.0.0  
**Status:** active  
**Severity default:** high

Every service that declares a `healthcheck` path in `services.yml` must
return a JSON response conforming to the platform health schema when that
endpoint is called with an HTTP GET request.

## Required Response Shape

```json
{
  "status": "healthy | degraded | error",
  "version": "<semver or build identifier>",
  "checks": {
    "<component_name>": "ok | error | disabled"
  }
}
```

### Fields

- `status` (required): Overall service health.  Must be one of `healthy`,
  `degraded`, or `error`.
- `version` (required): The service version, typically from `package.json`
  or `pyproject.toml`.
- `checks` (required): A map of named subsystem checks.  Each key is a
  component name (e.g. `database`, `cache`, `opensearch`, `kafka`), each
  value is `ok`, `error`, or `disabled`.

### HTTP Status Codes

- `200` when `status` is `healthy` or `degraded`
- `503` when `status` is `error`

## Signals

- healthcheck endpoint returns non-JSON response
- response missing `status`, `version`, or `checks` field
- `status` value is not one of the three allowed strings
- `checks` values are not one of `ok`, `error`, `disabled`
- healthcheck returns 200 when a critical subsystem check is `error`
- health endpoint path in services.yml does not match the actual route

## Rationale

The estate dashboard polls every service's health endpoint every 15 seconds.
Inconsistent response shapes cause parsing failures, false-positive alerts,
and blind spots in the estate status view.  A standard schema enables
automated monitoring, conformance scoring, and trend analysis across the
entire estate.

## Exceptions

- Services with `auth_exemption` are still required to conform — the health
  schema is independent of authentication.
- Go services in the Recommender mesh may use `/healthz` as the path but must
  still return the standard JSON shape.
