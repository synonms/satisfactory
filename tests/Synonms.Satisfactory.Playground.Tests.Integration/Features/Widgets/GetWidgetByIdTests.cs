using System.Net.Http.Json;
using Synonms.Satisfactory.Playground.Contract.Features.Widgets;

namespace Synonms.Satisfactory.Playground.Tests.Integration.Features.Widgets;

public class GetWidgetByIdTests(PlaygroundTestFixture fixture)
{
    [Fact]
    public async Task GetWidgetById_GivenKnownId_ReturnsWidget()
    {
        // Arrange
        HttpClient httpClient = fixture.HttpClient;

        // Act
        HttpResponseMessage response = await httpClient.GetAsync("/api/widgets/W00001", TestContext.Current.CancellationToken);
        response.EnsureSuccessStatusCode();
        WidgetResource? widget = await response.Content.ReadFromJsonAsync<WidgetResource>(TestContext.Current.CancellationToken);

        // Assert
        Assert.NotNull(widget);
        Assert.Equal("W00001", widget.Id);
        Assert.Equal("Basic Widget", widget.Name);
    }
}