using Microsoft.AspNetCore.Components.Web;
using Microsoft.AspNetCore.Components.WebAssembly.Hosting;
using Synonms.CarbonBlazor.Infrastructure.IoC;
using Synonms.Satisfactory.Playground.Ui;

WebAssemblyHostBuilder builder = WebAssemblyHostBuilder.CreateDefault(args);
builder.RootComponents.Add<App>("#app");
builder.RootComponents.Add<HeadOutlet>("head::after");

// Aspire Service Discovery doesn't work with Blazor WASM 
const string apiUrl = "https://localhost:7021";

builder.Services.AddScoped(_ => new HttpClient
{
    BaseAddress = new Uri(apiUrl)
});

builder.Services.AddCarbonBlazor();

await builder.Build().RunAsync();