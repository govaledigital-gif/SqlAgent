from fastapi import APIRouter, HTTPException, Depends, status, Request, Header
from app.application.schemas import (
    LoginRequest, RegisterRequest, TokenResponse, UserResponse
)
from app.application.auth_service import AuthService
from app.application.dependencies import get_current_user
from app.config.settings import settings
from app.infrastructure.cache_service import CacheService
from app.infrastructure.user_repository import UserRepository

router = APIRouter(prefix="/api/v1", tags=["Auth"])
# Initialize UserRepository
user_repo = UserRepository()
cache = CacheService()

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
# AI/SQL generation endpoints removed — inventory-only MVP

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
