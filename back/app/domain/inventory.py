from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Numeric, String, Text, UniqueConstraint

from app.domain.base import Base


class Company(Base):
    __tablename__ = "companies"

    id = Column(String(36), primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    code = Column(String(64), nullable=False, unique=True, index=True)
    owner_email = Column(String(255), nullable=False, index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CompanyMember(Base):
    __tablename__ = "company_members"

    id = Column(String(36), primary_key=True, index=True)
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False, index=True)
    user_email = Column(String(255), nullable=False, index=True)
    role = Column(String(32), nullable=False, default="member")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("company_id", "user_email", name="uq_company_member"),
    )


class Warehouse(Base):
    __tablename__ = "warehouses"

    id = Column(String(36), primary_key=True, index=True)
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    code = Column(String(64), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("company_id", "code", name="uq_warehouse_company_code"),
    )


class Location(Base):
    __tablename__ = "locations"

    id = Column(String(36), primary_key=True, index=True)
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False, index=True)
    warehouse_id = Column(String(36), ForeignKey("warehouses.id"), nullable=False, index=True)
    parent_location_id = Column(String(36), ForeignKey("locations.id"), nullable=True, index=True)
    name = Column(String(255), nullable=False)
    code = Column(String(64), nullable=False)
    location_type = Column(String(64), nullable=False, default="storage")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("warehouse_id", "code", name="uq_location_warehouse_code"),
    )


class Product(Base):
    __tablename__ = "products"

    id = Column(String(36), primary_key=True, index=True)
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False, index=True)
    sku = Column(String(128), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(255), nullable=True)
    unit_of_measure = Column(String(64), nullable=False)
    min_stock = Column(Numeric(18, 4), default=0)
    max_stock = Column(Numeric(18, 4), default=0)
    reorder_point = Column(Numeric(18, 4), default=0)
    barcode = Column(String(128), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("company_id", "sku", name="uq_product_company_sku"),
    )


class StockBalance(Base):
    __tablename__ = "stock_balances"

    id = Column(String(36), primary_key=True, index=True)
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False, index=True)
    product_id = Column(String(36), ForeignKey("products.id"), nullable=False, index=True)
    warehouse_id = Column(String(36), ForeignKey("warehouses.id"), nullable=False, index=True)
    location_id = Column(String(36), ForeignKey("locations.id"), nullable=False, index=True)
    lot_number = Column(String(120), nullable=False, default="")
    serial_number = Column(String(120), nullable=False, default="")
    quantity = Column(Numeric(18, 4), nullable=False, default=0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint(
            "company_id",
            "product_id",
            "warehouse_id",
            "location_id",
            "lot_number",
            "serial_number",
            name="uq_stock_balance_scope",
        ),
    )


class StockMovement(Base):
    __tablename__ = "stock_movements"

    id = Column(String(36), primary_key=True, index=True)
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False, index=True)
    product_id = Column(String(36), ForeignKey("products.id"), nullable=False, index=True)
    movement_type = Column(String(32), nullable=False)
    quantity = Column(Numeric(18, 4), nullable=False)
    source_warehouse_id = Column(String(36), ForeignKey("warehouses.id"), nullable=True, index=True)
    source_location_id = Column(String(36), ForeignKey("locations.id"), nullable=True, index=True)
    destination_warehouse_id = Column(String(36), ForeignKey("warehouses.id"), nullable=True, index=True)
    destination_location_id = Column(String(36), ForeignKey("locations.id"), nullable=True, index=True)
    lot_number = Column(String(120), nullable=False, default="")
    serial_number = Column(String(120), nullable=False, default="")
    reference_type = Column(String(64), nullable=True)
    reference_id = Column(String(64), nullable=True)
    notes = Column(Text, nullable=True)
    created_by = Column(String(255), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(String(36), primary_key=True, index=True)
    company_id = Column(String(36), nullable=False, index=True)
    actor_email = Column(String(255), nullable=True, index=True)
    action = Column(String(128), nullable=False)
    entity_type = Column(String(64), nullable=False)
    entity_id = Column(String(64), nullable=True)
    metadata_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class CycleCount(Base):
    __tablename__ = "cycle_counts"

    id = Column(String(36), primary_key=True, index=True)
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False, index=True)
    warehouse_id = Column(String(36), ForeignKey("warehouses.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    notes = Column(Text, nullable=True)
    status = Column(String(32), nullable=False, default="open")
    created_by = Column(String(255), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    closed_at = Column(DateTime, nullable=True, index=True)


class CycleCountLine(Base):
    __tablename__ = "cycle_count_lines"

    id = Column(String(36), primary_key=True, index=True)
    cycle_count_id = Column(String(36), ForeignKey("cycle_counts.id"), nullable=False, index=True)
    product_id = Column(String(36), ForeignKey("products.id"), nullable=False, index=True)
    location_id = Column(String(36), ForeignKey("locations.id"), nullable=False, index=True)
    lot_number = Column(String(120), nullable=False, default="")
    serial_number = Column(String(120), nullable=False, default="")
    system_quantity = Column(Numeric(18, 4), nullable=False, default=0)
    counted_quantity = Column(Numeric(18, 4), nullable=False, default=0)
    variance = Column(Numeric(18, 4), nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)