namespace Synonms.Satisfactory.Playground.Contract.Features.Requests;

public class WorkItemResource
{
    public class WorkItemAcceptanceCriteria
    {
        public required string Id { get; set; }
        public required string Description { get; set; }
    }

    public class IntakeActivityResource
    {
        public required DateTime Ts { get; set; }
        public required string Agent { get; set; }
        public required string Result { get; set; }
        public required MetricsResource Metrics { get; set; }
    }

    public class ExecutionResource
    {
        public class BudgetResource
        {
            public required int MaxTaskAttempts { get; set; }
            public required int MaxReviewLoops { get; set; }
            public required int MaxValidationLoops { get; set; }
            public required int MaxTotalAgentRuns { get; set; }
            public required int ReviewLoops { get; set; }
            public required int ValidationLoops { get; set; }
            public required int TotalAgentRuns { get; set; }
        }
        
        public class TotalsResource
        {
            public required decimal DurationSeconds { get; set; }
            public required int TotalTokens { get; set; }
            public required decimal EstimatedCostUsd { get; set; }
        }
        
        public class EscalationResource
        {
            public required DateTime Ts { get; set; }
            public string? TaskId { get; set; }
            public required string Requirement { get; set; }
            public required string Evidence { get; set; }
            public required int Attempts { get; set; }
            public required string RecommendedAction { get; set; }
        }
        
        public string? Branch { get; set; }
        
        public required BudgetResource Budget { get; set; }

        public required TotalsResource Totals { get; set; }
        
        public required List<EscalationResource> Escalations { get; set; }
    }
    
    public class SpecificationResource
    {
        public required string WorkItemId { get; set; }
        public required DateTime Created { get; set; }
        public required string Status { get; set; }
        public required string Summary { get; set; }
        public required string ArchitecturalSummary { get; set; }
        public List<string>? KeyDesignDecisions { get; set; }
        public List<string>? ApiContracts { get; set; }
        public List<string>? DatabaseSchema { get; set; }
        public List<string>? UiComponents { get; set; }
        public List<string>? CrossTaskIntegrationPoints { get; set; }
        public List<string>? OpenQuestionsAndRisks { get; set; }
    }

    public class TaskResource
    {
        public class TaskActivityResource
        {
            public required DateTime Ts { get; set; }
            public required int Iteration { get; set; }
            public required string Agent { get; set; }
            public string? Technology { get; set; }
            public required string Outcome { get; set; }
            public required string Result { get; set; }
            public string? Artifact { get; set; }
            public required List<string> FilesChanged { get; set; }
            public string? RemediationTargetTaskId { get; set; }
            public required MetricsResource Metrics { get; set; }
        }
        
        public required string Id { get; set; }
        public required string Phase { get; set; }
        public required string Owner { get; set; }
        public required string Scope { get; set; }
        public List<string>? Deliverables { get; set; }
        public List<string>? Verification { get; set; }
        public string? Technology { get; set; }
        public List<string>? AffectedPaths { get; set; }
        public List<string>? Contracts { get; set; }
        public List<string>? Dependencies { get; set; }
        public required List<string> AcceptanceCriteriaCovered { get; set; }
        public required string State { get; set; }
        public required int Attempts { get; set; }
        public string? LastFailureSignature { get; set; }
        public string? PreviousFailureSignature { get; set; }
        public string? LatestArtifact { get; set; }
        public string? RemediationTargetTaskId { get; set; }
        public string? BlockedReason { get; set; }
        public List<TaskActivityResource> History { get; set; } = [];
    }

    public class MetricsResource
    {
        public required decimal DurationSeconds { get; set; }
        public required int InputTokens { get; set; }
        public required int OutputTokens { get; set; }
        public required int TotalTokens { get; set; }
        public required string Model { get; set; }
        public required decimal EstimatedCostUsd { get; set; }
    }
    
    public required string Id { get; set; }
    
    public required string Type { get; set; }
    
    public required DateTime Created { get; set; }
    
    public required string Status { get; set; }
    
    public required string Request { get; set; }
    
    public string? Source { get; set; }
    
    public required string Description { get; set; }
    
    public required List<TaskResource> Tasks { get; set; }
    
    public required string PlanStatus { get; set; }
    
    public List<IntakeActivityResource>? Intake { get; set; }
    
    public required ExecutionResource Execution { get; set; }
    
    public List<WorkItemAcceptanceCriteria>? AcceptanceCriteria { get; set; }
    
    public string? StepsToReproduce { get; set; }
    
    public string? ExpectedResult { get; set; }
    
    public string? ActualResult { get; set; }
    
    public string? Content { get; set; }
    
    public SpecificationResource? Specification { get; set; }
}
