# Documentation Workflow

This workflow handles documentation work items.

## Flow 3: documentation

```mermaid
stateDiagram-v2
    [*] --> documentation
    documentation --> validation : documentation written
    validation --> documentation : Failed AND attempts < max
    validation --> ready_for_user : Passed
    validation --> blocked : Blocked OR attempts >= max
    ready_for_user --> done : human approval
    ready_for_user --> documentation : unmet existing requirement
```

No specification, no automated tests, no chunks. The validator checks the documentation change against the `triage` work item.