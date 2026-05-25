from fastapi import APIRouter, Depends, HTTPException

from app.application.dependencies import get_current_user
from app.application.inventory_schemas import (
    CompanyCreate,
    CompanyMemberCreate,
    CompanyMemberRead,
    CompanyRead,
    CycleCountCreate,
    CycleCountRead,
    InventoryOverviewResponse,
    LocationCreate,
    LocationRead,
    MovementCreate,
    MovementRead,
    ProductCreate,
    ProductRead,
    StockRead,
    WarehouseCreate,
    WarehouseRead,
)
from app.application.inventory_service import InventoryService
from app.infrastructure.inventory_repository import InventoryRepository


router = APIRouter(prefix="/api/v1", tags=["Inventory"])

inventory_repository = InventoryRepository()
inventory_service = InventoryService(inventory_repository)


@router.post("/companies", response_model=CompanyRead)
def create_company(payload: CompanyCreate, current_user: str = Depends(get_current_user)):
    try:
        return inventory_service.create_company(payload.name, payload.code, current_user)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/companies", response_model=list[CompanyRead])
def list_companies(current_user: str = Depends(get_current_user)):
    return inventory_service.list_companies(current_user)


@router.get("/companies/{company_id}", response_model=CompanyRead)
def get_company(company_id: str, current_user: str = Depends(get_current_user)):
    company = inventory_service.repository.get_company(company_id, current_user)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


@router.post("/companies/{company_id}/members", response_model=CompanyMemberRead)
def add_member(company_id: str, payload: CompanyMemberCreate, current_user: str = Depends(get_current_user)):
    try:
        return inventory_service.add_member(company_id, payload.user_email, payload.role, current_user)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/companies/{company_id}/members", response_model=list[CompanyMemberRead])
def list_members(company_id: str, current_user: str = Depends(get_current_user)):
    try:
        return inventory_service.list_members(company_id, current_user)
    except ValueError as exc:
        raise HTTPException(status_code=403, detail=str(exc))


@router.post("/companies/{company_id}/warehouses", response_model=WarehouseRead)
def create_warehouse(company_id: str, payload: WarehouseCreate, current_user: str = Depends(get_current_user)):
    try:
        return inventory_service.create_warehouse(company_id, payload.name, payload.code, current_user)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/companies/{company_id}/warehouses", response_model=list[WarehouseRead])
def list_warehouses(company_id: str, current_user: str = Depends(get_current_user)):
    try:
        return inventory_service.list_warehouses(company_id, current_user)
    except ValueError as exc:
        raise HTTPException(status_code=403, detail=str(exc))


@router.post("/companies/{company_id}/locations", response_model=LocationRead)
def create_location(company_id: str, payload: LocationCreate, current_user: str = Depends(get_current_user)):
    try:
        return inventory_service.create_location(
            company_id=company_id,
            warehouse_id=payload.warehouse_id,
            name=payload.name,
            code=payload.code,
            location_type=payload.location_type,
            parent_location_id=payload.parent_location_id,
            actor_email=current_user,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/companies/{company_id}/locations", response_model=list[LocationRead])
def list_locations(company_id: str, warehouse_id: str | None = None, current_user: str = Depends(get_current_user)):
    try:
        return inventory_service.list_locations(company_id, current_user, warehouse_id)
    except ValueError as exc:
        raise HTTPException(status_code=403, detail=str(exc))


@router.post("/companies/{company_id}/products", response_model=ProductRead)
def create_product(company_id: str, payload: ProductCreate, current_user: str = Depends(get_current_user)):
    try:
        return inventory_service.create_product(company_id, current_user, **payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/companies/{company_id}/products", response_model=list[ProductRead])
def list_products(company_id: str, current_user: str = Depends(get_current_user)):
    try:
        return inventory_service.list_products(company_id, current_user)
    except ValueError as exc:
        raise HTTPException(status_code=403, detail=str(exc))


@router.get("/companies/{company_id}/stock", response_model=list[StockRead])
def list_stock(company_id: str, current_user: str = Depends(get_current_user)):
    try:
        return inventory_service.list_stock(company_id, current_user)
    except ValueError as exc:
        raise HTTPException(status_code=403, detail=str(exc))


@router.get("/companies/{company_id}/overview", response_model=InventoryOverviewResponse)
def inventory_overview(company_id: str, current_user: str = Depends(get_current_user)):
    try:
        return inventory_service.get_overview(company_id, current_user)
    except ValueError as exc:
        raise HTTPException(status_code=403, detail=str(exc))


@router.post("/companies/{company_id}/movements/receipts", response_model=MovementRead)
def record_receipt(company_id: str, payload: MovementCreate, current_user: str = Depends(get_current_user)):
    try:
        return inventory_service.record_movement(company_id, current_user, "receipt", payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/companies/{company_id}/movements/shipments", response_model=MovementRead)
def record_shipment(company_id: str, payload: MovementCreate, current_user: str = Depends(get_current_user)):
    try:
        return inventory_service.record_movement(company_id, current_user, "dispatch", payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/companies/{company_id}/movements/transfers", response_model=MovementRead)
def record_transfer(company_id: str, payload: MovementCreate, current_user: str = Depends(get_current_user)):
    try:
        return inventory_service.record_movement(company_id, current_user, "transfer", payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/companies/{company_id}/cycle-counts", response_model=CycleCountRead)
def create_cycle_count(company_id: str, payload: CycleCountCreate, current_user: str = Depends(get_current_user)):
    try:
        count = inventory_service.create_cycle_count(
            company_id=company_id,
            actor_email=current_user,
            warehouse_id=payload.warehouse_id,
            name=payload.name,
            notes=payload.notes,
            lines=[line.model_dump() for line in payload.lines],
            auto_close=payload.auto_close,
        )
        lines = inventory_service.repository.list_cycle_count_lines(count.id)
        count.lines = lines
        return count
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/companies/{company_id}/cycle-counts", response_model=list[CycleCountRead])
def list_cycle_counts(company_id: str, current_user: str = Depends(get_current_user)):
    try:
        counts = inventory_service.list_cycle_counts(company_id, current_user)
        for count in counts:
            count.lines = inventory_service.repository.list_cycle_count_lines(count.id)
        return counts
    except ValueError as exc:
        raise HTTPException(status_code=403, detail=str(exc))


@router.get("/companies/{company_id}/cycle-counts/{count_id}", response_model=CycleCountRead)
def get_cycle_count(company_id: str, count_id: str, current_user: str = Depends(get_current_user)):
    try:
        count = inventory_service.get_cycle_count(company_id, current_user, count_id)
        if not count:
            raise HTTPException(status_code=404, detail="Cycle count not found")
        count.lines = inventory_service.repository.list_cycle_count_lines(count.id)
        return count
    except ValueError as exc:
        raise HTTPException(status_code=403, detail=str(exc))


@router.post("/companies/{company_id}/cycle-counts/{count_id}/close", response_model=CycleCountRead)
def close_cycle_count(company_id: str, count_id: str, current_user: str = Depends(get_current_user)):
    try:
        count = inventory_service.close_cycle_count(company_id, current_user, count_id)
        count.lines = inventory_service.repository.list_cycle_count_lines(count.id)
        return count
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))