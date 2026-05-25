"""inventory core schema

Revision ID: 0001_inventory_core
Revises:
Create Date: 2026-05-24 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0001_inventory_core"
down_revision = None
branch_labels = None
depends_on = None


def _has_table(bind, table_name: str) -> bool:
    inspector = sa.inspect(bind)
    return inspector.has_table(table_name)


def upgrade() -> None:
    bind = op.get_bind()

    if not _has_table(bind, "companies"):
        op.create_table(
            "companies",
            sa.Column("id", sa.String(length=36), primary_key=True),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("code", sa.String(length=64), nullable=False),
            sa.Column("owner_email", sa.String(length=255), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
            sa.UniqueConstraint("code", name="uq_companies_code"),
        )
        op.create_index("ix_companies_id", "companies", ["id"])
        op.create_index("ix_companies_owner_email", "companies", ["owner_email"])

    if not _has_table(bind, "company_members"):
        op.create_table(
            "company_members",
            sa.Column("id", sa.String(length=36), primary_key=True),
            sa.Column("company_id", sa.String(length=36), sa.ForeignKey("companies.id"), nullable=False),
            sa.Column("user_email", sa.String(length=255), nullable=False),
            sa.Column("role", sa.String(length=32), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
            sa.UniqueConstraint("company_id", "user_email", name="uq_company_member"),
        )
        op.create_index("ix_company_members_company_id", "company_members", ["company_id"])
        op.create_index("ix_company_members_user_email", "company_members", ["user_email"])

    if not _has_table(bind, "warehouses"):
        op.create_table(
            "warehouses",
            sa.Column("id", sa.String(length=36), primary_key=True),
            sa.Column("company_id", sa.String(length=36), sa.ForeignKey("companies.id"), nullable=False),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("code", sa.String(length=64), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
            sa.UniqueConstraint("company_id", "code", name="uq_warehouse_company_code"),
        )
        op.create_index("ix_warehouses_company_id", "warehouses", ["company_id"])

    if not _has_table(bind, "locations"):
        op.create_table(
            "locations",
            sa.Column("id", sa.String(length=36), primary_key=True),
            sa.Column("company_id", sa.String(length=36), sa.ForeignKey("companies.id"), nullable=False),
            sa.Column("warehouse_id", sa.String(length=36), sa.ForeignKey("warehouses.id"), nullable=False),
            sa.Column("parent_location_id", sa.String(length=36), sa.ForeignKey("locations.id"), nullable=True),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("code", sa.String(length=64), nullable=False),
            sa.Column("location_type", sa.String(length=64), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
            sa.UniqueConstraint("warehouse_id", "code", name="uq_location_warehouse_code"),
        )
        op.create_index("ix_locations_company_id", "locations", ["company_id"])
        op.create_index("ix_locations_warehouse_id", "locations", ["warehouse_id"])

    if not _has_table(bind, "products"):
        op.create_table(
            "products",
            sa.Column("id", sa.String(length=36), primary_key=True),
            sa.Column("company_id", sa.String(length=36), sa.ForeignKey("companies.id"), nullable=False),
            sa.Column("sku", sa.String(length=128), nullable=False),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("category", sa.String(length=255), nullable=True),
            sa.Column("unit_of_measure", sa.String(length=64), nullable=False),
            sa.Column("min_stock", sa.Numeric(18, 4), nullable=True),
            sa.Column("max_stock", sa.Numeric(18, 4), nullable=True),
            sa.Column("reorder_point", sa.Numeric(18, 4), nullable=True),
            sa.Column("barcode", sa.String(length=128), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
            sa.UniqueConstraint("company_id", "sku", name="uq_product_company_sku"),
        )
        op.create_index("ix_products_company_id", "products", ["company_id"])
        op.create_index("ix_products_sku", "products", ["sku"])

    if not _has_table(bind, "stock_balances"):
        op.create_table(
            "stock_balances",
            sa.Column("id", sa.String(length=36), primary_key=True),
            sa.Column("company_id", sa.String(length=36), sa.ForeignKey("companies.id"), nullable=False),
            sa.Column("product_id", sa.String(length=36), sa.ForeignKey("products.id"), nullable=False),
            sa.Column("warehouse_id", sa.String(length=36), sa.ForeignKey("warehouses.id"), nullable=False),
            sa.Column("location_id", sa.String(length=36), sa.ForeignKey("locations.id"), nullable=False),
            sa.Column("lot_number", sa.String(length=120), nullable=False),
            sa.Column("serial_number", sa.String(length=120), nullable=False),
            sa.Column("quantity", sa.Numeric(18, 4), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
            sa.UniqueConstraint(
                "company_id",
                "product_id",
                "warehouse_id",
                "location_id",
                "lot_number",
                "serial_number",
                name="uq_stock_balance_scope",
            ),
        )
        op.create_index("ix_stock_balances_company_id", "stock_balances", ["company_id"])
        op.create_index("ix_stock_balances_product_id", "stock_balances", ["product_id"])

    if not _has_table(bind, "stock_movements"):
        op.create_table(
            "stock_movements",
            sa.Column("id", sa.String(length=36), primary_key=True),
            sa.Column("company_id", sa.String(length=36), sa.ForeignKey("companies.id"), nullable=False),
            sa.Column("product_id", sa.String(length=36), sa.ForeignKey("products.id"), nullable=False),
            sa.Column("movement_type", sa.String(length=32), nullable=False),
            sa.Column("quantity", sa.Numeric(18, 4), nullable=False),
            sa.Column("source_warehouse_id", sa.String(length=36), sa.ForeignKey("warehouses.id"), nullable=True),
            sa.Column("source_location_id", sa.String(length=36), sa.ForeignKey("locations.id"), nullable=True),
            sa.Column("destination_warehouse_id", sa.String(length=36), sa.ForeignKey("warehouses.id"), nullable=True),
            sa.Column("destination_location_id", sa.String(length=36), sa.ForeignKey("locations.id"), nullable=True),
            sa.Column("lot_number", sa.String(length=120), nullable=False),
            sa.Column("serial_number", sa.String(length=120), nullable=False),
            sa.Column("reference_type", sa.String(length=64), nullable=True),
            sa.Column("reference_id", sa.String(length=64), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("created_by", sa.String(length=255), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
        )
        op.create_index("ix_stock_movements_company_id", "stock_movements", ["company_id"])
        op.create_index("ix_stock_movements_product_id", "stock_movements", ["product_id"])

    if not _has_table(bind, "audit_events"):
        op.create_table(
            "audit_events",
            sa.Column("id", sa.String(length=36), primary_key=True),
            sa.Column("company_id", sa.String(length=36), nullable=False),
            sa.Column("actor_email", sa.String(length=255), nullable=True),
            sa.Column("action", sa.String(length=128), nullable=False),
            sa.Column("entity_type", sa.String(length=64), nullable=False),
            sa.Column("entity_id", sa.String(length=64), nullable=True),
            sa.Column("metadata_json", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
        )
        op.create_index("ix_audit_events_company_id", "audit_events", ["company_id"])
        op.create_index("ix_audit_events_actor_email", "audit_events", ["actor_email"])

    if not _has_table(bind, "cycle_counts"):
        op.create_table(
            "cycle_counts",
            sa.Column("id", sa.String(length=36), primary_key=True),
            sa.Column("company_id", sa.String(length=36), sa.ForeignKey("companies.id"), nullable=False),
            sa.Column("warehouse_id", sa.String(length=36), sa.ForeignKey("warehouses.id"), nullable=False),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("status", sa.String(length=32), nullable=False),
            sa.Column("created_by", sa.String(length=255), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("closed_at", sa.DateTime(), nullable=True),
        )
        op.create_index("ix_cycle_counts_company_id", "cycle_counts", ["company_id"])
        op.create_index("ix_cycle_counts_warehouse_id", "cycle_counts", ["warehouse_id"])

    if not _has_table(bind, "cycle_count_lines"):
        op.create_table(
            "cycle_count_lines",
            sa.Column("id", sa.String(length=36), primary_key=True),
            sa.Column("cycle_count_id", sa.String(length=36), sa.ForeignKey("cycle_counts.id"), nullable=False),
            sa.Column("product_id", sa.String(length=36), sa.ForeignKey("products.id"), nullable=False),
            sa.Column("location_id", sa.String(length=36), sa.ForeignKey("locations.id"), nullable=False),
            sa.Column("lot_number", sa.String(length=120), nullable=False),
            sa.Column("serial_number", sa.String(length=120), nullable=False),
            sa.Column("system_quantity", sa.Numeric(18, 4), nullable=False),
            sa.Column("counted_quantity", sa.Numeric(18, 4), nullable=False),
            sa.Column("variance", sa.Numeric(18, 4), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=True),
        )
        op.create_index("ix_cycle_count_lines_cycle_count_id", "cycle_count_lines", ["cycle_count_id"])


def downgrade() -> None:
    bind = op.get_bind()

    if _has_table(bind, "cycle_count_lines"):
        op.drop_index("ix_cycle_count_lines_cycle_count_id", table_name="cycle_count_lines")
        op.drop_table("cycle_count_lines")

    if _has_table(bind, "cycle_counts"):
        op.drop_index("ix_cycle_counts_warehouse_id", table_name="cycle_counts")
        op.drop_index("ix_cycle_counts_company_id", table_name="cycle_counts")
        op.drop_table("cycle_counts")

    if _has_table(bind, "audit_events"):
        op.drop_index("ix_audit_events_actor_email", table_name="audit_events")
        op.drop_index("ix_audit_events_company_id", table_name="audit_events")
        op.drop_table("audit_events")

    if _has_table(bind, "stock_movements"):
        op.drop_index("ix_stock_movements_product_id", table_name="stock_movements")
        op.drop_index("ix_stock_movements_company_id", table_name="stock_movements")
        op.drop_table("stock_movements")

    if _has_table(bind, "stock_balances"):
        op.drop_index("ix_stock_balances_product_id", table_name="stock_balances")
        op.drop_index("ix_stock_balances_company_id", table_name="stock_balances")
        op.drop_table("stock_balances")

    if _has_table(bind, "products"):
        op.drop_index("ix_products_sku", table_name="products")
        op.drop_index("ix_products_company_id", table_name="products")
        op.drop_table("products")

    if _has_table(bind, "locations"):
        op.drop_index("ix_locations_warehouse_id", table_name="locations")
        op.drop_index("ix_locations_company_id", table_name="locations")
        op.drop_table("locations")

    if _has_table(bind, "warehouses"):
        op.drop_index("ix_warehouses_company_id", table_name="warehouses")
        op.drop_table("warehouses")

    if _has_table(bind, "company_members"):
        op.drop_index("ix_company_members_user_email", table_name="company_members")
        op.drop_index("ix_company_members_company_id", table_name="company_members")
        op.drop_table("company_members")

    if _has_table(bind, "companies"):
        op.drop_index("ix_companies_owner_email", table_name="companies")
        op.drop_index("ix_companies_id", table_name="companies")
        op.drop_table("companies")