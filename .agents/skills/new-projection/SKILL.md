---
name: new-projection
description: Guide for adding new aggregate projections to the internal Sample projects or to any projects consuming the Structur framework. Use this when asked to add new projections to the Samples or Sample projects.
---

To add new aggregate projections to a consuming project, follow this process:

1. Determine the target consuming API project for the new handlers. For example, `Synonms.Structur.Sample.Api`.
2. Determine the pluralised form of the aggregate name to be used as the collection name for the feature. For example, if the aggregate name is "Employee" the collection name would be "Employees".
3. Determine the destination folder for the new projections in the consuming API project as `{ApiProject}/Features/{CollectionName}/Projections`. For example, `Synonms.Structur.Sample.Api/Features/Employees/Projections`.  Create it if it does not exist.  In this folder:
   - Create the required projection for the specified domain event. Use the following guidelines:
     - The projection class should be named using the purpose (e.g. `EmployeeSummary`) and then "Projection", for example `EmployeeSummaryProjection`.
     - The projection class should inherit `Projection<TAggregateRoot>`, for example `Projection<Employee>`.
     - It should be decorated with the `StructurProjectionAttribute` to define the relationship to the Aggregate Root and control the metadata returned from the projections controller as well as how the projection endpoints should be registered, for example `[StructurProjection(typeof(Employee), "summary", "Employee Summary", "A high level summary of the Employee.", allowAnonymous: true)]` links to the `Employee` aggregate and sets up endpoint route using the URL template `/employees/{id}/projections/summary`.
     - Any domain events which influence the state of the projection must handle the projection in the `Replay` method and perform the appropriate mutation.  For example: 
       ```csharp
       public override void Replay(Projection projection)
       {
           if (projection is EmployeeSummaryProjection employeeSummaryProjection)
           {
               employeeSummaryProjection.FullName = Resource.Forename + " " + (string.IsNullOrWhiteSpace(Resource.MiddleNames) ? string.Empty : Resource.MiddleNames + " ") + Resource.Surname;
           }
       }
       ```
