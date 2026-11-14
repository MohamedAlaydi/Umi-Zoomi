# Implementation task

## Goal
Verify the hackathon software environment and build a reproducible health-check for officially supported tooling.

## Scope
- Inspect the local project structure and installed documentation.
- Check for a configured Nebius CLI and report its version/path if accessible.
- Confirm that the credentials environment variable is set WITHOUT opening or printing the credentials.
- Verify that a safe, targeted model list or schema query is available; do not request the entire model catalog.
- Create or update a short setup README and a non-secret run ledger for job IDs and outputs.
- Add or run basic unit/smoke tests where feasible.

## Constraints
- Do not generate or modify antibody candidates in this first task.
- Do not submit computational jobs without explicit user authorisation.
- Keep credentials private and excluded from Git.
- Document unmet dependencies precisely.

## Done when
- Setup and basic checks are reproducible.
- `handoff/last_result.md` contains commands run, outcomes and file changes.
