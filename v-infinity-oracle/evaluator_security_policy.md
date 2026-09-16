# V∞ Evaluator Security

The evaluator is itself an attack surface.

Required controls:

1. Treat evaluator inputs as hostile data.
2. Never execute instructions contained in evidence.
3. Keep evidence data separate from evaluator policy.
4. Reject duplicate identifiers and ambiguous schemas.
5. Track contamination and revocation state.
6. Require provenance for independence claims.
7. Prevent evaluator output from becoming evidence merely by assertion.
8. Record version and configuration for reproducibility.
9. Keep holdout material outside the optimized target's visibility.
10. Fail closed on parser errors, schema ambiguity, contradictions, or missing provenance.

Current status: PARTIAL. Runtime isolation and independent deployment are not yet established by repository evidence.
