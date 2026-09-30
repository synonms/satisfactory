using Synonms.Satisfactory.Playground.Contract.Features.Widgets;

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

List<WidgetResource> widgetResources = 
[
    new()
    {
        Id = "W00001",
        Name = "Basic Widget",
        Description = "The entry level widget for the Satisfactory Playground.",
    },
    new()
    {
        Id = "W00002",
        Name = "Advanced Widget",
        Description = "A more capable widget for the Satisfactory Playground.",
    },
];

app.UseCors(uiCorsPolicyName);
app.MapDefaultEndpoints();

app.MapGet("/api", () => "Hello World!");

app.MapGet("/api/widgets", () => widgetResources);

app.MapGet("/api/widgets/{id}", (string id) =>
{
    WidgetResource? widget = widgetResources.FirstOrDefault(w => w.Id == id);
    
    return widget is not null ? Results.Ok(widget) : Results.NotFound();
});

app.Run();