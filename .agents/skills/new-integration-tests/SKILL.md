---
name: new-integration-tests
description: Guide for adding integration tests for aggregate features in the internal Sample projects or to any projects consuming the Structur framework. Use this when asked to add new integration tests for features, aggregates or CRUD endpoints in the Samples or Sample projects.
---

To add new integration tests to a consuming project, follow this process:

1. Determine the target consuming Integration Tests project for the new tests. For example, `Synonms.Structur.Sample.Tests.Integration`.
2. Determine the pluralised form of the aggregate name to be used as the collection name for the feature. For example, if the aggregate name is "Employee" the collection name would be "Employees".
3. Determine the destination folder for the new tests in the consuming project as `{IntegrationTestProject}/Features/{CollectionName}`. For example, `Synonms.Structur.Sample.Tests.Integration/Features/Employees`.  Create it if it does not exist.  In this folder:
   - Add a Test Feature class.  This class defines how to create/manipulate/persist the required objects and perform assertions, while the Tests class contains the XUnit tests.  Use these guidelines:
     - It should be named using the pluralised name of the feature followed by "TestFeature", for example `EmployeesTestFeature`.
     - It should implement `IGetAllTestFeature<TAggregateRoot, TResource>`, `IGetByIdTestFeature<TAggregateRoot, TResource>`.
     - It should implement `IPostTestFeature<TAggregateRoot, TResource>` and `ICreateFormTestFeature` if create operations are supported.
     - It should implement `IPutTestFeature<TAggregateRoot, TResource>` and `IEditFormTestFeature<TAggregateRoot>` if update operations are supported.
     - It should implement `IDeleteTestFeature<TAggregateRoot>` if delete operations are supported.
   - Add a Tests class.  This class contains the XUnit tests.  Use these guidelines:
     - It should be named using the pluralised name of the feature followed by "Tests", for example `EmployeesTests`.
     - It should contain XUnit tests that use the test feature to perform integration tests against the API endpoints for the new feature, using the relevant fluent builders to assist with the Arrange/Act/Assert steps, for example:
       ```csharp
       [Fact]
       public void GetById_KnownId_Returns200Ok() =>
          GetByIdTest<Employee, EmployeeResource>.Create(fixture, _testFeature)
              .Arrange.WithAggregate()
              .Act
              .Assert.SucceedsWith(HttpStatusCode.OK);
       ```
     
