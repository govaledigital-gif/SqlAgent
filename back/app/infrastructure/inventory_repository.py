from contextlib import contextmanager
from datetime import datetime
from decimal import Decimal
import json
from uuid import uuid4

from sqlalchemy import func, text
import re

from app.config.settings import settings
from app.domain.base import Base
from app.domain.inventory import (
    AuditEvent,
    Company,
    CompanyMember,
    CycleCount,
    CycleCountLine,
    Location,
    Product,
    StockBalance,
    StockMovement,
    Warehouse,
)
from app.infrastructure.database import create_database_engine, create_session_factory
from app.infrastructure.security_logger import SecurityLogger


logger = SecurityLogger(__name__)


class InventoryRepository:
    def __init__(self):
        if not settings.DATABASE_URL:
            raise ValueError("DATABASE_URL must be configured")

        self.engine = create_database_engine()
        self.SessionLocal = create_session_factory(self.engine, expire_on_commit=False)
        Base.metadata.create_all(bind=self.engine)

    @contextmanager
    def session_scope(self):
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def _create_audit_event(self, session, company_id: str, actor_email: str | None, action: str, entity_type: str, entity_id: str | None, metadata: dict | None = None):
        event = AuditEvent(
            id=str(uuid4()),
            company_id=company_id,
            actor_email=actor_email,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            metadata_json=json.dumps(metadata or {}, ensure_ascii=False),
            created_at=datetime.utcnow(),
        )
        session.add(event)
        return event

    def create_company(self, name: str, code: str, owner_email: str) -> Company:
        with self.session_scope() as session:
            existing = session.query(Company).filter(Company.code == code).first()
            if existing:
                raise ValueError(f"Company code {code} already exists")

            company = Company(
                id=str(uuid4()),
                name=name,
                code=code,
                owner_email=owner_email,
                ai_enabled=False,
                is_active=True,
            )
            member = CompanyMember(
                id=str(uuid4()),
                company_id=company.id,
                user_email=owner_email,
                role="owner",
                is_active=True,
            )
            session.add(company)
            session.add(member)
            self._create_audit_event(session, company.id, owner_email, "company.created", "company", company.id, {"code": code})
            return company

    def update_company_ai_enabled(self, company_id: str, enabled: bool, actor_email: str | None = None) -> Company:
        with self.session_scope() as session:
            company = session.query(Company).filter(Company.id == company_id).first()
            if not company:
                raise ValueError("Company not found")
            # Only owner can change AI opt-in
            if company.owner_email != actor_email:
                raise ValueError("Only company owner can change AI settings")
            company.ai_enabled = bool(enabled)
            session.add(company)
            self._create_audit_event(session, company_id, actor_email, "company.ai.toggled", "company", company_id, {"ai_enabled": company.ai_enabled})
            return company

    def update_company_ai_config(self, company_id: str, actor_email: str | None = None, ai_api_key: str | None = None, ai_quota_per_hour: int | None = None) -> Company:
        with self.session_scope() as session:
            company = session.query(Company).filter(Company.id == company_id).first()
            if not company:
                raise ValueError("Company not found")
            if company.owner_email != actor_email:
                raise ValueError("Only company owner can change AI settings")
            if ai_api_key is not None:
                company.ai_api_key = ai_api_key
            if ai_quota_per_hour is not None:
                company.ai_quota_per_hour = str(ai_quota_per_hour)
            session.add(company)
            self._create_audit_event(session, company_id, actor_email, "company.ai.config.updated", "company", company_id, {"ai_quota_per_hour": company.ai_quota_per_hour})
            return company

    def list_companies(self, user_email: str) -> list[Company]:
        with self.session_scope() as session:
            return (
                session.query(Company)
                .join(CompanyMember, CompanyMember.company_id == Company.id)
                .filter(CompanyMember.user_email == user_email, CompanyMember.is_active.is_(True))
                .order_by(Company.created_at.desc())
                .all()
            )

    def get_company(self, company_id: str, user_email: str | None = None) -> Company | None:
        with self.session_scope() as session:
            company = session.query(Company).filter(Company.id == company_id).first()
            if not company:
                return None
            if user_email is None:
                return company
            member = (
                session.query(CompanyMember)
                .filter(CompanyMember.company_id == company_id, CompanyMember.user_email == user_email, CompanyMember.is_active.is_(True))
                .first()
            )
            return company if member else None

    def list_members(self, company_id: str) -> list[CompanyMember]:
        with self.session_scope() as session:
            return (
                session.query(CompanyMember)
                .filter(CompanyMember.company_id == company_id)
                .order_by(CompanyMember.created_at.asc())
                .all()
            )

    def add_member(self, company_id: str, user_email: str, role: str = "member") -> CompanyMember:
        with self.session_scope() as session:
            existing = (
                session.query(CompanyMember)
                .filter(CompanyMember.company_id == company_id, CompanyMember.user_email == user_email)
                .first()
            )
            if existing:
                raise ValueError("Member already exists in company")
            member = CompanyMember(
                id=str(uuid4()),
                company_id=company_id,
                user_email=user_email,
                role=role,
                is_active=True,
            )
            session.add(member)
            self._create_audit_event(session, company_id, user_email, "company.member.added", "company_member", member.id, {"role": role})
            return member

    def create_warehouse(self, company_id: str, name: str, code: str, actor_email: str | None = None) -> Warehouse:
        with self.session_scope() as session:
            existing = session.query(Warehouse).filter(Warehouse.company_id == company_id, Warehouse.code == code).first()
            if existing:
                raise ValueError(f"Warehouse code {code} already exists in company")

            warehouse = Warehouse(
                id=str(uuid4()),
                company_id=company_id,
                name=name,
                code=code,
                is_active=True,
            )
            session.add(warehouse)
            session.flush()

            default_location = Location(
                id=str(uuid4()),
                company_id=company_id,
                warehouse_id=warehouse.id,
                parent_location_id=None,
                name="Main",
                code="MAIN",
                location_type="storage",
                is_active=True,
            )
            session.add(default_location)
            self._create_audit_event(session, company_id, actor_email, "warehouse.created", "warehouse", warehouse.id, {"code": code})
            return warehouse

    def list_warehouses(self, company_id: str) -> list[Warehouse]:
        with self.session_scope() as session:
            return session.query(Warehouse).filter(Warehouse.company_id == company_id).order_by(Warehouse.created_at.desc()).all()

    def create_location(self, company_id: str, warehouse_id: str, name: str, code: str, location_type: str = "storage", parent_location_id: str | None = None, actor_email: str | None = None) -> Location:
        with self.session_scope() as session:
            existing = session.query(Location).filter(Location.warehouse_id == warehouse_id, Location.code == code).first()
            if existing:
                raise ValueError(f"Location code {code} already exists in warehouse")

            location = Location(
                id=str(uuid4()),
                company_id=company_id,
                warehouse_id=warehouse_id,
                parent_location_id=parent_location_id,
                name=name,
                code=code,
                location_type=location_type,
                is_active=True,
            )
            session.add(location)
            self._create_audit_event(session, company_id, actor_email, "location.created", "location", location.id, {"warehouse_id": warehouse_id})
            return location

    def list_locations(self, company_id: str, warehouse_id: str | None = None) -> list[Location]:
        with self.session_scope() as session:
            query = session.query(Location).filter(Location.company_id == company_id)
            if warehouse_id:
                query = query.filter(Location.warehouse_id == warehouse_id)
            return query.order_by(Location.created_at.asc()).all()

    def get_default_location(self, company_id: str, warehouse_id: str) -> Location | None:
        with self.session_scope() as session:
            return (
                session.query(Location)
                .filter(Location.company_id == company_id, Location.warehouse_id == warehouse_id, Location.code == "MAIN")
                .first()
            )

    def create_product(
        self,
        company_id: str,
        sku: str,
        name: str,
        unit_of_measure: str,
        description: str | None = None,
        category: str | None = None,
        min_stock: Decimal = Decimal("0"),
        max_stock: Decimal = Decimal("0"),
        reorder_point: Decimal = Decimal("0"),
        barcode: str | None = None,
        actor_email: str | None = None,
    ) -> Product:
        with self.session_scope() as session:
            existing = session.query(Product).filter(Product.company_id == company_id, Product.sku == sku).first()
            if existing:
                raise ValueError(f"Product SKU {sku} already exists in company")

            product = Product(
                id=str(uuid4()),
                company_id=company_id,
                sku=sku,
                name=name,
                description=description,
                category=category,
                unit_of_measure=unit_of_measure,
                min_stock=min_stock,
                max_stock=max_stock,
                reorder_point=reorder_point,
                barcode=barcode,
                is_active=True,
            )
            session.add(product)
            self._create_audit_event(session, company_id, actor_email, "product.created", "product", product.id, {"sku": sku})
            return product

    def list_products(self, company_id: str) -> list[Product]:
        with self.session_scope() as session:
            return session.query(Product).filter(Product.company_id == company_id).order_by(Product.created_at.desc()).all()

    def get_product(self, company_id: str, product_id: str) -> Product | None:
        with self.session_scope() as session:
            return session.query(Product).filter(Product.company_id == company_id, Product.id == product_id).first()

    def _get_balance(self, session, company_id: str, product_id: str, warehouse_id: str, location_id: str, lot_number: str, serial_number: str) -> StockBalance | None:
        return (
            session.query(StockBalance)
            .filter(
                StockBalance.company_id == company_id,
                StockBalance.product_id == product_id,
                StockBalance.warehouse_id == warehouse_id,
                StockBalance.location_id == location_id,
                StockBalance.lot_number == lot_number,
                StockBalance.serial_number == serial_number,
            )
            .first()
        )

    def _upsert_balance(self, session, company_id: str, product_id: str, warehouse_id: str, location_id: str, lot_number: str, serial_number: str, delta: Decimal) -> StockBalance:
        balance = self._get_balance(session, company_id, product_id, warehouse_id, location_id, lot_number, serial_number)
        if balance:
            balance.quantity = Decimal(balance.quantity) + delta
            balance.updated_at = datetime.utcnow()
            return balance

        balance = StockBalance(
            id=str(uuid4()),
            company_id=company_id,
            product_id=product_id,
            warehouse_id=warehouse_id,
            location_id=location_id,
            lot_number=lot_number,
            serial_number=serial_number,
            quantity=delta,
        )
        session.add(balance)
        return balance

    def record_movement(
        self,
        company_id: str,
        product_id: str,
        movement_type: str,
        quantity: Decimal,
        actor_email: str | None = None,
        source_warehouse_id: str | None = None,
        source_location_id: str | None = None,
        destination_warehouse_id: str | None = None,
        destination_location_id: str | None = None,
        lot_number: str = "",
        serial_number: str = "",
        reference_type: str | None = None,
        reference_id: str | None = None,
        notes: str | None = None,
    ) -> StockMovement:
        with self.session_scope() as session:
            product = self.get_product(company_id, product_id)
            if not product:
                raise ValueError("Product not found for company")

            movement_type = movement_type.lower().strip()
            lot_number = lot_number or ""
            serial_number = serial_number or ""

            if movement_type == "receipt":
                if not destination_warehouse_id:
                    raise ValueError("destination_warehouse_id is required for receipt")
                if not destination_location_id:
                    default_location = self.get_default_location(company_id, destination_warehouse_id)
                    if not default_location:
                        raise ValueError("Destination warehouse has no default location")
                    destination_location_id = default_location.id
                self._upsert_balance(session, company_id, product_id, destination_warehouse_id, destination_location_id, lot_number, serial_number, Decimal(quantity))

            elif movement_type == "dispatch":
                if not source_warehouse_id:
                    raise ValueError("source_warehouse_id is required for dispatch")
                if not source_location_id:
                    default_location = self.get_default_location(company_id, source_warehouse_id)
                    if not default_location:
                        raise ValueError("Source warehouse has no default location")
                    source_location_id = default_location.id
                balance = self._get_balance(session, company_id, product_id, source_warehouse_id, source_location_id, lot_number, serial_number)
                available = Decimal(balance.quantity) if balance else Decimal("0")
                if available < quantity:
                    raise ValueError("Insufficient stock for dispatch")
                self._upsert_balance(session, company_id, product_id, source_warehouse_id, source_location_id, lot_number, serial_number, -Decimal(quantity))

            elif movement_type == "transfer":
                if not source_warehouse_id or not destination_warehouse_id:
                    raise ValueError("Both source_warehouse_id and destination_warehouse_id are required for transfer")
                if not source_location_id:
                    default_source = self.get_default_location(company_id, source_warehouse_id)
                    if not default_source:
                        raise ValueError("Source warehouse has no default location")
                    source_location_id = default_source.id
                if not destination_location_id:
                    default_destination = self.get_default_location(company_id, destination_warehouse_id)
                    if not default_destination:
                        raise ValueError("Destination warehouse has no default location")
                    destination_location_id = default_destination.id
                balance = self._get_balance(session, company_id, product_id, source_warehouse_id, source_location_id, lot_number, serial_number)
                available = Decimal(balance.quantity) if balance else Decimal("0")
                if available < quantity:
                    raise ValueError("Insufficient stock for transfer")
                self._upsert_balance(session, company_id, product_id, source_warehouse_id, source_location_id, lot_number, serial_number, -Decimal(quantity))
                self._upsert_balance(session, company_id, product_id, destination_warehouse_id, destination_location_id, lot_number, serial_number, Decimal(quantity))

            else:
                raise ValueError(f"Unsupported movement type: {movement_type}")

            movement = StockMovement(
                id=str(uuid4()),
                company_id=company_id,
                product_id=product_id,
                movement_type=movement_type,
                quantity=quantity,
                source_warehouse_id=source_warehouse_id,
                source_location_id=source_location_id,
                destination_warehouse_id=destination_warehouse_id,
                destination_location_id=destination_location_id,
                lot_number=lot_number,
                serial_number=serial_number,
                reference_type=reference_type,
                reference_id=reference_id,
                notes=notes,
                created_by=actor_email,
                created_at=datetime.utcnow(),
            )
            session.add(movement)
            self._create_audit_event(session, company_id, actor_email, f"movement.{movement_type}", "stock_movement", movement.id, {"quantity": str(quantity)})
            return movement

    def list_stock(self, company_id: str) -> list[dict]:
        with self.session_scope() as session:
            rows = (
                session.query(StockBalance, Product, Warehouse, Location)
                .join(Product, Product.id == StockBalance.product_id)
                .join(Warehouse, Warehouse.id == StockBalance.warehouse_id)
                .join(Location, Location.id == StockBalance.location_id)
                .filter(StockBalance.company_id == company_id)
                .order_by(Product.name.asc())
                .all()
            )

            result = []
            for balance, product, warehouse, location in rows:
                result.append(
                    {
                        "product_id": product.id,
                        "sku": product.sku,
                        "product_name": product.name,
                        "warehouse_id": warehouse.id,
                        "warehouse_code": warehouse.code,
                        "location_id": location.id,
                        "location_code": location.code,
                        "lot_number": balance.lot_number,
                        "serial_number": balance.serial_number,
                        "quantity": Decimal(balance.quantity),
                        "reorder_point": Decimal(product.reorder_point),
                        "min_stock": Decimal(product.min_stock),
                    }
                )
            return result

    def _set_balance(self, session, company_id: str, product_id: str, warehouse_id: str, location_id: str, lot_number: str, serial_number: str, new_quantity: Decimal):
        balance = self._get_balance(session, company_id, product_id, warehouse_id, location_id, lot_number, serial_number)
        if balance:
            balance.quantity = new_quantity
            balance.updated_at = datetime.utcnow()
            return balance

        balance = StockBalance(
            id=str(uuid4()),
            company_id=company_id,
            product_id=product_id,
            warehouse_id=warehouse_id,
            location_id=location_id,
            lot_number=lot_number,
            serial_number=serial_number,
            quantity=new_quantity,
        )
        session.add(balance)
        return balance

    def apply_adjustment(
        self,
        company_id: str,
        product_id: str,
        warehouse_id: str,
        location_id: str,
        quantity_delta: Decimal,
        actor_email: str | None = None,
        lot_number: str = "",
        serial_number: str = "",
        reference_type: str | None = None,
        reference_id: str | None = None,
        notes: str | None = None,
    ) -> StockMovement:
        with self.session_scope() as session:
            return self._apply_adjustment_in_session(
                session=session,
                company_id=company_id,
                product_id=product_id,
                warehouse_id=warehouse_id,
                location_id=location_id,
                quantity_delta=quantity_delta,
                actor_email=actor_email,
                lot_number=lot_number,
                serial_number=serial_number,
                reference_type=reference_type,
                reference_id=reference_id,
                notes=notes,
            )

    def _apply_adjustment_in_session(
        self,
        session,
        company_id: str,
        product_id: str,
        warehouse_id: str,
        location_id: str,
        quantity_delta: Decimal,
        actor_email: str | None = None,
        lot_number: str = "",
        serial_number: str = "",
        reference_type: str | None = None,
        reference_id: str | None = None,
        notes: str | None = None,
    ) -> StockMovement:
        lot_number = lot_number or ""
        serial_number = serial_number or ""
        current_balance = self._get_balance(session, company_id, product_id, warehouse_id, location_id, lot_number, serial_number)
        current_quantity = Decimal(current_balance.quantity) if current_balance else Decimal("0")
        new_quantity = current_quantity + quantity_delta
        if new_quantity < 0:
            raise ValueError("Adjustment would result in negative stock")
        self._set_balance(session, company_id, product_id, warehouse_id, location_id, lot_number, serial_number, new_quantity)

        movement = StockMovement(
            id=str(uuid4()),
            company_id=company_id,
            product_id=product_id,
            movement_type="adjustment",
            quantity=abs(quantity_delta),
            source_warehouse_id=warehouse_id if quantity_delta < 0 else None,
            source_location_id=location_id if quantity_delta < 0 else None,
            destination_warehouse_id=warehouse_id if quantity_delta > 0 else None,
            destination_location_id=location_id if quantity_delta > 0 else None,
            lot_number=lot_number,
            serial_number=serial_number,
            reference_type=reference_type,
            reference_id=reference_id,
            notes=notes,
            created_by=actor_email,
            created_at=datetime.utcnow(),
        )
        session.add(movement)
        self._create_audit_event(session, company_id, actor_email, "movement.adjustment", "stock_movement", movement.id, {"quantity_delta": str(quantity_delta)})
        return movement

    def create_cycle_count(self, company_id: str, warehouse_id: str, name: str, lines: list[dict], actor_email: str | None = None, notes: str | None = None, auto_close: bool = True) -> CycleCount:
        with self.session_scope() as session:
            cycle_count = CycleCount(
                id=str(uuid4()),
                company_id=company_id,
                warehouse_id=warehouse_id,
                name=name,
                notes=notes,
                status="open",
                created_by=actor_email,
                created_at=datetime.utcnow(),
            )
            session.add(cycle_count)
            session.flush()

            created_lines = []
            for line in lines:
                product_id = line["product_id"]
                location_id = line["location_id"]
                lot_number = line.get("lot_number", "") or ""
                serial_number = line.get("serial_number", "") or ""
                counted_quantity = Decimal(str(line["counted_quantity"]))
                balance = self._get_balance(session, company_id, product_id, warehouse_id, location_id, lot_number, serial_number)
                system_quantity = Decimal(balance.quantity) if balance else Decimal("0")
                variance = counted_quantity - system_quantity
                cycle_line = CycleCountLine(
                    id=str(uuid4()),
                    cycle_count_id=cycle_count.id,
                    product_id=product_id,
                    location_id=location_id,
                    lot_number=lot_number,
                    serial_number=serial_number,
                    system_quantity=system_quantity,
                    counted_quantity=counted_quantity,
                    variance=variance,
                    created_at=datetime.utcnow(),
                )
                session.add(cycle_line)
                created_lines.append(cycle_line)

            self._create_audit_event(session, company_id, actor_email, "cycle_count.created", "cycle_count", cycle_count.id, {"warehouse_id": warehouse_id})

            if auto_close:
                cycle_count.status = "closed"
                cycle_count.closed_at = datetime.utcnow()
                session.flush()
                for line in created_lines:
                    if Decimal(line.variance) == 0:
                        continue
                    delta = Decimal(line.variance)
                    self._apply_adjustment_in_session(
                        session=session,
                        company_id=company_id,
                        product_id=line.product_id,
                        warehouse_id=warehouse_id,
                        location_id=line.location_id,
                        quantity_delta=delta,
                        actor_email=actor_email,
                        lot_number=line.lot_number,
                        serial_number=line.serial_number,
                        reference_type="cycle_count",
                        reference_id=cycle_count.id,
                        notes=f"Cycle count adjustment for {name}",
                    )
            return cycle_count

    def get_cycle_count(self, company_id: str, count_id: str) -> CycleCount | None:
        with self.session_scope() as session:
            return session.query(CycleCount).filter(CycleCount.company_id == company_id, CycleCount.id == count_id).first()

    def list_cycle_counts(self, company_id: str) -> list[CycleCount]:
        with self.session_scope() as session:
            return session.query(CycleCount).filter(CycleCount.company_id == company_id).order_by(CycleCount.created_at.desc()).all()

    def list_cycle_count_lines(self, count_id: str) -> list[CycleCountLine]:
        with self.session_scope() as session:
            return session.query(CycleCountLine).filter(CycleCountLine.cycle_count_id == count_id).order_by(CycleCountLine.created_at.asc()).all()

    def close_cycle_count(self, company_id: str, count_id: str, actor_email: str | None = None) -> CycleCount:
        with self.session_scope() as session:
            cycle_count = session.query(CycleCount).filter(CycleCount.company_id == company_id, CycleCount.id == count_id).first()
            if not cycle_count:
                raise ValueError("Cycle count not found")
            if cycle_count.status == "closed":
                return cycle_count

            lines = session.query(CycleCountLine).filter(CycleCountLine.cycle_count_id == count_id).all()
            for line in lines:
                if Decimal(line.variance) == 0:
                    continue
                delta = Decimal(line.variance)
                self._apply_adjustment_in_session(
                    session=session,
                    company_id=company_id,
                    product_id=line.product_id,
                    warehouse_id=cycle_count.warehouse_id,
                    location_id=line.location_id,
                    quantity_delta=delta,
                    actor_email=actor_email,
                    lot_number=line.lot_number,
                    serial_number=line.serial_number,
                    reference_type="cycle_count",
                    reference_id=cycle_count.id,
                    notes=f"Cycle count close for {cycle_count.name}",
                )

            cycle_count.status = "closed"
            cycle_count.closed_at = datetime.utcnow()
            self._create_audit_event(session, company_id, actor_email, "cycle_count.closed", "cycle_count", cycle_count.id, {"line_count": len(lines)})
            return cycle_count

    def get_overview(self, company_id: str) -> dict:
        with self.session_scope() as session:
            product_count = session.query(func.count(Product.id)).filter(Product.company_id == company_id).scalar() or 0
            warehouse_count = session.query(func.count(Warehouse.id)).filter(Warehouse.company_id == company_id).scalar() or 0
            location_count = session.query(func.count(Location.id)).filter(Location.company_id == company_id).scalar() or 0
            stock_count = session.query(func.count(StockBalance.id)).filter(StockBalance.company_id == company_id).scalar() or 0
            total_quantity = session.query(func.coalesce(func.sum(StockBalance.quantity), 0)).filter(StockBalance.company_id == company_id).scalar() or 0

            low_stock_items = 0
            stock_rows = self.list_stock(company_id)
            for row in stock_rows:
                if row["quantity"] <= row["reorder_point"]:
                    low_stock_items += 1

            return {
                "company_id": company_id,
                "companies": 1,
                "products": int(product_count),
                "warehouses": int(warehouse_count),
                "locations": int(location_count),
                "stock_lines": int(stock_count),
                "low_stock_items": int(low_stock_items),
                "total_quantity": Decimal(str(total_quantity)),
            }

    def execute_safe_select(self, company_id: str, sql: str, limit: int = 200) -> list[dict]:
        """Execute a read-only SELECT with basic safety checks.

        - Rejects non-SELECT statements and statements with multiple statements.
        - Rejects common write/DDL keywords.
        - Ensures a `LIMIT` is present (appends one if missing).
        Returns list of dict rows.
        """
        s = (sql or "").strip()
        if not s:
            raise ValueError("Empty SQL")

        # Disallow semicolons (multiple statements)
        if ";" in s:
            raise ValueError("Multiple statements are not allowed")

        # Disallow SQL comment markers or UNION which may be used for injection
        if "--" in s or "/*" in s or "*/" in s or re.search(r"(?i)\bunion\b", s):
            raise ValueError("Potentially unsafe SQL (comments/UNION) detected")

        # Must be a SELECT
        if not re.match(r"(?i)^\s*select\b", s):
            raise ValueError("Only SELECT queries are allowed")

        # Disallow write/DDL keywords
        if re.search(r"(?i)\b(insert|update|delete|alter|create|drop|truncate|merge)\b", s):
            raise ValueError("Write or DDL statements are not allowed")

        # Ensure LIMIT
        if not re.search(r"(?i)\blimit\b", s):
            s = f"{s} LIMIT {int(limit)}"

        # Parameterize all single-quoted literals to avoid injection
        literals = re.findall(r"'((?:\\'|[^'])*?)'", s)
        params = {}
        for i, lit in enumerate(literals):
            pname = f"p{i}"
            # replace only first occurrence each time to keep mapping
            s = s.replace(f"'{lit}'", f":{pname}", 1)
            params[pname] = lit.replace("\\'", "'")

        with self.session_scope() as session:
            result = session.execute(text(s), params)
            try:
                rows = [dict(r) for r in result.mappings().all()]
            except Exception:
                rows = [dict(r) for r in result.fetchall()]
        return rows