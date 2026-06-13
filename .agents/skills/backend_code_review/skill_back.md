# Skill Instructions: Architecture and Testing Review — Django / Python Backend

> **Project:** Laboratory Maintenance Management System  
> **Group:** GPT — Universidad Nacional de Colombia, Bogotá Campus  

This skill is designed for the agent to validate the backend architecture and coding practices according to the requirements specified in the course deliverables.

## 1. Backend Architecture

### 1.1 Architecture Diagram
The project must follow an n-tier structure defined as follows:

```
┌──────────────────────────────────────────────────────────────┐
│                     Controller Layer                         │
│          (HTTP Endpoints — Django REST Framework)            │
└───────────────────────────┬──────────────────────────────────┘
                            │ invokes
┌───────────────────────────▼──────────────────────────────────┐
│                     Service Layer                            │
│   ┌─────────────────────────┐  ┌────────────────────────┐    │
│   │   EquipmentServices     │  │      UserServices      │    │
│   │ • Business logic        │  │ • Business logic       │    │
│   │ • Validations           │  │ • OAuth 2.0 / JWT      │    │
│   │ • Response formatting   │  │ • Response formatting  │    │
│   └─────────────┬───────────┘  └──────────┬─────────────┘    │
└─────────────────┼─────────────────────────┼──────────────────┘
                  │ delegates to            │ delegates to
┌─────────────────▼─────────────────────────▼──────────────────┐
│                   Repository Layer                           │
│   ┌──────────────────────────┐  ┌──────────────────────┐     │
│   │  EquipmentRepository     │  │   UserRepository     │     │
│   │ • Django ORM Queries     │  │ • Django ORM Queries │     │
│   │ • DB Abstraction         │  │ • DB Abstraction     │     │
│   └──────────────┬───────────┘  └──────────┬───────────┘     │
└──────────────────┼─────────────────────────┼─────────────────┘
                   │ uses models             │ uses models
┌──────────────────▼─────────────────────────▼─────────────────┐
│                     Models (Django ORM)                      │
│   Equipo, Usuario, Tecnico, Solicitud, HorarioAtencion       │
│   Intervencion, Asignacion, Notificacion, Adjunto, Anexo     │
└──────────────────────────────────────────────────────────────┘
```

### 1.2 Responsibilities by Layer

| Layer | Files | Responsibility | Restrictions (What NOT to do) |
|-------|-------|----------------|-------------------------------|
| Service | `*_services.py` | Business logic, validations, response formatting | Direct DB queries, object access via `Model.objects.*`, interacting with database directly |
| Repository | `*_repository.py` | DB access via Django ORM | Business rules, throwing business-oriented `ValueError` exceptions |
| Model | `models.py` | Definition of entities and relationships | Containing service logic methods |

---

## 2. Good Practices Guide — Python / Django

### 2.1 Style Standards (Based on PEP 8)
*   **Maximum line length:** 120 characters.
*   **Class names:** `PascalCase`.
*   **Method and variable names:** `snake_case`.
*   **Module constants:** `UPPER_SNAKE_CASE`.

### 2.2 Design Principles
*   **SRP (Single Responsibility Principle):** Each method must fulfill a single purpose.
*   **DRY (Don't Repeat Yourself):** Reuse of static validation methods.
*   **Dependency Inversion:** Services depend on repositories, not models directly.
*   **Fail fast:** Validations must execute at the beginning of methods.

### 2.3 Exception Handling and Typing
Specific exceptions with descriptive messages must be used. Generic exceptions like `raise Exception(...)` are forbidden. In addition, all public methods must include Type Hints in their signature.

---

## 3. MANDATORY Validation Rules (MUST HAVE)
The agent must evaluate compliance with these rules. A failure to perform any of these indicates a critical issue.

| ID | Rule | Description |
|----|------|-------------|
| M1 | Layer separation | Services do not import models files. Repositories do not contain business logic. |
| M2 | SRP per method | Each method has a single functional responsibility. |
| M3 | No magic numbers | Literal values must be assigned to named constants. |
| M4 | Specific exceptions | Use specific types like `ValueError`, `PermissionError`, including explicit context. |
| M5 | Pre-persistence validation | Data must be fully validated before accessing the repository layer. |
| M6 | Atomic transactions | Usage of `@transaction.atomic` for database writes. |
| M7 | Descriptive naming | Clear names that express intent without obscure abbreviations. |
| M8 | Adherence to DRY | No explicit duplication in validation logic. |
| M9 | No direct queries in services | Zero references to `Model.objects.*` inside the `services` layer. |
| M10 | Type Hints | All exposed methods must declare input parameter types and output type. |

---

## 4. RECOMMENDED Validation Rules (SHOULD HAVE)
The agent will evaluate these practices to assess the project's maintainability score.

| ID | Rule | Description |
|----|------|-------------|
| S1 | Structural documentation | Use section comments to group related logic. |
| S2 | Early constant declaration | Constants are defined at the top of the file, before functions or classes. |
| S3 | `@staticmethod` decorator | Correct usage of static decorators for stateless methods. |
| S4 | Contextualized error messages | Error messages clarify the faulty value and the allowed ones. |
| S5 | Line length limit | Maximum of 120 characters respected via structured line breaks. |
| S6 | Standardized response formats | Existence of consistent methods for structuring output dictionaries. |
| S7 | Visual structuring of constants | Constants of the same block are grouped and aligned. |

---

## 5. Execution Instructions for the Testing Agent Module

When the user invokes this technical review (evaluating backend architecture and testing), the agent will interact by proceeding as follows:

1.  Analyze the repository's real structure (`controllers`, `services`, `repositories`, `models` files, and `tests` directory).
2.  Perform a thorough inspection for each rule (M1-M10 and S1-S7).
3.  Include in the evaluation the tests coverage and integrity (as per testing module deliverable parameters).
4.  Generate a structured technical report, presented formally (without emojis): Rule ID, Compliance Status ([COMPLIES] / [DOES NOT COMPLY]), and Inspection Evidence.
5.  Produce an executive summary summarizing the application's overall status.

Expected output format example:

```text
[ARCHITECTURE AND TESTING TECHNICAL REPORT]

MANDATORY COMPLIANCE (MUST HAVE)
------------------------------------------------------------
M1 - Layer separation: [COMPLIES]. Evidence: No models default imports detected in the service layer. [File link]
M2 - SRP per method: [COMPLIES]. Evidence: (...)

EXECUTIVE SUMMARY
------------------------------------------------------------
MUST HAVE: 10/10 [100%]
SHOULD HAVE: 7/7 [100%]
OBSERVATIONS: [Additional details]
```