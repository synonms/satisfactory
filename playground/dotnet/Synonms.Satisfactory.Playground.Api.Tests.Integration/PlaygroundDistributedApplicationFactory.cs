using Aspire.Hosting;
using Aspire.Hosting.Testing;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
using Synonms.Satisfactory.Playground.AppHost;

namespace Synonms.Satisfactory.Playground.Api.Tests.Integration;

public class PlaygroundDistributedApplicationFactory() : DistributedApplicationFactory(typeof(PlaygroundAppHostProject))
{
    public DistributedApplication? Application { get; private set; }
    public const string EnvironmentName = "IntegrationTest";
    
    protected override void OnBuilderCreating(DistributedApplicationOptions applicationOptions, HostApplicationBuilderSettings hostOptions)
    {
        hostOptions.Configuration ??= new ConfigurationManager();
        hostOptions.Configuration["environment"] = EnvironmentName;
        
        applicationOptions.DisableDashboard = true;
    }
    
    protected override void OnBuilderCreated(DistributedApplicationBuilder applicationBuilder)
    {
        applicationBuilder.Services.ConfigureHttpClientDefaults(clientBuilder =>
        {
        });
        
        applicationBuilder.Services.AddLogging(loggingBuilder =>
        {
            loggingBuilder.AddFilter(applicationBuilder.Environment.ApplicationName, LogLevel.Debug);
            loggingBuilder.AddProvider(new TestContextLoggerProvider());
        });
    }
    
    protected override void OnBuilt(DistributedApplication application)
    {
        Application = application;
    }
    
    private sealed class TestContextLoggerProvider : ILoggerProvider
    {
        public ILogger CreateLogger(string categoryName) => new TestContextLogger(categoryName);
        public void Dispose() { }
    }

    private sealed class TestContextLogger(string categoryName) : ILogger
    {
        public IDisposable? BeginScope<TState>(TState state) where TState : notnull => null;
        public bool IsEnabled(LogLevel logLevel) => true;

        public void Log<TState>(LogLevel logLevel, EventId eventId, TState state, Exception? exception, Func<TState, Exception?, string> formatter)
        {
            if (!IsEnabled(logLevel)) return;

            string message = $"[{logLevel}] {categoryName}: {formatter(state, exception)}";

            if (exception is not null)
            {
                message += $"\n{exception}";
            }

            TestContext.Current.SendDiagnosticMessage(message);
        }
    }
}