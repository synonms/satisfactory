# Bug Fix Workflow

This workflow handles bug fixes.

## Flow 2: bug

Entry point is QA, not the architect.

```mermaid
stateDiagram-v2
    [*] --> bug_repro_test
    bug_repro_test --> bug_fix : failing repro test written
    bug_repro_test --> blocked : cannot reproduce
    bug_fix --> chunk_testing
    chunk_testing --> bug_fix : tests failed AND attempts < max
    chunk_testing --> validation : tests passed
    chunk_testing --> blocked : attempts >= max OR no progress
    validation --> bug_fix : Failed
    validation --> ready_for_user : Passed
    validation --> blocked : Blocked OR attempts >= max
    ready_for_user --> done : human approval
    ready_for_user --> bug_fix : unmet existing requirement
```

The driver creates a single synthetic chunk in `state.json` whose `technology` matches the affected stack, so chunk-scoped artifact paths and counters behave identically to flow 1.

When the defect cannot be reproduced by an automated test, QA records the reason in `testlog.1.md` and the driver moves straight to `bug-fix` with `reproTestAvailable: false` recorded in the chunk. Validation then relies on inspection and manual evidence, and must say so.