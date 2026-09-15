IDistributedApplicationBuilder builder = DistributedApplication.CreateBuilder(args);

IResourceBuilder<ProjectResource> api = builder.AddProject<Projects.Synonms_Satisfactory_Playground_Api>("synonms-satisfactory-playground-api")
    .WithEnvironment("ASPNETCORE_ENVIRONMENT", builder.Environment.EnvironmentName)
    .WithIconName("SettingsCogMultiple");

builder.AddProject<Projects.Synonms_Satisfactory_Playground_Ui>("synonms-satisfactory-playground-ui")
    .WithReference(api).WaitFor(api)
    .WithIconName("ShareScreenPerson");

builder.Build().Run();
