# V∞ Independent Oracle v1

External verification layer for the V∞ Universal AI Security / TEVV stack.

## Trust boundary

This oracle is **external to the model conversation**. It does not share the model's hidden state, chain of thought, or internal runtime. It therefore provides a separate verification process, but it is **not automatically an independent truth oracle**: independence must be established per deployment and evidence path.

## Pipeline

`CLAIM -> EVIDENCE -> PROVENANCE -> CONTRADICTION CHECK -> INVARIANTS -> DECISION`

Fail-closed rules include:

- UNKNOWN / NOT_EXECUTED / BLOCKED_BY_ACCESS_CEILING never become PASS.
- INFERRED never becomes OBSERVED.
- SIMULATION never becomes EXECUTION.
- EXTERNAL never becomes INDEPENDENT.
- AGREEMENT never becomes TRUTH.
- SCORE / COVERAGE never become SECURITY / COMPLETENESS.
- TESTING never becomes PROOF.
- absence of evidence never becomes evidence of absence.

The oracle returns a machine-readable decision and reasons. It never upgrades evidence merely because a claim looks plausible.

## Input

JSON object with `claims` and `evidence` arrays. See `schema.json`.

## Output

`PASS`, `FAIL`, or `BLOCKED`, with explicit reasons and evidence IDs.

`PASS` means only that the supplied claim satisfies the oracle's declared checks; it is not a global security certification.
