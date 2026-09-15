using System.Net.Http.Json;
using Synonms.Satisfactory.Playground.Contract.Features.Agents;

namespace Synonms.Satisfactory.Playground.Api.Tests.Integration.Features.Agents;

public class AgentsTests(PlaygroundTestFixture fixture)
{
    [Fact]
    public async Task GetAgents_ReturnsAgents()
    {
        // Arrange
        HttpClient httpClient = fixture.HttpClient;

        // Act
        HttpResponseMessage response = await httpClient.GetAsync("/api/agents", TestContext.Current.CancellationToken);
        response.EnsureSuccessStatusCode();
        List<AgentResource>? agents = await response.Content.ReadFromJsonAsync<List<AgentResource>>(TestContext.Current.CancellationToken);

        // Assert
        Assert.NotNull(agents);
        Assert.Contains(agents, agent => agent is { Id: "request-writer", Name: "Request Writer", File: "request-writer.agent.md" });
    }
}