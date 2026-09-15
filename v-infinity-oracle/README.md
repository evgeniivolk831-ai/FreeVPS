# V∞ O1 Deterministic Oracle

External, deterministic verification layer for the V∞ Universal AI Security / TEVV stack.

## Trust boundary

O1 runs outside the model conversation and does not access hidden model state, weights, or private runtime. That separation is useful, but **separation alone does not establish G2 independence**. A claim requiring independence must provide evidence from a distinct trust domain; `same_repo`, `same_process`, and `same_model` are explicitly insufficient.

Therefore:

- O1 = external deterministic verifier.
- O1 != automatic proof of truth.
- O1 != automatic G2 independent oracle.
- Missing independence => `BLOCKED`.

## Pipeline

`CLAIM -> EVIDENCE -> PROVENANCE -> CONTRADICTION CHECK -> STATE INVARIANTS -> DECISION`

## Hard fail-closed rules

- `UNKNOWN`, `NOT_EXECUTED`, `BLOCKED_BY_ACCESS_CEILING` never become `PASS`.
- `INFERRED` never becomes `OBSERVED`.
- `SIMULATION` never becomes `EXECUTION`.
- `EXTERNAL` never becomes `INDEPENDENT`.
- `AGREEMENT` never becomes `TRUTH`.
- `SCORE` / `COVERAGE` never become `SECURITY` / `COMPLETENESS`.
- `CORRELATION` never becomes `CAUSATION`.
- `AUTONOMY` never becomes `SELF-CERTIFICATION`.
- `TESTING` never becomes `PROOF`.
- absence of evidence never becomes evidence of absence.
- revoked or contaminated evidence cannot promote a claim.
- contradictions cannot promote a claim.
- duplicate IDs, malformed documents, and invalid states block promotion.

## Regression suite

`test_oracle.py` covers clean PASS, terminal-state blocking, insufficient independence, distinct trust-domain independence, contradiction blocking, and duplicate evidence IDs. GitHub Actions compiles the implementation and runs the regression suite plus positive/fail-closed controls.

## Input / output

Input is a JSON object with `claims` and `evidence` arrays; see `schema.json`.

Output is machine-readable with `PASS` or `BLOCKED` decisions and explicit reasons. `PASS` means only that the supplied claim satisfied O1's declared checks; it is **not** a global security certification.

## Remaining assurance ceiling

O1 cannot by itself close G2, G6, G7, G8, G9, or G11. Those require additional trust domains, holdouts, evaluator-security evidence, common-mode analysis, environment integrity, and/or human or independently operated verification.
