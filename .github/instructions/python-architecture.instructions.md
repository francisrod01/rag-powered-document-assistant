---
description: "Use when generating or modifying Python code. Enforces design patterns (YAGNI, DRY, SOLID) and strict type checking."
name: "Python Architecture & Typing"
applyTo: "**/*.py"
---

# Python Code Generation Guidelines

When generating or modifying Python code in this workspace, ALWAYS adhere to the following principles:

1. **Design Patterns & Clean Code**:
   - **SOLID Principles**: Keep classes focused (Single Responsibility), extendable without modification (Open/Closed), substituteable (Liskov Substitution), use specific interfaces (Interface Segregation), and depend on abstractions (Dependency Inversion).
   - **YAGNI (You Aren't Gonna Need It)**: Do not add functionality, abstractions, or genericness until it is absolutely necessary. Keep solutions as simple and direct as possible.
   - **DRY (Don't Repeat Yourself)**: Extract reusable logic into helper functions or base classes where it makes sense, without over-engineering.

2. **Strict Type Checking**:
   - Always include type hints for function arguments and return types.
   - Use modern Python type hints (e.g., modern SQLAlchemy `Mapped` typing, `List`, `Optional`, `Dict`).
   - Ensure the generated code is compatible with strict static type checkers (like Pylance/Mypy).
   - Resolve potential `None` type issues safely (e.g., using `getattr` or explicit `is not None` checks).
