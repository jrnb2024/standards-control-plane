# Confidence Taxonomy — 2026-04-12

## Purpose

This note defines the shared confidence and evidence vocabulary used by the
Standards Control Plane before the inference-heavier advisory domains land.

## Confidence thresholds

- `high`: `confidence >= 0.95`
- `medium`: `0.80 <= confidence < 0.95`
- `low`: `confidence < 0.80`

The numeric score remains the source of truth. `confidence_class` is a derived
label for inspection, filtering, and later warning logic.

## Evidence classes

- `direct_file`: evidence taken directly from a concrete repo file that carries
  the cited marker or path
- `declared_metadata`: evidence derived from declared scope metadata such as
  `area_id`, enhancement-spec placement, or audit scope fields
- `structured_review`: evidence drawn from structured review metadata carried in
  review markdown
- `historical_review`: evidence drawn from a historical review reference rather
  than the current area files
- `derived_heuristic`: evidence that points to an inferred signal that is not a
  single direct repo marker

## Guidance

- prefer `direct_file` when the source path itself contains the cited marker
- use `declared_metadata` for boundary, area, or planning artefact alignment
  checks
- use `structured_review` only when a current finding directly cites parsed
  review metadata
- use `historical_review` for advisory references from prior review material
- reserve `derived_heuristic` for weaker or composite signals
