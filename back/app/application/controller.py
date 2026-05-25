from fastapi import APIRouter, HTTPException, Depends, status
from app.application.schemas import (
    GenerateSqlRequest, GenerateSqlResponse, SchemaResponse,
    LoginRequest, RegisterRequest, TokenResponse, UserResponse,
    QueryHistoryResponse, QueryHistoryListResponse
)
from app.application.service import SqlGeneratorService
from app.application.auth_service import AuthService
from app.application.dependencies import get_current_user
from app.config.settings import settings
from app.infrastructure.cache_service import CacheService
import secrets
from app.application.sql_validator import SqlValidator
from fastapi import Request, Header
from app.infrastructure.repository import SchemaRepository
from app.infrastructure.user_repository import UserRepository
from app.infrastructure.query_history_repository import QueryHistoryRepository

router = APIRouter(prefix="/api/v1", tags=["SQL Generator"])
# Initialize UserRepository first to ensure users table is created before QueryHistoryRepository
user_repo = UserRepository()
history_repo = QueryHistoryRepository()
cache = CacheService()

# Dependency injection
def get_schema_repository():
    return SchemaRepository()

def get_sql_service(schema_repo: SchemaRepository = Depends(get_schema_repository)):
    try:
        return SqlGeneratorService(schema_repo)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=f"Service initialization error: {str(e)}")

# ============ AUTH ENDPOINTS ============

@router.post("/auth/register", response_model=TokenResponse, tags=["Auth"])
async def register(request: RegisterRequest):
    """Register a new user"""
    # Disallow public registration if configured
    if not settings.ALLOW_REGISTRATION:
        raise HTTPException(status_code=403, detail="Registration is disabled. Contact an administrator.")

    # If invite tokens are required, validate provided token
    if settings.REQUIRE_INVITE_TOKEN:
        token = request.invite_token
        if not token:
            raise HTTPException(status_code=400, detail="invite_token is required")
        key = f"invite:{token}"
        if not cache.get(key):
            raise HTTPException(status_code=400, detail="Invalid or expired invite token")

    try:
        user = user_repo.create_user(request.email, request.password, request.full_name)
        token = AuthService.create_token(user.email)
        # If used an invite token, delete it so it cannot be reused
        if settings.REQUIRE_INVITE_TOKEN and request.invite_token:
            cache.delete(f"invite:{request.invite_token}")
        return TokenResponse(access_token=token, email=user.email)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/auth/login", response_model=TokenResponse, tags=["Auth"])
async def login(request: LoginRequest):
    """Login user and return JWT token"""
    # Check for lockout
    fail_key = f"login:fail:{request.email}"
    lock_key = f"login:lock:{request.email}"
    if cache.get(lock_key):
        raise HTTPException(status_code=403, detail="Account locked due to multiple failed login attempts. Try later.")

    if not user_repo.authenticate_user(request.email, request.password):
        # Increment failure counter
        count = cache.incr(fail_key, 1, ttl=settings.LOGIN_LOCKOUT_SECONDS)
        if count >= settings.LOGIN_MAX_ATTEMPTS:
            # set a lock key
            cache.set(lock_key, "1", ttl=settings.LOGIN_LOCKOUT_SECONDS)
            cache.delete(fail_key)
            raise HTTPException(status_code=403, detail="Account locked due to multiple failed login attempts. Try later.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Successful login: clear failure counter
    cache.delete(fail_key)
    token = AuthService.create_token(request.email)
    return TokenResponse(access_token=token, email=request.email)


@router.post("/auth/invite", tags=["Auth"])
async def create_invite(request: Request, authorization: str = Header(None)):
    """Create an invite token (admin only). Provide header Authorization: Bearer <ADMIN_API_TOKEN>"""
    # Validate admin token
    if not settings.ADMIN_API_TOKEN:
        raise HTTPException(status_code=403, detail="Invite generation is not configured")

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    token = authorization.split(" ", 1)[1].strip()
    if token != settings.ADMIN_API_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid admin token")

    # generate invite token
    invite = secrets.token_urlsafe(32)
    cache.set(f"invite:{invite}", "1", ttl=settings.INVITE_TOKEN_TTL_SECONDS)
    return {"invite_token": invite, "ttl": settings.INVITE_TOKEN_TTL_SECONDS}


@router.get("/auth/me", response_model=UserResponse, tags=["Auth"])
async def get_current_user_info(current_user: str = Depends(get_current_user)):
    """Get current authenticated user info"""
    user = user_repo.get_user(current_user)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse(email=user.email, full_name=user.full_name, is_active=user.is_active)

# ============ SQL GENERATION ENDPOINTS (Protected) ============

@router.post("/generate-sql", response_model=GenerateSqlResponse)
async def generate_sql(
    request: GenerateSqlRequest,
    current_user: str = Depends(get_current_user),
    service: SqlGeneratorService = Depends(get_sql_service)
):
    """Generate SQL query from natural language prompt"""
    generated_query = None
    error = None
    is_valid = False
    
    try:
        if not request.prompt.strip():
            raise HTTPException(status_code=400, detail="Prompt cannot be empty")
        
        query = await service.generate_sql(request.prompt, request.schema)
        generated_query = query
        
        # Validar la query generada
        is_valid, error_msg = SqlValidator.validate(query)
        if not is_valid:
            error = f"Generated query failed validation: {error_msg}. Please try with a different request."
            # Guardar en historial como inválida
            history_repo.save_query(
                user_email=current_user,
                prompt=request.prompt,
                generated_sql=query,
                is_valid=False,
                error_message=error_msg
            )
            return GenerateSqlResponse(query="", error=error)
        
        # Sanitizar la query
        sanitized_query = SqlValidator.sanitize(query)
        
        # Guardar en historial como válida
        history_repo.save_query(
            user_email=current_user,
            prompt=request.prompt,
            generated_sql=sanitized_query,
            is_valid=True
        )
        
        return GenerateSqlResponse(query=sanitized_query)
    except Exception as e:
        error_msg = str(e)
        # Guardar el error en historial
        if current_user:
            history_repo.save_query(
                user_email=current_user,
                prompt=request.prompt,
                generated_sql=generated_query,
                is_valid=False,
                error_message=error_msg
            )
        raise HTTPException(status_code=400, detail=error_msg)

@router.get("/schema", response_model=SchemaResponse)
async def get_schema(
    current_user: str = Depends(get_current_user),
    schema_repo: SchemaRepository = Depends(get_schema_repository)
):
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
    current_user: str = Depends(get_current_user),
    schema_repo: SchemaRepository = Depends(get_schema_repository)
):
    """Get specific table schema"""
    try:
        schema = await schema_repo.get_table_schema(table_name)
        return {"table": table_name, "schema": schema}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/history")
async def get_user_history(
    current_user: str = Depends(get_current_user),
    limit: int = 50
):
    """Get query history for current user"""
    try:
        queries = history_repo.get_user_history(current_user, limit)
        return {
            "total": len(queries),
            "queries": [
                {
                    "id": q.id,
                    "user_email": q.user_email,
                    "prompt": q.prompt,
                    "generated_sql": q.generated_sql,
                    "is_valid": q.is_valid,
                    "error_message": q.error_message,
                    "created_at": q.created_at
                }
                for q in queries
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/history/{query_id}")
async def get_query_detail(
    query_id: str,
    current_user: str = Depends(get_current_user)
):
    """Get detail of a specific query from history"""
    try:
        query = history_repo.get_query(query_id)
        if not query:
            raise HTTPException(status_code=404, detail="Query not found")
        
        # Verificar que el usuario sea el dueño
        if query.user_email != current_user:
            raise HTTPException(status_code=403, detail="Access denied")
        
        return {
            "id": query.id,
            "user_email": query.user_email,
            "prompt": query.prompt,
            "generated_sql": query.generated_sql,
            "is_valid": query.is_valid,
            "error_message": query.error_message,
            "created_at": query.created_at
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/history/{query_id}")
async def delete_query_from_history(
    query_id: str,
    current_user: str = Depends(get_current_user)
):
    """Delete a query from history"""
    try:
        query = history_repo.get_query(query_id)
        if not query:
            raise HTTPException(status_code=404, detail="Query not found")
        
        # Verificar que el usuario sea el dueño
        if query.user_email != current_user:
            raise HTTPException(status_code=403, detail="Access denied")
        
        if history_repo.delete_query(query_id):
            return {"message": "Query deleted successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete query")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
