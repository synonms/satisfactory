---
name: new-domain-event-handlers
description: Guide for adding new in-process domain event handlers to the internal Sample projects or to any projects consuming the Structur framework. Use this when asked to add new domain event handlers to the Samples or Sample projects.
---

To add new domain event handlers to a consuming project, follow this process:

1. Determine the target consuming API project for the new handlers. For example, `Synonms.Structur.Sample.Api`.
2. Determine the pluralised form of the aggregate name to be used as the collection name for the feature. For example, if the aggregate name is "Employee" the collection name would be "Employees".
3. Determine the destination folder for the new handlers in the consuming API project as `{ApiProject}/Features/{CollectionName}/Handlers`. For example, `Synonms.Structur.Sample.Api/Features/Employees/Handlers`.  Create it if it does not exist.  In this folder:
   - Create the required domain event handler for the specified domain event. Use the following guidelines:
     - The handler class should be named using the purpose (e.g. `SendEmail`) and then the name of the event being handled (e.g. `ProductCreatedEvent`) and then "Handler", for example `SendEmailProductCreatedEventHandler`.
     - The handler class should implement `DomainEventHandler<TEvent>`, for example `DomainEventHandler<ProductCreatedEvent>`.
     - The handler class should implement the `HandleAsync` method to perform the required action in response to the event, for example sending an email notification when a new product is created.
