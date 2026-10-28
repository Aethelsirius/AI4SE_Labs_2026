# RentYourExpert Task 2 Notes

## User Request

Based on the architecture discussion in Task 1, create an Architecture Decision Record (ADR) for RentYourExpert.

## Agent Response

Understood. I formalized the chosen architecture as an ADR and kept it grounded in the actual project requirements and the earlier design decision.

### ADR decision summary
- Project: RentYourExpert
- Chosen architecture: modular monolith
- Why: the system is workflow-heavy, role-based, and transactional, and it does not yet require the complexity of a distributed system
- Main idea: one application with clear internal modules for auth, customer, worker, requests, reviews, Q&A, admin, and catalog/search

### ADR content included
- project context
- decision and rationale
- alternatives considered
- consequences
- implementation guidance
- future evolution path

---

## User Request

Add a few tables and diagrams about the chosen architecture. Also include the relationship of the modules.

## Agent Response

I updated the ADR to include:
- module responsibility table
- core domain relationship table
- layered architectural diagram
- module relationship diagram

These additions help explain how the main modules fit together and how the key domain entities interact within the modular monolith.

---

## User Request

Go into a bit more detail about implementation.

## Agent Response

I expanded the implementation guidance in the ADR to include more concrete design and engineering details.

### Additional implementation detail added
- clear domain boundaries for auth, customer, worker, request, review, Q&A, admin, and catalog/search
- application-layer orchestration for workflows such as create request, accept request, submit review, and answer question
- shared relational database with domain-owned tables
- audit metadata like created_by, created_at, updated_at, and deleted_at
- optimistic locking or version checks for request transitions to prevent race conditions
- explicit authorization checks at the action boundary
- treating the search/catalog as a read-optimized projection, not the source of truth
- keeping the monolith modular intentionally so it can be evolved later without a full rewrite

### Final outcome
The ADR now includes both conceptual architecture and practical implementation guidance for the modular monolith approach.

---

## User Request

Also include DB schema.

## Agent Response

I added a proposed database schema section to the ADR, covering the main domain tables for users, profiles, requests, reviews, Q&A, and moderation.

This gives the architecture both a module view and a data model view, which makes the modular monolith approach clearer and easier to implement.

---

## User Request

Add sequence diagrams where applicable, and also basic API breakdown.

## Agent Response

I extended the ADR with sequence diagrams for the main request lifecycle and a basic API map by module.

### Added material
- customer creates a request sequence diagram
- worker accepts a request sequence diagram
- basic API breakdown by module

This makes the architecture easier to understand from both a workflow perspective and an implementation/API perspective.

---

## User Request

Make the diagrams in flowchart format so they render in GitHub.

## Agent Response

I converted the structural and sequence diagrams in the ADR to Mermaid flowcharts so they render correctly in GitHub markdown.

### Updated diagrams
- layered architecture diagram
- module relationship diagram
- customer request sequence diagram
- worker accept request sequence diagram

This keeps the ADR visually readable while preserving the technical meaning of the architecture.
