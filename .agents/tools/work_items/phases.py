"""Authoritative ADLC phase contract: owners, per-phase states, and outcome transitions."""

from __future__ import annotations

from .models import TaskOutcome, TaskPhase, TaskState

PHASE_OWNER: dict[TaskPhase, str] = {
    TaskPhase.BUG_REPRO: "quality-assurance-engineer",
    TaskPhase.IMPLEMENTATION: "software-engineer",
    TaskPhase.UNIT_TEST: "quality-assurance-engineer",
    TaskPhase.INTEGRATION_TEST: "quality-assurance-engineer",
    TaskPhase.REVIEW: "reviewer",
    TaskPhase.VALIDATION: "implementation-validator",
    TaskPhase.DOCUMENTATION: "documentation-writer",
}

_TEST_STATES = frozenset(
    {
        TaskState.NOT_STARTED,
        TaskState.IN_PROGRESS,
        TaskState.TESTS_PASSING,
        TaskState.TESTS_FAILING,
        TaskState.BLOCKED,
    }
)

PHASE_STATES: dict[TaskPhase, frozenset[TaskState]] = {
    TaskPhase.BUG_REPRO: _TEST_STATES,
    TaskPhase.UNIT_TEST: _TEST_STATES,
    TaskPhase.INTEGRATION_TEST: _TEST_STATES,
    TaskPhase.IMPLEMENTATION: frozenset(
        {
            TaskState.NOT_STARTED,
            TaskState.IN_PROGRESS,
            TaskState.IMPLEMENTED,
            TaskState.REWORK_REQUIRED,
            TaskState.BLOCKED,
        }
    ),
    TaskPhase.DOCUMENTATION: frozenset(
        {
            TaskState.NOT_STARTED,
            TaskState.IN_PROGRESS,
            TaskState.DOCUMENTED,
            TaskState.REWORK_REQUIRED,
            TaskState.BLOCKED,
        }
    ),
    TaskPhase.REVIEW: frozenset(
        {
            TaskState.NOT_STARTED,
            TaskState.IN_PROGRESS,
            TaskState.APPROVED,
            TaskState.CHANGES_REQUESTED,
            TaskState.BLOCKED,
        }
    ),
    TaskPhase.VALIDATION: frozenset(
        {
            TaskState.NOT_STARTED,
            TaskState.IN_PROGRESS,
            TaskState.VALIDATED,
            TaskState.REJECTED,
            TaskState.BLOCKED,
        }
    ),
}

_TEST_OUTCOMES = {
    TaskOutcome.PASSED: TaskState.TESTS_PASSING,
    TaskOutcome.FAILED: TaskState.TESTS_FAILING,
    TaskOutcome.BLOCKED: TaskState.BLOCKED,
}

PHASE_OUTCOMES: dict[TaskPhase, dict[TaskOutcome, TaskState]] = {
    TaskPhase.BUG_REPRO: _TEST_OUTCOMES,
    TaskPhase.UNIT_TEST: _TEST_OUTCOMES,
    TaskPhase.INTEGRATION_TEST: _TEST_OUTCOMES,
    TaskPhase.IMPLEMENTATION: {
        TaskOutcome.IMPLEMENTED: TaskState.IMPLEMENTED,
        TaskOutcome.BLOCKED: TaskState.BLOCKED,
    },
    TaskPhase.DOCUMENTATION: {
        TaskOutcome.DOCUMENTED: TaskState.DOCUMENTED,
        TaskOutcome.BLOCKED: TaskState.BLOCKED,
    },
    TaskPhase.REVIEW: {
        TaskOutcome.APPROVED: TaskState.APPROVED,
        TaskOutcome.CHANGES_REQUESTED: TaskState.CHANGES_REQUESTED,
        TaskOutcome.BLOCKED: TaskState.BLOCKED,
    },
    TaskPhase.VALIDATION: {
        TaskOutcome.VALIDATED: TaskState.VALIDATED,
        TaskOutcome.REJECTED: TaskState.REJECTED,
        TaskOutcome.BLOCKED: TaskState.BLOCKED,
    },
}

TERMINAL_SUCCESS_STATES = frozenset(
    {
        TaskState.IMPLEMENTED,
        TaskState.TESTS_PASSING,
        TaskState.APPROVED,
        TaskState.VALIDATED,
        TaskState.DOCUMENTED,
    }
)

# States a task is put back into when a reviewer or validator sends it back for rework.
REWORK_STATE: dict[TaskPhase, TaskState] = {
    TaskPhase.BUG_REPRO: TaskState.TESTS_FAILING,
    TaskPhase.UNIT_TEST: TaskState.TESTS_FAILING,
    TaskPhase.INTEGRATION_TEST: TaskState.TESTS_FAILING,
    TaskPhase.IMPLEMENTATION: TaskState.REWORK_REQUIRED,
    TaskPhase.DOCUMENTATION: TaskState.REWORK_REQUIRED,
    TaskPhase.REVIEW: TaskState.NOT_STARTED,
    TaskPhase.VALIDATION: TaskState.NOT_STARTED,
}

REMEDIATION_OUTCOMES = frozenset({TaskOutcome.CHANGES_REQUESTED, TaskOutcome.REJECTED})


def owner_for(phase: TaskPhase) -> str:
    return PHASE_OWNER[phase]


def allowed_states(phase: TaskPhase) -> frozenset[TaskState]:
    return PHASE_STATES[phase]


def allowed_outcomes(phase: TaskPhase) -> frozenset[TaskOutcome]:
    return frozenset(PHASE_OUTCOMES[phase])


def state_for_outcome(phase: TaskPhase, outcome: TaskOutcome) -> TaskState | None:
    return PHASE_OUTCOMES[phase].get(outcome)


def is_terminal_success(state: TaskState) -> bool:
    return state in TERMINAL_SUCCESS_STATES
