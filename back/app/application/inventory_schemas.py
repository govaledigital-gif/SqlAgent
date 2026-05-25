from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class CompanyCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    code: str = Field(min_length=2, max_length=64)


class CompanyRead(BaseModel):
    id: str
    name: str
    code: str
    owner_email: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class CompanyMemberCreate(BaseModel):
    user_email: str = Field(min_length=3, max_length=255)
    role: str = Field(default="member", max_length=32)


class CompanyMemberRead(BaseModel):
    id: str
    company_id: str
    user_email: str
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class WarehouseCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    code: str = Field(min_length=2, max_length=64)


class WarehouseRead(BaseModel):
    id: str
    company_id: str
    name: str
    code: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class LocationCreate(BaseModel):
    warehouse_id: str
    name: str = Field(min_length=2, max_length=255)
    code: str = Field(min_length=1, max_length=64)
    location_type: str = Field(default="storage", max_length=64)
    parent_location_id: Optional[str] = None


class LocationRead(BaseModel):
    id: str
    company_id: str
    warehouse_id: str
    parent_location_id: Optional[str] = None
    name: str
    code: str
    location_type: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ProductCreate(BaseModel):
    sku: str = Field(min_length=1, max_length=128)
    name: str = Field(min_length=2, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = None
    unit_of_measure: str = Field(min_length=1, max_length=64)
    min_stock: Decimal = Decimal("0")
    max_stock: Decimal = Decimal("0")
    reorder_point: Decimal = Decimal("0")
    barcode: Optional[str] = None


class ProductRead(BaseModel):
    id: str
    company_id: str
    sku: str
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    unit_of_measure: str
    min_stock: Decimal
    max_stock: Decimal
    reorder_point: Decimal
    barcode: Optional[str] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class MovementCreate(BaseModel):
    product_id: str
    quantity: Decimal = Field(gt=0)
    source_warehouse_id: Optional[str] = None
    source_location_id: Optional[str] = None
    destination_warehouse_id: Optional[str] = None
    destination_location_id: Optional[str] = None
    lot_number: str = ""
    serial_number: str = ""
    reference_type: Optional[str] = None
    reference_id: Optional[str] = None
    notes: Optional[str] = None


class CycleCountLineCreate(BaseModel):
    product_id: str
    location_id: str
    lot_number: str = ""
    serial_number: str = ""
    counted_quantity: Decimal = Field(ge=0)


class CycleCountCreate(BaseModel):
    warehouse_id: str
    name: str = Field(min_length=2, max_length=255)
    notes: Optional[str] = None
    lines: list[CycleCountLineCreate]
    auto_close: bool = True


class CycleCountLineRead(BaseModel):
    id: str
    cycle_count_id: str
    product_id: str
    location_id: str
    lot_number: str
    serial_number: str
    system_quantity: Decimal
    counted_quantity: Decimal
    variance: Decimal
    created_at: datetime

    class Config:
        from_attributes = True


class CycleCountRead(BaseModel):
    id: str
    company_id: str
    warehouse_id: str
    name: str
    notes: Optional[str] = None
    status: str
    created_by: Optional[str] = None
    created_at: datetime
    closed_at: Optional[datetime] = None
    lines: list[CycleCountLineRead] = []

    class Config:
        from_attributes = True


class MovementRead(BaseModel):
    id: str
    company_id: str
    product_id: str
    movement_type: str
    quantity: Decimal
    source_warehouse_id: Optional[str] = None
    source_location_id: Optional[str] = None
    destination_warehouse_id: Optional[str] = None
    destination_location_id: Optional[str] = None
    lot_number: str
    serial_number: str
    reference_type: Optional[str] = None
    reference_id: Optional[str] = None
    notes: Optional[str] = None
    created_by: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class StockRead(BaseModel):
    product_id: str
    sku: str
    product_name: str
    warehouse_id: str
    warehouse_code: str
    location_id: str
    location_code: str
    lot_number: str
    serial_number: str
    quantity: Decimal
    reorder_point: Decimal
    min_stock: Decimal


class InventoryOverviewResponse(BaseModel):
    company_id: str
    companies: int
    products: int
    warehouses: int
    locations: int
    stock_lines: int
    low_stock_items: int
    total_quantity: Decimal