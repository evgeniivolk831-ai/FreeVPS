# V∞ External Assurance Harness v1

This layer is an evidence-producing harness, not a proof engine.

## Purpose

Produce machine-readable artifacts for the assurance gaps identified by V∞ × DeepSeek H100:

- runtime/environment attestation
- execution event capture
- observer separation metadata
- oracle/generator trust-domain declarations
- sealed holdout manifest
- evidence hashes and provenance
- evaluator-security test records
- reproducibility/version binding

## Epistemic rules

`INSTANCE_EVIDENCE != SYSTEM_PROPERTY`

`NOT_OBSERVED != ABSENT`

`NOT_EXECUTED != PASS`

`UNKNOWN != PASS`

`EXTERNAL != INDEPENDENT`

The harness must never manufacture execution results. It records what the harness itself can observe and explicitly marks unobserved fields.

## Commands

```bash
python3 v-infinity-assurance-harness/harness.py attest
python3 v-infinity-assurance-harness/harness.py seal-holdout --input holdout.json
python3 v-infinity-assurance-harness/harness.py evidence --input evidence.json
python3 v-infinity-assurance-harness/harness.py self-test
```

Artifacts are JSON and include SHA-256 hashes where applicable.

## Independence

A declared trust domain is metadata, not proof of independence. Independent assurance remains `NOT_VERIFIED` until an external verifier establishes process/data/code/trust-domain separation.
