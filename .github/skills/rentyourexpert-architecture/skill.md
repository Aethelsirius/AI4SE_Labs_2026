---
name: rentyourexpert-architecture
description: Use this skill for requirements-driven architecture design, comparison of candidate solutions, final architecture selection, and ADR creation for marketplace / service-booking systems.
---

# Skill: RentYourExpert Architecture Advisory

## When to use this skill

Use this skill when a project has a functional requirements document and the next step is to:
- propose 3 architecture options
- explain the trade-offs
- choose the best fit for the project stage
- produce an Architecture Decision Record (ADR)
- keep notes as a recorded conversation/history of the design process

This is especially useful for workflow-heavy, role-based platforms with customers, workers, admins, requests, reviews, Q&A, and moderation.

## Goal

Produce a practical architecture recommendation grounded in project requirements rather than generic best-practice advice.

## Required workflow

1. Read the project requirements carefully.
   - Extract actors, business flows, role-based permissions, and important functional requirements.
   - Identify whether the system is primarily transactional, read-heavy, workflow-heavy, or distributed.

2. Propose three candidate architectures.
   - Example options: modular monolith, domain-oriented microservices, serverless/BFF with search-first catalog.
   - For each option, explain:
     - strengths
     - costs
     - operational complexity
     - fit with the domain
     - key risks

3. Add implementation detail.
   - Break the system into modules/services.
   - Describe responsibilities, tables/entities, ownership boundaries, auth concerns, and request flows.
   - Include tables and diagrams when helpful.

4. Choose the best architecture.
   - Compare the options against the real project needs.
   - Prefer simplicity and correctness over over-engineering.
   - Explain why the chosen option fits the current scale and business model.

5. Produce an ADR.
   - Include: Context, Decision, Alternatives Considered, Consequences, Implementation Notes, Future Evolution.
   - Use clear, structured markdown headings.

6. Keep notes as a conversation record.
   - Preserve a User Request / Agent Response style when documenting the task process.
   - Do not invent dialogue or overwrite the real discussion.
   - Keep the task record and the formal ADR separate.

## Output expectations

Create two artifacts:

1. A task notes file
   - conversation record of the design discussion
   - should follow the structure used in the earlier task notes, with User Request / Agent Response sections

2. An ADR file
   - formal architecture decision record
   - includes rationale, alternatives, diagram(s), tables, implementation insights and schema ideas

## Recommended file system structure

Follow the project’s task-based folder structure, for example:

- `Week_05_Designing/Tasks/Task1/notes.md`
- `Week_05_Designing/Tasks/Task2/notes.md`
- `Week_05_Designing/Tasks/Task2/ADR.md`

When writing the task outputs, prefer:
- Task1 folder for the architecture discussion notes
- Task2 folder for the conversation record and ADR

Do not rewrite or rename unrelated existing files unless the user explicitly asks to normalize the repository layout.

## Quality bar

The final output should be:
- grounded in the actual requirements
- realistic for the project stage
- explicit about trade-offs
- not overly generic
- concrete enough to guide implementation
- structured for GitHub rendering when diagrams are used

## Preferred diagram style

When using diagrams, prefer Mermaid flowcharts so they render in GitHub markdown.

Examples:
- layered architecture
- module relationship diagram
- sequence flow for request creation / acceptance

## Typical architecture decision to prefer for early-stage marketplace apps

For projects like RentYourExpert, the default recommendation is usually a modular monolith unless the requirements clearly demand distributed services.

Why:
- transaction-heavy workflows
- role-based authorization and ownership rules
- easier correctness and debugging
- lower operational overhead at early stage
- easier evolution later if scale increases

## Prompt template for future use

Use this when starting a new task:

"Read the requirements in [file]. Propose 3 architecture options, compare them, explain implementation details, choose the best fit, create an ADR, and keep the task notes as a conversation record. Use the repository task structure: Task1/notes.md for the architecture discussion, Task2/notes.md and Task2/ADR.md for the decision record. Use a modular monolith as the likely default unless the requirements strongly indicate otherwise. Include tables, diagrams, and basic API or schema detail."
