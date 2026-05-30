# Inventory Platform Blueprint v1

## Goal
Rebuild the current project into a modular inventory platform for warehouse, retail, manufacturing, lab, IT, and services use cases, with a path from MVP to enterprise scale.

## Product Principles
- Multi-company from day one.
- Multi-warehouse and multi-location stock control.
- Traceability first: every stock change is an auditable movement.
- UX must work for technical and non-technical users.
- AI must assist operations, not replace deterministic rules.
- Modular monolith first, with clear boundaries for later service extraction.

## Scope for MVP
### Core inventory
- Products, categories, attributes, units of measure.
- Warehouses, locations, bins, zones.
- Lots, serial numbers, expiry dates.
- Minimum and maximum stock rules.
- Stock ledger and current stock snapshots.
- Receipts, dispatches, transfers, adjustments.
- Cycle counts and discrepancy handling.
- Full audit trail.

### AI copilot MVP
- Conversational assistant for inventory questions.
- Demand prediction for selected SKUs.
- Replenishment recommendations based on stock policy and demand signals.
- Simple anomaly detection for stock movements and unusual consumption.

### Adaptability
- Multi-company support.
- Per-area workflows and permissions.
- Public API for integrations.
- Initial connector for one external system.

## Recommended Architecture
### Backend
- FastAPI as API layer.
- Hexagonal or clean architecture.
- Domain modules by capability, not by technical layer only.
- PostgreSQL as primary database.
- Redis for cache, rate limits, background jobs, and AI session state.
- Celery or RQ for asynchronous work.
- Event/outbox pattern for integrations and AI signals.

### Frontend
- React web app as the main UI.
- PWA-ready responsive design.
- Role-based navigation and task flows.
- Mobile basic support through responsive UI first.

### AI layer
- Dedicated AI module/service.
- Forecasting pipeline with baseline statistical model first.
- Retrieval over operational knowledge and inventory context.
- Tool calling for safe actions and read-only guidance.

### Observability and ops
- Structured logs.
- Metrics and traces.
- Audit events stored in database and exported to logs.
- Backups and restore procedures.

## Domain Modules
### 1. Identity and access
- Users, roles, permissions.
- Company membership.
- Session management.

### 2. Inventory master data
- Product catalog.
- Units of measure.
- Categories.
- Product attributes.
- Barcodes and identifiers.

### 3. Stock and traceability
- Stock ledger.
- Current stock by company, warehouse, location, lot, and serial.
- Expiration tracking.
- Reconciliation.

### 4. Operations
- Receipts.
- Dispatches.
- Transfers.
- Adjustments.
- Cycle counts.

### 5. Rules and automation
- Min/max thresholds.
- Reorder policies.
- Workflow rules by area.
- Approval steps.

### 6. Integrations
- ERP connector.
- E-commerce connector.
- POS connector.
- Scanner and RFID ingestion.
- Webhooks and public API.

### 7. AI and analytics
- Assistant chat.
- Forecasting.
- Replenishment suggestions.
- Anomaly detection.
- Report generation.

## Core Data Model
### Tenant layer
- companies
- company_members
- roles
- permissions
- role_permissions

### Catalog layer
- products
- product_variants
- product_attributes
- categories
- units_of_measure
- barcodes

### Warehouse layer
- warehouses
- locations
- location_types
- stock_balances
- stock_ledger
- stock_reservations

### Operations layer
- receipts
- receipt_lines
- shipments
- shipment_lines
- transfers
- transfer_lines
- cycle_counts
- cycle_count_lines
- inventory_adjustments

### AI and analytics layer
- demand_forecasts
- replenishment_suggestions
- anomaly_events
- ai_conversations
- ai_messages

### Integration layer
- external_connections
- sync_jobs
- webhook_deliveries
- import_batches

### Audit layer
- audit_events
- security_events

## API Contract v1
### Auth
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/logout`
- `POST /api/v1/auth/refresh`
- `GET /api/v1/auth/me`

### Companies and access
- `POST /api/v1/companies`
- `GET /api/v1/companies`
- `GET /api/v1/companies/{company_id}`
- `POST /api/v1/companies/{company_id}/members`
- `GET /api/v1/companies/{company_id}/members`

### Catalog
- `GET /api/v1/products`
- `POST /api/v1/products`
- `GET /api/v1/products/{product_id}`
- `PATCH /api/v1/products/{product_id}`
- `GET /api/v1/units`
- `GET /api/v1/categories`

### Warehouses and locations
- `GET /api/v1/warehouses`
- `POST /api/v1/warehouses`
- `GET /api/v1/warehouses/{warehouse_id}/locations`
- `POST /api/v1/locations`

### Stock and movements
- `GET /api/v1/stock`
- `GET /api/v1/stock/{product_id}`
- `POST /api/v1/movements/receipts`
- `POST /api/v1/movements/shipments`
- `POST /api/v1/movements/transfers`
- `POST /api/v1/movements/adjustments`
- `POST /api/v1/counts`
- `POST /api/v1/counts/{count_id}/close`

### AI assistant
- `POST /api/v1/ai/chat`
- `GET /api/v1/ai/recommendations`
- `GET /api/v1/ai/forecasts/{product_id}`
- `GET /api/v1/ai/anomalies`

### Integrations
- `POST /api/v1/integrations/connectors`
- `POST /api/v1/integrations/webhooks`
- `POST /api/v1/integrations/sync`

### Audit
- `GET /api/v1/audit/events`
- `GET /api/v1/audit/events/{event_id}`

## MVP Milestones
### Sprint 1
- Define entities and relationships.
- Replace SQL-agent domain with inventory core.
- Create auth and multi-company scaffolding.
- Stand up product, warehouse, and stock APIs.

### Sprint 2
- Implement receipts, shipments, transfers, adjustments, and counts.
- Add audit ledger and validation rules.
- Create first responsive UI screens.

### Sprint 3
- Add AI assistant with chat, forecast, and replenishment suggestions.
- Add one external connector.
- Add async jobs and basic observability.

### Sprint 4
- Harden permissions, testing, and CI/CD.
- Prepare documentation and deployment path.

## Definition of Done for MVP
- A user can log in, select a company, manage products, warehouses, and stock.
- Every stock change is traceable.
- The AI assistant can answer operational questions and provide recommendations.
- At least one external system can sync data successfully.
- Tests cover core flows and critical failures.
- The UI is usable on desktop and mobile.

## Technical Risks
- Scope creep across industries.
- Overbuilding AI before data exists.
- Weak tenant isolation.
- Inventory ledger inconsistencies.
- Integration brittleness.

## Mitigations
- Fix an MVP domain and keep other areas as configuration.
- Start AI with simple models and deterministic rules.
- Enforce company_id on all tenant data.
- Use a stock ledger as the source of truth.
- Use idempotent integration jobs and retries.

## Next Build Step
1. Define the domain entities and folder structure.
2. Replace the current SQL translator endpoints with inventory APIs.
3. Add migrations and seed data for companies, products, warehouses, and users.
4. Build the first UI flow for login, company selection, and stock overview.
