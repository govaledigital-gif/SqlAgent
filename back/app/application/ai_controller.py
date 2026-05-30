from fastapi import APIRouter, Depends, HTTPException

from app.application.dependencies import get_current_user
from app.application.ai_schemas import SQLOptimizeRequest, SQLOptimizeResponse, NLQueryRequest, NLQueryResponse
from app.infrastructure.llm_service import LLMService
from app.infrastructure.cache_service import CacheService
from app.config.settings import settings

router = APIRouter(prefix="/api/v1/ai", tags=["AI"])

llm_service = LLMService()
cache = CacheService()


@router.post("/sql-optimize", response_model=SQLOptimizeResponse)
def sql_optimize(payload: SQLOptimizeRequest, current_user: str = Depends(get_current_user)):
    # Fetch company and enforce ai_enabled and quotas
    company = None
    try:
        if llm_service.repo:
            company = llm_service.repo.get_company(payload.company_id, current_user)
            if not company:
                raise HTTPException(status_code=403, detail="User not authorized for this company")
            if not getattr(company, "ai_enabled", False):
                raise HTTPException(status_code=403, detail="AI features are disabled for this company")
            try:
                comp_quota = int(getattr(company, "ai_quota_per_hour", None) or 0)
            except Exception:
                comp_quota = 0
        else:
            comp_quota = 0
    except HTTPException:
        raise
    except Exception:
        comp_quota = 0

    # Quota enforcement (per-user and per-company per-hour)
    try:
        user_key = f"quota:ai:{payload.company_id}:{current_user}"
        comp_key = f"quota:ai:company:{payload.company_id}"
        user_count = cache.incr(user_key, 1, ttl=3600)
        comp_count = cache.incr(comp_key, 1, ttl=3600)
        if settings.AI_QUOTA_PER_HOUR and user_count > settings.AI_QUOTA_PER_HOUR:
            raise HTTPException(status_code=429, detail="AI quota exceeded for this hour (user)")
        if comp_quota and comp_count > comp_quota:
            raise HTTPException(status_code=429, detail="AI quota exceeded for this hour (company)")
    except HTTPException:
        raise
    except Exception:
        # If cache is unavailable, proceed but log internally
        pass

    try:
        return llm_service.optimize_sql(payload.sql, payload.company_id, current_user)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/nl-query", response_model=NLQueryResponse)
def nl_query(payload: NLQueryRequest, current_user: str = Depends(get_current_user)):
    # Fetch company and enforce ai_enabled and quotas
    company = None
    try:
        if llm_service.repo:
            company = llm_service.repo.get_company(payload.company_id, current_user)
            if not company:
                raise HTTPException(status_code=403, detail="User not authorized for this company")
            if not getattr(company, "ai_enabled", False):
                raise HTTPException(status_code=403, detail="AI features are disabled for this company")
            try:
                comp_quota = int(getattr(company, "ai_quota_per_hour", None) or 0)
            except Exception:
                comp_quota = 0
        else:
            comp_quota = 0
    except HTTPException:
        raise
    except Exception:
        comp_quota = 0

    # Quota enforcement (per-user and per-company per-hour)
    try:
        user_key = f"quota:ai:{payload.company_id}:{current_user}"
        comp_key = f"quota:ai:company:{payload.company_id}"
        user_count = cache.incr(user_key, 1, ttl=3600)
        comp_count = cache.incr(comp_key, 1, ttl=3600)
        if settings.AI_QUOTA_PER_HOUR and user_count > settings.AI_QUOTA_PER_HOUR:
            raise HTTPException(status_code=429, detail="AI quota exceeded for this hour (user)")
        if comp_quota and comp_count > comp_quota:
            raise HTTPException(status_code=429, detail="AI quota exceeded for this hour (company)")
    except HTTPException:
        raise
    except Exception:
        pass

    try:
        nl = llm_service.nl_to_sql(payload.question, payload.company_id, current_user)
        sql = nl.get("sql")
        explanation = nl.get("explanation")
        confidence = nl.get("confidence")

        # Execute safely
        repo = llm_service.repo
        if not repo:
            raise HTTPException(status_code=500, detail="Database repository not available")

        try:
            rows = repo.execute_safe_select(payload.company_id, sql, limit=200)
        except ValueError as ve:
            raise HTTPException(status_code=400, detail=str(ve))

        return {"sql": sql, "explanation": explanation, "confidence": confidence, "results": rows}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/usage/{company_id}")
def usage(company_id: str, current_user: str = Depends(get_current_user)):
    # Return simple aggregated usage metrics from Redis (best-effort)
    try:
        comp_tokens = int(cache.get(f"ai:tokens:company:{company_id}") or 0)
        comp_cost_cents = int(cache.get(f"ai:cost_cents:company:{company_id}") or 0)
        return {"company_id": company_id, "tokens": comp_tokens, "cost_cents": comp_cost_cents}
    except Exception:
        raise HTTPException(status_code=500, detail="Unable to fetch usage")
