using Synonms.Satisfactory.Playground.Contract.Features.Agents;

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