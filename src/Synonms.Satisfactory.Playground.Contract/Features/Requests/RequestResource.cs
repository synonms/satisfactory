namespace Synonms.Satisfactory.Playground.Contract.Features.Requests;

public class RequestResource
{
    public class WorkItemIdentifier
    {
        public string Id { get; set; } = string.Empty;
    }
    
    public string Id { get; set; } = string.Empty;
    
    public List<WorkItemIdentifier> WorkItems { get; set; } = [];
}