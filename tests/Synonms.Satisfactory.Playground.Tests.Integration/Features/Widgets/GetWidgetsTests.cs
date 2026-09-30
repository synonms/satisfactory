using System.Net.Http.Json;
using Synonms.Satisfactory.Playground.Contract.Features.Widgets;

namespace Synonms.Satisfactory.Playground.Tests.Integration.Features.Widgets;

public class GetWidgetsTests(PlaygroundTestFixture fixture)
{
    [Fact]
    public async Task GetWidgets_ReturnsWidgets()
    {
        // Arrange
        HttpClient httpClient = fixture.HttpClient;

        // Act
        HttpResponseMessage response = await httpClient.GetAsync("/api/widgets", TestContext.Current.CancellationToken);
        response.EnsureSuccessStatusCode();
        List<WidgetResource>? widgets = await response.Content.ReadFromJsonAsync<List<WidgetResource>>(TestContext.Current.CancellationToken);

        // Assert
        Assert.NotNull(widgets);
        Assert.Contains(widgets, widget => widget is { Id: "W00001", Name: "Basic Widget" });
        Assert.Contains(widgets, widget => widget is { Id: "W00002", Name: "Advanced Widget" });
    }
}