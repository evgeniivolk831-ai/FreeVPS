# V∞ Common-Mode Failure Matrix

## Required trust domains

- MODEL
- TEST_GENERATOR
- ORACLE
- EVALUATOR
- CI
- DATA
- POLICY
- INFRASTRUCTURE

## Required checks

- shared implementation
- shared model
- shared data
- shared generator
- shared policy
- shared infrastructure
- shared credentials
- shared failure modes

## Promotion rule

Any unresolved critical common-mode dependency blocks G8 and prevents FULL_PROMOTION.

## Current state

NOT_EXECUTED_UNTIL_DEPENDENCIES_ARE_INVENTORIED
