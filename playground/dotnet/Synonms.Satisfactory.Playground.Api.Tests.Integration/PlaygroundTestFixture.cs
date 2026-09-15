using Aspire.Hosting.Testing;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Synonms.Satisfactory.Playground.AppHost;

[assembly: AssemblyFixture(typeof(Synonms.Satisfactory.Playground.Api.Tests.Integration.PlaygroundTestFixture))]

namespace Synonms.Satisfactory.Playground.Api.Tests.Integration;

public class PlaygroundTestFixture : IAsyncLifetime
{
    public HttpClient HttpClient { get; private set; } = null!;
    public IServiceScopeFactory ServiceScopeFactory { get; private set; } = null!;
    protected PlaygroundDistributedApplicationFactory? AppHost;
    protected ServiceProvider? ServiceProvider;
    
    public async ValueTask InitializeAsync()
    {
        TestContext.Current.TestOutputHelper?.WriteLine("PlaygroundTestFixture.InitializeAsync");
        
        await StartServicesAsync(TimeSpan.FromMinutes(1));
        await WaitForHealthyResourcesAsync([Resources.Api], TimeSpan.FromSeconds(30));
        await SetupServiceProvider();
    }
    
    protected async Task StartServicesAsync(TimeSpan timeout)
    {
        using CancellationTokenSource cancellationTokenSource = new(timeout);

        try
        {
            AppHost = new PlaygroundDistributedApplicationFactory();
            
            await AppHost.StartAsync(cancellationTokenSource.Token);
        }
        catch (Exception exception)
        {
            TestContext.Current.SendDiagnosticMessage("ERROR: Exception occurred starting Aspire AppHost: {0}", exception);
            throw new Exception("Failed to start Aspire AppHost", exception);
        }

        if (AppHost.Application is null)
        {
            TestContext.Current.SendDiagnosticMessage("ERROR: Aspire AppHost started but DistributedApplication is not initialised.");
            throw new NullReferenceException("DistributedApplication not initialised");
        }
    }
    
    public async ValueTask DisposeAsync()
    {
        if (AppHost is not null)
        {
            await AppHost.DisposeAsync();
        }

        if (ServiceProvider is not null)
        {
            await ServiceProvider.DisposeAsync();
        }
    }
    
    private async Task WaitForHealthyResourcesAsync(IEnumerable<string> resourceNames, TimeSpan timeout)
    {
        using CancellationTokenSource cancellationTokenSource = new(timeout);
        
        Task[] waitTasks = resourceNames.Select(resourceName => WaitForResourceAsync(resourceName, cancellationTokenSource.Token)).ToArray();

        await Task.WhenAll(waitTasks);
    }

    private async Task WaitForResourceAsync(string aspireResourceName, CancellationToken cancellationToken)
    {
        if (AppHost?.Application is null)
        {
            throw new NullReferenceException("AppHost Application not initialised");
        }

        try
        {
            await AppHost.Application.ResourceNotifications.WaitForResourceHealthyAsync(aspireResourceName, cancellationToken);

            TestContext.Current.SendDiagnosticMessage("SUCCESS: Resource '{0}' healthy", aspireResourceName);
        }
        catch (Exception exception)
        {
            TestContext.Current.SendDiagnosticMessage("ERROR: Exception occurred waiting for resource '{0}': {1}", aspireResourceName, exception);
            throw new Exception($"Failure waiting for resource '{aspireResourceName}'", exception);
        }
    }
    
    private async Task SetupServiceProvider()
    {
        if (AppHost?.Application is null)
        {
            throw new NullReferenceException("AppHost Application not initialised");
        }

        HostApplicationBuilderSettings settings = new()
        {
            EnvironmentName = PlaygroundDistributedApplicationFactory.EnvironmentName
        };
        HostApplicationBuilder host = new(settings);
        
        ServiceProvider = host.Services.BuildServiceProvider();
        HttpClient = AppHost.Application.CreateHttpClient(Resources.Api);
        ServiceScopeFactory = ServiceProvider.GetRequiredService<IServiceScopeFactory>();
    }
}