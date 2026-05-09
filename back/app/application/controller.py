from fastapi import APIRouter, HTTPException, Depends
from app.application.schemas import GenerateSqlRequest, GenerateSqlResponse, SchemaResponse
from app.application.service import SqlGeneratorService
from app.infrastructure.repository import SchemaRepository

router = APIRouter(prefix="/api/v1", tags=["SQL Generator"])

# Dependency injection
def get_schema_repository():
    return SchemaRepository()

def get_sql_service(schema_repo: SchemaRepository = Depends(get_schema_repository)):
    try:
        return SqlGeneratorService(schema_repo)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=f"Service initialization error: {str(e)}")

@router.post("/generate-sql", response_model=GenerateSqlResponse)
async def generate_sql(
    request: GenerateSqlRequest,
    service: SqlGeneratorService = Depends(get_sql_service)
):
    """Generate SQL query from natural language prompt"""
    try:
        if not request.prompt.strip():
            raise HTTPException(status_code=400, detail="Prompt cannot be empty")
        
        query = await service.generate_sql(request.prompt, request.schema)
        return GenerateSqlResponse(query=query)
    except Exception as e:
        error_msg = str(e)
        raise HTTPException(status_code=400, detail=error_msg)

@router.get("/schema", response_model=SchemaResponse)
async def get_schema(schema_repo: SchemaRepository = Depends(get_schema_repository)):
    """Get database schema"""
    try:
        tables = await schema_repo.list_tables()
        schema = await schema_repo.get_schema()
        return SchemaResponse(tables=tables, schema=schema)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/schema/{table_name}")
async def get_table_schema(
    table_name: str,
    schema_repo: SchemaRepository = Depends(get_schema_repository)
):
    """Get specific table schema"""
    try:
        schema = await schema_repo.get_table_schema(table_name)
        return {"table": table_name, "schema": schema}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/tables")
async def list_tables(schema_repo: SchemaRepository = Depends(get_schema_repository)):
    """List all available tables"""
    try:
        tables = await schema_repo.list_tables()
        return {"tables": tables}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
