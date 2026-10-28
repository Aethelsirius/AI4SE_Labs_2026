# RentYourExpert ADR Discussion Record

## User Request

Based on the architecture discussion in Task 1, create an Architecture Decision Record (ADR) for RentYourExpert.

## Agent Response

The Task 1 analysis identified RentYourExpert as a transactional, role-based service marketplace with customers, workers, and administrators. Its core workflows are authentication, worker discovery, service-request management, worker Q&A, reviews, and administrative moderation.

Three architectures were considered:

1. **Modular monolith:** one deployable application with explicit modules and a shared PostgreSQL database.
2. **Domain-oriented microservices:** independently deployed identity, profile, search, request, review, Q&A, and administration services with separate data ownership.
3. **Serverless/event-driven BFF:** API Gateway functions backed by managed data services and an event bus.

The selected decision is to implement the first version as a **modular monolith backed by PostgreSQL**. This option provides strong consistency for request and review workflows, keeps role-based authorization in one security boundary, and minimizes infrastructure and operational complexity. Internal module boundaries and domain events should be designed so that high-load areas, especially search, can be extracted later if required.

The formal ADR is recorded separately in `task2_rerun_ADR.md`.

### Decision summary

| Area | Initial decision |
|---|---|
| Application style | Modular monolith |
| API style | REST API |
| Persistence | PostgreSQL relational database |
| Security | Central authentication with role- and resource-based authorization |
| Search | PostgreSQL indexes initially; dedicated search index only when justified |
| Modules | Identity, Profiles, Catalogue, Requests, Reviews, Q&A, Administration |
| Future evolution | Extract search, notifications, or other bounded modules when scale requires it |
