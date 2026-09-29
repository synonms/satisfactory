using System.Text.Json;
using Microsoft.AspNetCore.Mvc;
using Synonms.Satisfactory.Playground.Contract.Features.Agents;
using Synonms.Satisfactory.Playground.Contract.Features.Requests;

WebApplicationBuilder builder = WebApplication.CreateBuilder(args);

builder.AddServiceDefaults();

const string uiCorsPolicyName = "Ui";
const string uiUrl = "https://localhost:7121";

builder.Services.AddCors(options =>
{
    options.AddPolicy(uiCorsPolicyName, policy =>
    {
        policy.WithOrigins(uiUrl)
            .AllowAnyHeader()
            .AllowAnyMethod();
    });
});

WebApplication app = builder.Build();

app.UseCors(uiCorsPolicyName);
app.MapDefaultEndpoints();

app.MapGet("/api", () => "Hello World!");

app.MapGet("/api/requests", () =>
{
    List<RequestResource> requestResources = Directory.EnumerateDirectories(@"c:\Git\Synonms.Satisfactory\.agents\board")
        .Select(directory => new RequestResource
        {
            Id = Path.GetRelativePath(@"c:\Git\Synonms.Satisfactory\.agents\board", directory),
            WorkItems = Directory.EnumerateFiles(directory, "*.work-item.json")
                .Select(file => new RequestResource.WorkItemIdentifier
                {
                    Id = Path.GetFileName(file).Replace(".work-item.json", "")
                })
                .ToList()
        })
        .ToList();
    
    return requestResources;
});

app.MapGet("/api/requests/{id}", ([FromRoute] string id) =>
{
    if (!Path.Exists(@"c:\Git\Synonms.Satisfactory\.agents\board\" + id))
    {
        return Results.NotFound();
    }

    return Results.Ok(new RequestResource
    {
        Id = id,
        WorkItems = Directory.EnumerateFiles(@"c:\Git\Synonms.Satisfactory\.agents\board\" + id, "*.work-item.json")
            .Select(file => new RequestResource.WorkItemIdentifier
            {
                Id = Path.GetFileName(file).Replace(".work-item.json", "")
            })
            .ToList()
    });
}).Produces<RequestResource>();

app.MapGet("/api/requests/{requestId}/work-items/{workItemId}", async ([FromRoute] string requestId, [FromRoute] string workItemId, CancellationToken cancellationToken = default) =>
{
    string filePath = Path.Combine(@"c:\Git\Synonms.Satisfactory\.agents\board\", requestId, workItemId + ".work-item.json");
    
    if (!File.Exists(filePath))
    {
        return Results.NotFound();
    }
    
    string json = await File.ReadAllTextAsync(filePath, cancellationToken);
    
    WorkItemResource? workItem = JsonSerializer.Deserialize<WorkItemResource>(json, new JsonSerializerOptions
    {
        PropertyNameCaseInsensitive = true
    });

    return Results.Ok(workItem);
}).Produces<WorkItemResource>();


app.MapGet("/api/agents", () =>
{
    List<AgentResource> agentResources = 
    [
        new()
        {
            Id = "request-writer",
            Name = "Request Writer",
            File = "request-writer.agent.md"
        }
    ];
    
    return agentResources;
});

app.Run();