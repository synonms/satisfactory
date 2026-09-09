---
name: new-aggregate-member
description: Guide for adding new Aggregate Members to the internal Sample projects or to any projects consuming the Structur framework. Use this when asked to add new features, aggregates or CRUD endpoints to any consuming projects and a new aggregate member is required, or if asked to add an aggregate member to an existing aggregate.
---

To add new aggregate members to a consuming project, follow this process:

1. Determine the aggregate name (singular) for the parent aggregate. For example, if you are adding an aggregate member to a "Employee" aggregate, the aggregate root name would be "Employee".
2. Determine the pluralised form of the aggregate name to be used as the collection name for the feature. For example, if the aggregate name is "Employee" the collection name would be "Employees".
3. Determine the destination folder for the new feature in the consuming Client API project as `{ClientApiProject}/Features/{CollectionName}`. For example, `Synonms.Structur.Sample.ClientApi/Features/Employees`.  This will contain the shared backend/frontend code.  Create it if it does not exist.  In this folder:
   - Create the related Child Resource class. This class will define the API contract for the aggregate member. Use the following guidelines:
     - The class should be named using the Aggregate Member or Value Object name in Pascal case followed by "Resource", for example `EmploymentContractResource`.
     - It should inherit from `ChildResource`.
     - It should define public mutable properties for the resource as specified in the requirements, for example `public string Name { get; set; }` and `public decimal Price { get; set; }`. The name must match the corresponding property on the Aggregate Member or Value Object for mapping to work.
     - It should provide a default empty private constructor as required by some ORMs.
     - It should provide an overloaded private constructor that takes `Guid id` parameter to pass to the base class, for example `private EmploymentContractResource(Guid id) : base(id) { }`.
     - Scalar properties should be plain C# types (string, int, decimal, etc.) or collections of plain C# types (e.g. `List<string>`).
4. Determine the destination folder for the new feature in the consuming API project as `{ApiProject}/Features/{CollectionName}`. For example, `Synonms.Structur.Sample.Api/Features/Employees`.  This will contain the backend code.  Create it if it does not exist.  In this folder:
    - Determine the aggregate member name (singular) for the new aggregate member, for example `EmploymentContract`.
    - Create the Aggregate Member class in the aggregate features folder of the Api project. Use the following guidelines:
      - The class should be named using the singular name of the member in Pascal case, for example `EmploymentContract`.
      - It should inherit from `AggregateMember<TAggregateMember>`, for example `AggregateMember<EmploymentContract>`.
      - It should provide a default empty private constructor as required by some ORMs.
      - It should provide an overloaded private constructor that takes `EntityId<TAggregateMember> id` parameter to pass to the base class, along with any other parameters required to set mandatory properties, for example `private EmploymentContract(EntityId<EmploymentContract> id, Moniker name) : base(id) { Name = name; }`.
      - It should define public properties with private setters for the member as specified in the requirements, for example `public Moniker Name { get; private set; }`. These properties will represent the state of the member and should generally be ValueObject derived types.
      - It should provide an internal factory method that performs validation against a Resource and returns `OneOf<TAggregateMember, IEnumerable<DomainRuleFault>>` to ensure that only valid instances can be created, for example `internal static OneOf<EmploymentContract, IEnumerable<DomainRuleFault>> Create(string parentPropertyName, EmploymentContractResource resource)`.  This factory method should use the `Validator.CreateBuilder<T>()` fluent builder to perform validation, convert the plain Resource property values to the corresponding value objects and construct the member instance if validation passes.
      - It should provide an internal instance method that performs validation against a Resource and updates the member if validation passes, for example `internal Maybe<Fault> Update(EmploymentContractResource resource, Action rootUpdatedAction)`.  This method should use the `Validator.CreateBuilder<T>()` fluent builder to perform validation, convert the plain Resource property values to the corresponding value objects and update the member instance if validation passes.  The method should return `Maybe<Fault>` to indicate whether the operation was successful or if there were any validation errors or domain rule violations.
