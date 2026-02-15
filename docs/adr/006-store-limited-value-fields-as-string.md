# ADR-006: Store Limited-Value Fields as String, Not Enum

## Status

Accepted

## Context

When designing database schemas, fields often need to represent a limited set of values (such as roles, statuses, types, etc.). How these constraints are enforced will impact both the flexibility of the system and the complexity of schema management. Enforcing constraints at the database level (e.g., using ENUM types) provides strong guarantees but requires schema migrations for any change to the set of allowed values. Enforcing constraints at the application level (e.g., using string columns and business logic) offers greater flexibility and easier evolution of value sets, but shifts responsibility for data integrity to the application code and may increase the risk of invalid data if not properly managed.

## Decision

We decided to store fields that represent a limited set of values (enums) as strings in the database, rather than using database ENUM types. Allowed values are enforced in the application code, not the schema. This makes it easier to add, remove, or change valid values as requirements evolve, without requiring database migrations.

## Consequences

- Allowed values can be changed in business logic without schema migrations.
- The database does not enforce allowed values; responsibility shifts to application code.
- Greater flexibility for evolving value sets (roles, statuses, etc.).
- Potential risk of invalid values if business logic is not properly enforced.

## Alternatives Considered

- Using database ENUM types for fields, requiring migrations for any changes to allowed values.
- Using lookup tables for value sets, with foreign keys from the relevant fields.

## Rationale

This approach prioritizes flexibility and ease of maintenance. By enforcing allowed values in business logic, we avoid unnecessary database migrations when requirements change. It also aligns with Python's dynamic nature and keeps the schema simple. While this shifts responsibility for data integrity to the application layer, it enables faster iteration and reduces coupling between business rules and database structure. If stricter enforcement or more robust validation is needed in the future, we can revisit this decision and consider database-level constraints or lookup tables.