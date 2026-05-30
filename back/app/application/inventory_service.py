from decimal import Decimal

from app.infrastructure.inventory_repository import InventoryRepository


class InventoryService:
    def __init__(self, repository: InventoryRepository):
        self.repository = repository

    def ensure_access(self, company_id: str, user_email: str):
        company = self.repository.get_company(company_id, user_email)
        if not company:
            raise ValueError("Company not found or access denied")
        return company

    def create_company(self, name: str, code: str, owner_email: str):
        return self.repository.create_company(name=name, code=code, owner_email=owner_email)

    def set_company_ai_enabled(self, company_id: str, enabled: bool, actor_email: str):
        # ensure actor is member and then delegate to repository which checks owner
        self.ensure_access(company_id, actor_email)
        return self.repository.update_company_ai_enabled(company_id, enabled, actor_email)

    def set_company_ai_config(self, company_id: str, actor_email: str, ai_api_key: str | None = None, ai_quota_per_hour: int | None = None):
        self.ensure_access(company_id, actor_email)
        return self.repository.update_company_ai_config(company_id, actor_email, ai_api_key=ai_api_key, ai_quota_per_hour=ai_quota_per_hour)

    def list_companies(self, user_email: str):
        return self.repository.list_companies(user_email)

    def add_member(self, company_id: str, user_email: str, role: str, actor_email: str):
        self.ensure_access(company_id, actor_email)
        return self.repository.add_member(company_id, user_email, role)

    def list_members(self, company_id: str, actor_email: str):
        self.ensure_access(company_id, actor_email)
        return self.repository.list_members(company_id)

    def create_warehouse(self, company_id: str, name: str, code: str, actor_email: str):
        self.ensure_access(company_id, actor_email)
        return self.repository.create_warehouse(company_id, name, code, actor_email=actor_email)

    def list_warehouses(self, company_id: str, actor_email: str):
        self.ensure_access(company_id, actor_email)
        return self.repository.list_warehouses(company_id)

    def create_location(self, company_id: str, warehouse_id: str, name: str, code: str, location_type: str, parent_location_id: str | None, actor_email: str):
        self.ensure_access(company_id, actor_email)
        return self.repository.create_location(company_id, warehouse_id, name, code, location_type, parent_location_id, actor_email=actor_email)

    def list_locations(self, company_id: str, actor_email: str, warehouse_id: str | None = None):
        self.ensure_access(company_id, actor_email)
        return self.repository.list_locations(company_id, warehouse_id)

    def create_product(self, company_id: str, actor_email: str, **payload):
        self.ensure_access(company_id, actor_email)
        payload["actor_email"] = actor_email
        return self.repository.create_product(company_id=company_id, **payload)

    def list_products(self, company_id: str, actor_email: str):
        self.ensure_access(company_id, actor_email)
        return self.repository.list_products(company_id)

    def record_movement(self, company_id: str, actor_email: str, movement_type: str, payload: dict):
        self.ensure_access(company_id, actor_email)
        return self.repository.record_movement(
            company_id=company_id,
            actor_email=actor_email,
            movement_type=movement_type,
            product_id=payload["product_id"],
            quantity=Decimal(str(payload["quantity"])),
            source_warehouse_id=payload.get("source_warehouse_id"),
            source_location_id=payload.get("source_location_id"),
            destination_warehouse_id=payload.get("destination_warehouse_id"),
            destination_location_id=payload.get("destination_location_id"),
            lot_number=payload.get("lot_number", ""),
            serial_number=payload.get("serial_number", ""),
            reference_type=payload.get("reference_type"),
            reference_id=payload.get("reference_id"),
            notes=payload.get("notes"),
        )

    def list_stock(self, company_id: str, actor_email: str):
        self.ensure_access(company_id, actor_email)
        return self.repository.list_stock(company_id)

    def get_overview(self, company_id: str, actor_email: str):
        self.ensure_access(company_id, actor_email)
        return self.repository.get_overview(company_id)

    def create_cycle_count(self, company_id: str, actor_email: str, warehouse_id: str, name: str, notes: str | None, lines: list[dict], auto_close: bool = True):
        self.ensure_access(company_id, actor_email)
        return self.repository.create_cycle_count(
            company_id=company_id,
            warehouse_id=warehouse_id,
            name=name,
            lines=lines,
            actor_email=actor_email,
            notes=notes,
            auto_close=auto_close,
        )

    def get_cycle_count(self, company_id: str, actor_email: str, count_id: str):
        self.ensure_access(company_id, actor_email)
        return self.repository.get_cycle_count(company_id, count_id)

    def list_cycle_counts(self, company_id: str, actor_email: str):
        self.ensure_access(company_id, actor_email)
        return self.repository.list_cycle_counts(company_id)

    def close_cycle_count(self, company_id: str, actor_email: str, count_id: str):
        self.ensure_access(company_id, actor_email)
        return self.repository.close_cycle_count(company_id, count_id, actor_email=actor_email)