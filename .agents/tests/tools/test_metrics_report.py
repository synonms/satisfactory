from tools.work_items.metrics_report import build_metrics_report


def test_metrics_report_excludes_placeholder_runs_and_reports_data_quality() -> None:
    work_items = [
        {
            "id": "00001-1",
            "type": "user-story",
            "status": "done",
            "intake": [
                {
                    "agent": "software-architect",
                    "metrics": {
                        "durationSeconds": 10,
                        "inputTokens": 100,
                        "outputTokens": 50,
                        "totalTokens": 150,
                        "model": "test-model",
                        "estimatedCostUsd": 0.01,
                    },
                }
            ],
            "tasks": [
                {
                    "phase": "implementation",
                    "history": [
                        {
                            "agent": "software-engineer",
                            "iteration": 1,
                            "metrics": {
                                "durationSeconds": 0,
                                "inputTokens": 0,
                                "outputTokens": 0,
                                "totalTokens": 0,
                                "model": "unknown",
                                "estimatedCostUsd": 0,
                            },
                        }
                    ],
                }
            ],
            "execution": {"totals": {"durationSeconds": 10, "totalTokens": 150, "estimatedCostUsd": 0.01}},
        }
    ]

    report = build_metrics_report(work_items)

    assert report["agentRuns"] == 2
    assert report["measured"] == {
        "runs": 1,
        "durationSeconds": 10.0,
        "totalTokens": 150,
        "estimatedCostUsd": 0.01,
    }
    assert report["workItems"][0]["invalidMetricRuns"] == 1
    assert report["invalidRuns"][0]["reason"] == "token counts must be positive integers"