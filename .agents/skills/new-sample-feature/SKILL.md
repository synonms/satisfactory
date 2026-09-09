---
name: new-sample-feature
description: Guide for adding new features (or aggregates) to the internal Sample projects or to any projects consuming the Structur framework. Use this when asked to add new features, aggregates or CRUD endpoints to the Samples or Sample projects.
---

Consider the following skills when adding new features to a consuming project:
 - /new-aggregate-root - for adding new aggregate roots.
 - /new-aggregate-member - for adding new aggregate members.
 - /new-value-object - for adding new value objects.
 - /new-domain-event-handlers - for adding new in-process domain event handlers.
 - /new-projection - for adding new aggregate projections.
 - /new-integration-tests - for adding integration tests for the new feature.

To add new features to the Sample projects, follow this process:

1. Determine the aggregate name (singular) and collection name (plural) for the new feature. For example, if you are adding an "Employee" feature, the aggregate name would be "Employee" and the collection name (used for the URL root path) would be "employees".
2. Determine the target consuming API project and Client API project for the new feature. For example, `Synonms.Structur.Sample.Api` and `Synonms.Structur.Sample.ClientApi` respectively.
3. If it does not already exist, create a destination folder for the new feature in the consuming Client API project as `{ClientApiProject}/Features/{CollectionName}`. For example, `Synonms.Structur.Sample.ClientApi/Features/Employees`.  This will contain the shared backend/frontend code.  In this folder:
   - Create any client resources as required by the feature.
4. If it does not already exist, create a destination folder for the new feature in the consuming API project as `{ApiProject}/Features/{CollectionName}`. For example, `Synonms.Structur.Sample.Api/Features/Employees`.  This will contain the backend code.  In this folder:
   - Create any Value Objects and Aggregate Members along with the Aggregate Root as required by the feature. 
   - Create any domain events, event handlers and projections as required to support the feature.
5. If it does not already exist, create a destination folder for the new feature integration tests in the consuming Integration Test project as `{IntegrationTestProject}/Features/{CollectionName}`. For example, `Synonms.Structur.Sample.Tests.Integration/Features/Employees`.  This will contain the integration test code.  In this folder:
   - Create any integration tests as required by the feature.
