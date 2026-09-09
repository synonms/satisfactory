---
name: new-aggregate-root
description: Guide for adding new Aggregate Roots to the internal Sample projects or to any projects consuming the Structur framework. Use this when asked to add new aggregates or aggregate roots to any consuming projects.
---

To add new aggregate roots to a consuming project, follow this process:

1. Determine the aggregate name (singular) and collection name (plural) for the new aggregate. For example, if you are adding a "Product" aggregate, the aggregate root name would be "Product" and the collection name (used for the URL root path) would be "products".
2. If it does not already exist, create a new "Features" folder in the consuming API project (e.g. `Synonms.Structur.Sample.Api`). For example, `Synonms.Structur.Sample.Api/Features`.
3. If it does not already exist, create a new "Features" folder in the consuming Client API project (e.g. `Synonms.Structur.Sample.ClientApi`). For example, `Synonms.Structur.Sample.ClientApi/Features`.
4. If it does not already exist, create a new folder for the aggregate features in the "Features" directory of the consuming API project using the pluralised aggregate name in Pascal case. For example, `Synonms.Structur.Sample.Api/Features/Products`.  This will contain the backend code.
5. If it does not already exist, create a new folder for the aggregate features in the "Features" directory of the consuming Client API project using the pluralised aggregate name in Pascal case. For example, `Synonms.Structur.Sample.ClientApi/Features/Products`.  This will contain the shared backend/frontend code.
6. Create the related Resource class in the aggregate features folder of the Client API project. This class will define the API contract for the aggregate root. Use the following guidelines:
   - The class should be named using the singular aggregate name in Pascal case followed by "Resource", for example `ProductResource`.
   - It should inherit from `Resource`.
   - It should provide a default empty public constructor.
   - It should provide an overloaded public constructor that takes `Guid id` and `Link selfLink` parameters to pass to the base class, for example `public ProductResource(Guid id, Link selfLink) : base(id, selfLink) {}`.
   - It should define a field that specifies the collection path for the resource, for example `public const string CollectionPath = "products";`.  The value should be the pluralised collection name determined earlier (lowercase).
   - The CollectionName field should be used in the implementation of `GetCollectionPath()`, for example `public override string GetCollectionPath() => CollectionPath;`.
   - It should define public mutable properties for the resource as specified in the requirements, for example `public string Name { get; set; }` and `public decimal Price { get; set; }`. The name must match the corresponding property on the Aggregate Root for mapping to work.
   - Scalar properties should be plain C# types (string, int, decimal, etc.) or collections of plain C# types (e.g. `List<string>`).
   - Properties that represent relationships to other aggregates should be represented as `Guid` or `List<Guid>` to represent the IDs of the related aggregates.
   - Properties that represent embedded aggregate members or complex value objects should be represented as separate Resource classes, for example `public CategoryResource Category { get; set; }` to represent an embedded Category resource.
   - The public properties should be decorated with Structur attributes to define any required validation rules, for example `[StructurMaxLength(100)]` to represent a maximum string length of 100.
7. Create the Aggregate Root class in the aggregate features folder of the Api project. This class will represent the domain model for the feature and will contain the business logic. Use the following guidelines:
   - The class should be named using the singular aggregate name in Pascal case, for example `Product`.
   - It should inherit from `AggregateRoot<TAggregateRoot>`, for example `AggregateRoot<Product>`.
   - It should provide a default empty private constructor as required by some ORMs.
   - It should provide an overloaded private constructor that takes `EntityId<TAggregateRoot> id`, `Guid tenantId` and `UserAction createdAction` parameters to pass to the base class, along with any other parameters required to set mandatory properties, for example `private Product(EntityId<Product> id, Guid tenantId, UserAction createdAction, Moniker name) : base(id, tenantId, createdAction) { Name = name; }`.
   - It should define public properties with private setters for the aggregate as specified in the requirements, for example `public Moniker Name { get; private set; } = null!;` and `public Currency? Price { get; private set; }`. These properties will represent the state of the aggregate and should generally be ValueObject or AggregateMember derived types.
   - It should be decorated with the `StructurResourceAttribute` to define the relationship to the new Resource and control how the CRUD endpoints should be registered, for example `[StructurResource(typeof(ProductResource), "products", allowAnonymous: true, pageLimit: 5)]` links to the `ProductResource` class and sets up endpoint routes using the URL base path (collection name) `products`.
     - The attribute properties `isCreateDisabled`, `isUpdateDisabled` and `isDeleteDisabled` can be used to control which CRUD operations are supported. For example, if the aggregate should not support deletions then `isDeleteDisabled` would be set to `true`.
   - It should provide an internal factory method that performs validation against the Resource and returns `Result<TAggregateRoot>` to ensure that only valid instances can be created, for example `internal static Result<Person> Create(Guid tenantId, ProductResource resource, UserActionDto createdActionDto)`.  This factory method should use the `Validator.CreateBuilder<T>()` fluent builder to perform validation, convert the plain Resource property values to the corresponding value objects and construct the aggregate instance if validation passes.
   - It should provide an internal instance method that performs validation against the Resource and updates the aggregate if validation passes, for example `internal Maybe<Fault> Update(ProductResource resource, UserActionDto updatedActionDto, Version? applicableVersion = null)`.  This method should use the `Validator.CreateBuilder<T>()` fluent builder to perform validation, convert the plain Resource property values to the corresponding value objects and update the aggregate instance if validation passes.  The method should use the protected update methods to modify properties, which will handle updating the audit fields and entity tag automatically, for example ` UpdateMandatoryValue(x => x.Name, nameValueObject, updatedActionValueObject);`.  The method should return `Maybe<Fault>` to indicate whether the operation was successful or if there were any validation errors or domain rule violations.  If updating a collection of aggregate members it should utilise the `MergeChanges` extension method to ensure the collection is updated correctly while maintaining entity identity for existing members and allowing new members to be added, for example `Contracts.MergeChanges(resource.Contracts, r => EmploymentContract.Create(nameof(Contracts), r), (am, r) => am.Update(r, () => MarkAsUpdated(updatedActionValueObject)))`.
8. Create corresponding domain events if create, update and/or delete operations are required. Use the following guidelines:
   - The event classes should be created in a `Events` folder in the new feature folder, for example `Synonms.Structur.Sample.Api/Features/Products/Events`.
   - The event class should be named using the singular name of the aggregate followed by the action and then `Event`, for example `ProductCreatedEvent`, `ProductUpdatedEvent` and `ProductDeletedEvent`.
   - The event class should inherit from the appropriate derivative of `DomainEvent<TAggregateRoot>`, for example `AggregateCreatedDomainEvent<Product, ProductResource>`.
   - The created event should ultimately call the new Create factory method on the Aggregate Root to perform the action, for example `return Product.Create(TenantId, resource, _userActionProvider.Get(), applicableVersion);`.
   - The updated event should ultimately call the new Update instance method on the Aggregate Root to perform the action, for example `return aggregateRoot.Update(resource, _userActionProvider.Get(), applicableVersion);`.
   - The deleted event should ultimately call the Delete instance method on the `AggregateRoot<TAggregateRoot>` base class to perform the action, for example `return aggregateRoot.Delete(_userActionProvider.Get()).ToResult(() => aggregateRoot);`.
9. Create an implementation of `IDomainEventFactory<TAggregateRoot, TResource>` for the new aggregate root and resource to enable domain event creation in the mediation layer. Use the following guidelines:
   - The factory class should be created in a `Events` folder in the new feature folder, for example `Synonms.Structur.Sample.Api/Features/Products/Events`.
   - The event class should be named using the singular name of the aggregate followed by `DomainEventFactory`, for example `ProductDomainEventFactory`.
   - The class should implement `IDomainEventFactory<TAggregateRoot, TResource>`, for example `IDomainEventFactory<Product, ProductResource>`.
   - The class should implement the `GenerateCreatedEvent`, `GenerateDeletedEvent` and/or `GenerateUpdatedEvent` methods to create the appropriate domain event where applicable, otherwise throw `NotImplementedException` if a particular event type is not applicable, for example if the aggregate does not support updates then `GenerateUpdatedEvent` would throw `NotImplementedException`.
   - Use dependency `ITenantContext<SampleTenant>` to access the current tenant ID, `IUserActionProvider` to access the current user action and `IVersionContext` to access the requested version when creating domain events in the factory methods, for example `return _tenantContext.GetTenant().Bind(tenant => Result<DomainEvent<Employee>>.Success(new EmployeeCreatedEvent(_userActionProvider, _versionContext, (EntityId<Employee>)resource.Id, resource, tenant.Id)));`.

**Example:**
```csharp
public class Person : AggregateRoot<Person>
{
    private Person(EntityId<Person> id, Guid tenantId, UserAction createdAction, Moniker name) : base(id, tenantId, createdAction) 
    {
        Name = name;
    }
    
    public Moniker Name { get; private set; } = null!;
    
    internal Maybe<Fault> UpdateName(string newName, UserAction updatedAction) =>
        Moniker.Convert(newName)
            .Match(
                moniker => {
                    UpdateMandatoryValue(u => u.Name, moniker, updatedAction);
                    return Maybe<Fault>.None;
                },
                fault => new DomainRulesFault([fault]));
    
    internal static Result<Person> Create(Guid tenantId, string name, UserActionDto createdActionDto) =>
        Validator.CreateBuilder<Person>()
            .WithMandatoryScalarProperty(createdActionDto, x => UserAction.CreateMandatory(nameof(CreatedAction), x), out UserAction createdActionValueObject)
            .WithMandatoryScalarProperty(name, x => Moniker.CreateMandatory(nameof(Name), x), out Moniker nameValueObject)
            .Build()
            .ToResult(() => new Person(EntityId<Person>.New(), tenantId, createdActionValueObject, nameValueObject));
}
```