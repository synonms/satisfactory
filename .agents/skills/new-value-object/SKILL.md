---
name: new-value-object
description: Guide for adding new Value Object classes to the internal Sample projects or to any projects consuming the Structur framework. Use this when asked to add new features, aggregates or CRUD endpoints to any consuming projects and a new value object is required, or if asked to add a new value object to an existing aggregate.
---

To add new value objects to a consuming project, follow this process:

1. Determine whether the Value Object encapsulates a single scalar value (Simple Value Object) or multiple properties (Complex Value Object).
2. Determine whether the Value Object is specific to a single aggregate or is likely to be shared across multiple aggregates:
   - If it is likely to be shared, it should be created in the Structur Domain project for greater re-use:
      - Use the "ValueObjects" folder of the Structur Domain project folder for the new Value Object class (`Synonms.Structur.Domain/ValueObjects`).
      - If it is a Complex Value Object, use the "Resources" folder of the Structur Api Core project for the corresponding Value Object Resource class (`Synonms.Structur.Api.Core/Resources`).
   - If it is specific to a single aggregate, it can be created directly in the consuming API project:
     - Determine the Collection Name (pluralised aggregate name) for the parent aggregate. For example, if you are adding a value object to a "Employee" aggregate, the Collection Name would be "Employees".
     - Use the "Features/{CollectionName}/ValueObjects" folder of the consuming API project for the new Value Object class. For example, `Synonms.Structur.Sample.Api/Features/Employees/ValueObjects`.  Create this folder if it does not exist.
     - If it is a Complex Value Object, use the "Features/{CollectionName}/ValueObjects" folder of the consuming Client API project for the new Value Object Resource class. For example, `Synonms.Structur.Sample.ClientApi/Features/Employees/ValueObjects`.  Create this folder if it does not exist.
3. If the new value object is s Simple Value Object then the following steps are required:
   - Create the Simple Value Object class in the value objects folder.
     - The class should be named using the singular name of the value object in Pascal case, for example `EmploymentContractStatus`.
     - It should inherit from a derivative of `SimpleValueObject<T>`, for example `StringValueObject` if the underlying type is a string.
     - It should present a private constructor taking the underlying value as a parameter.
     - It should present a static factory method that performs validation against mandatory raw values which returns `OneOf<TValueObject, IEnumerable<DomainRuleFault>>` to ensure that only valid instances can be created, for example `public static OneOf<EmploymentContractStatus, IEnumerable<DomainRuleFault>> CreateMandatory(string propertyName, string value)`.
     - It should present a static factory method that performs validation against optional raw values which returns `OneOf<Maybe<TValueObject>, IEnumerable<DomainRuleFault>>` to ensure that only valid instances can be created or null values converted to `Maybe<T>`, for example `public static OneOf<Maybe<EmploymentContractStatus>, IEnumerable<DomainRuleFault>> CreateOptional(string propertyName, string? value)`.
     - It should provide a static `Convert` method which handles validation faults and provides a default value (e.g. `Moniker.Convert("value")`).  This is used by value converters or serializers required by some persistence providers (e.g. `EmploymentContractStatusBsonSerialiser` used by MongoDb).
   - If the value object is being created directly in the Structur Domain project then create a corresponding BSON serialiser for MongoDb in `Synonms.Structur.Infrastructure.MongoDb/Serialisation` (e.g. `MonikerBsonSerialiser`).
     - It should implement `IBsonSerializer<TValueObject?>` (e.g. `IBsonSerializer<Moniker?>`) and implements the required methods to convert to/from the underlying raw value for MongoDb storage.
4. If the new value object is a Complex Value Object then the following steps are required:
   - Create the related Complex Value Object Resource class. This class will define the API contract for the value object. Use the following guidelines:
     - The class should be named using the Value Object name in Pascal case followed by "Resource", for example `EmploymentContractTermsResource`.
     - It should inherit from `ComplexValueObjectResource`.
     - It should define public mutable properties for the resource as specified in the requirements, for example `public string Name { get; set; }` and `public decimal Price { get; set; }`. The name must match the corresponding property on the Value Object for mapping to work.
     - Scalar properties should be plain C# types (string, int, decimal, etc.) or collections of plain C# types (e.g. `List<string>`).
   - Create the Complex Value Object class in the value objects folder of the API project.  For example `Synonms.Structur.Sample.Api/Features/Employees/ValueObjects`.
     - The class should be named using the singular name of the value object in Pascal case, for example `EmploymentContractTerms`.
     - It should inherit from `ComplexValueObject`.
     - It should define public properties with private setters as specified in the requirements, for example `public EffectiveDate EffectiveFrom { get; private set; }`. These properties will represent the state of the value object and should generally be SimpleValueObject derived types.
     - It should present a private constructor taking all underlying values as parameters.
     - It should present a static factory method that performs validation against mandatory raw values which returns `OneOf<TValueObject, IEnumerable<DomainRuleFault>>` to ensure that only valid instances can be created, for example `public static OneOf<EmploymentContractTerms, IEnumerable<DomainRuleFault>> CreateMandatory(string propertyName, string value)`.
     - It should present a static factory method that performs validation against optional raw values which returns `OneOf<Maybe<TValueObject>, IEnumerable<DomainRuleFault>>` to ensure that only valid instances can be created or null values converted to `Maybe<T>`, for example `public static OneOf<Maybe<EmploymentContractTerms>, IEnumerable<DomainRuleFault>> CreateOptional(string propertyName, string? value)`.
     - It should implement the `GetAtomicValues` method to return the underlying value components for equality comparison, for example:
       ```csharp
       protected override IEnumerable<object?> GetAtomicValues()
       {
           yield return (nameof(EffectiveFrom), EffectiveFrom);
           yield return (nameof(EffectiveTo), EffectiveTo);
       }
       ```

**Example:**
```csharp
public class Moniker : StringValueObject
{
    private Moniker(string value) : base(value) { }
    
    public static OneOf<Moniker, IEnumerable<DomainRuleFault>> CreateMandatory(string propertyName, string value) =>
        CreateMandatory(propertyName, value, DefaultMaxLength);

    public static OneOf<Moniker, IEnumerable<DomainRuleFault>> CreateMandatory(string propertyName, string value, int maxLength) =>
        Validator.CreateBuilder<Moniker>()
            .WithFaultIfNotPopulated(propertyName, value)
            .WithFaultIfLengthMoreThan(propertyName, value, maxLength)
            .Build(() => new Moniker(value));

    public static OneOf<Maybe<Moniker>, IEnumerable<DomainRuleFault>> CreateOptional(string propertyName, string? value)  =>
        CreateOptional(propertyName, value, DefaultMaxLength);

    public static OneOf<Maybe<Moniker>, IEnumerable<DomainRuleFault>> CreateOptional(string propertyName, string? value, int maxLength)
    {
        if (string.IsNullOrWhiteSpace(value))
        {
            return Maybe<Moniker>.None;
        }

        return CreateMandatory(propertyName, value, maxLength).ToMaybe();
    }
    
    public static Moniker Convert(string value) =>
        CreateMandatory(nameof(Moniker), value, value.Length)
            .Match(
                valueObject => valueObject,
                _ => new Moniker(string.Empty));
}
```