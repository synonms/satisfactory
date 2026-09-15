using Synonms.Satisfactory.Playground.AppHost;

IDistributedApplicationBuilder builder = DistributedApplication.CreateBuilder(args);

IResourceBuilder<ProjectResource> api = builder.AddProject<Projects.Synonms_Satisfactory_Playground_Api>(Resources.Api)
    .WithEnvironment("ASPNETCORE_ENVIRONMENT", builder.Environment.EnvironmentName)
    .WithIconName("SettingsCogMultiple");

builder.AddProject<Projects.Synonms_Satisfactory_Playground_Ui>(Resources.Ui)
    .WithReference(api).WaitFor(api)
    .WithIconName("ShareScreenPerson");

builder.Build().Run();
