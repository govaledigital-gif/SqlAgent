from hashlib import sha256
import json
from uuid import uuid4
from datetime import datetime

from app.config.settings import settings
from app.infrastructure.cache_service import CacheService
from app.infrastructure.security_logger import SecurityLogger
from app.infrastructure.inventory_repository import InventoryRepository
from app.domain.inventory import AuditEvent
import re
import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = SecurityLogger(__name__)


class LLMService:
    """Minimal LLM service with local-mode heuristics and Redis caching.

    This implementation is intentionally simple: in development it returns
    heuristic suggestions (no external API calls). In a production setup
    this class should be extended to call the configured LLM provider
    with proper anonymization, rate-limiting and cost controls.
    """

    def __init__(self):
        self.cache = CacheService()
        try:
            self.repo = InventoryRepository()
        except Exception:
            self.repo = None

    def _cache_key(self, company_id: str, user_email: str, sql: str) -> str:
        h = sha256(sql.encode("utf-8")).hexdigest()
        return f"llm:sql_opt:{company_id}:{user_email}:{h}"

    def optimize_sql(self, sql: str, company_id: str, user_email: str) -> dict:
        """Return an optimization suggestion for the provided SQL.

        Currently uses a local heuristic (development-friendly). Results are
        cached in Redis and an audit event is recorded if DB access is available.
        """
        key = self._cache_key(company_id, user_email, sql)
        try:
            cached = self.cache.get(key)
            if cached:
                logger.info("LLMService: cache hit for sql optimize")
                return json.loads(cached)
        except Exception:
            cached = None

        # Try provider if configured
        # Basic anonymization: remove email addresses
        anon_sql = re.sub(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", "[REDACTED_EMAIL]", sql)

        result = None
        if settings.LLM_PROVIDER.lower() == "google":
            # prefer company api key if available
            api_key = None
            try:
                if self.repo:
                    comp = self.repo.get_company(company_id)
                    api_key = getattr(comp, "ai_api_key", None)
            except Exception:
                api_key = None

            if api_key or settings.GOOGLE_API_KEY:
                try:
                    result = self._call_google_generate(anon_sql, company_id=company_id, user_email=user_email, api_key=api_key or settings.GOOGLE_API_KEY)
                except Exception as e:
                    logger.warning(f"LLMService: google call failed, falling back to local heuristics: {str(e)}")

        # Fallback to simple heuristics if provider not used or failed
        if not result:
            suggested = anon_sql
            explanation_msgs = []
            if "SELECT *" in anon_sql.upper():
                suggested = anon_sql.upper().replace("SELECT *", "SELECT <columns> /* specify columns instead of * */")
                explanation_msgs.append("Avoid SELECT *: specify required columns to reduce I/O and improve query plans.")
            else:
                explanation_msgs.append("No simple rewrite detected. Consider adding indexes on frequently filtered columns.")

            result = {
                "original": sql,
                "suggested_sql": suggested,
                "explanation": " ".join(explanation_msgs),
            }

        # Cache result
        try:
            self.cache.set(key, json.dumps(result))
        except Exception:
            logger.warning("LLMService: failed to write cache")

        # Record an audit event (best-effort)
        if self.repo:
            try:
                with self.repo.session_scope() as session:
                    event = AuditEvent(
                        id=str(uuid4()),
                        company_id=company_id or "-",
                        actor_email=user_email,
                        action="ai.sql_optimize.request",
                        entity_type="sql_optimize",
                        entity_id=None,
                        metadata_json=json.dumps({"sql_hash": sha256(sql.encode("utf-8")).hexdigest()}),
                        created_at=datetime.utcnow(),
                    )
                    session.add(event)
            except Exception as e:
                logger.warning(f"LLMService: audit failed: {str(e)}")

        return result

    @retry(reraise=True, stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10), retry=retry_if_exception_type(Exception))
    def _call_google_generate(self, prompt: str, company_id: str | None = None, user_email: str | None = None, api_key: str | None = None) -> dict:
        """Call Google Generative API (Gemini/text-bison) using REST API key.

        The implementation uses a simple REST call and returns a dict with
        keys: original, suggested_sql, explanation.
        """
        api_key = api_key or settings.GOOGLE_API_KEY
        model = settings.GOOGLE_MODEL or "text-bison@001"

        # Construct endpoint - using generativelanguage endpoint
        url = f"https://generativelanguage.googleapis.com/v1beta2/models/{model}:generateText?key={api_key}"

        # Request a JSON structured response to ease parsing.
        instructions = (
            "You are a SQL optimization assistant.\n"
            "Analyze the SQL query and return a JSON object with the following keys: \n"
            "  - suggested_sql: the improved SQL (if no change, return a cleaned up version)\n"
            "  - explanation: a short explanation of the changes and potential risks\n"
            "  - index_suggestions: an array of index suggestions (column names and reason)\n"
            "  - confidence: a numeric confidence estimate 0-1\n\n"
            "Output ONLY valid JSON. If you cannot produce JSON, still provide a concise textual answer.\n\n"
            f"SQL:\n{prompt}\n"
        )

        payload = {
            "prompt": {"text": instructions},
            "temperature": 0.0,
            "maxOutputTokens": 512,
        }

        headers = {"Content-Type": "application/json"}
        resp = requests.post(url, json=payload, headers=headers, timeout=settings.LLM_TIMEOUT_SECONDS)
        resp.raise_for_status()
        data = resp.json()

        # Parse generative response - attempt robust extraction
        text = ""
        if isinstance(data, dict):
            # Try multiple keys depending on API shape
            if "candidates" in data and isinstance(data["candidates"], list) and data["candidates"]:
                text = data["candidates"][0].get("content", "")
            elif "output" in data and isinstance(data["output"], list):
                # Some formats return output list with text
                text = " ".join([o.get("content", "") for o in data.get("output", []) if isinstance(o, dict)])
            else:
                # Fallback: stringify
                text = data.get("result", "") or json.dumps(data)

        # Try to extract JSON from the model output
        suggested_sql = text
        explanation = ""
        index_suggestions = []
        confidence = None

        try:
            # Attempt to find a JSON substring in the returned text
            m = re.search(r"\{.*\}", text, re.DOTALL)
            if m:
                obj = json.loads(m.group(0))
            else:
                # If response looks like a single candidate with content
                obj = json.loads(text)

            suggested_sql = obj.get("suggested_sql", suggested_sql)
            explanation = obj.get("explanation", "")
            index_suggestions = obj.get("index_suggestions", [])
            confidence = obj.get("confidence")
        except Exception:
            # Fallback: leave text as suggested_sql and attempt simple split
            split_tokens = ["\nExplanation:", "\nExplanation", "\nReason:", "\n-- Explanation"]
            for t in split_tokens:
                if t in text:
                    parts = text.split(t, 1)
                    suggested_sql = parts[0].strip()
                    explanation = parts[1].strip()
                    break

        # Estimate tokens and cost (best-effort)
        try:
            tokens = self._estimate_tokens(instructions, text)
            price = float(settings.TOKEN_PRICE_PER_1K or 0.0)
            cost = (tokens / 1000.0) * price
            cost_cents = int(round(cost * 100))
            # record usage
            if company_id or user_email:
                self._record_usage(company_id or "-", user_email or "-", tokens, cost_cents)
        except Exception:
            tokens = 0
            cost_cents = 0

        return {
            "original": prompt,
            "suggested_sql": suggested_sql,
            "explanation": explanation,
            "index_suggestions": index_suggestions,
            "confidence": confidence,
            "_estimated_tokens": tokens,
            "_estimated_cost_cents": cost_cents,
        }

    def nl_to_sql(self, question: str, company_id: str, user_email: str) -> dict:
        """Convert a natural-language question into a safe SQL SELECT and provide an explanation.

        Returns a dict with keys: `sql`, `explanation`, `confidence`.
        Uses the configured provider if available, otherwise a simple local heuristic.
        """
        # Basic caching key
        key = sha256(f"nl::{company_id}::{user_email}::{question}".encode("utf-8")).hexdigest()
        cache_key = f"llm:nl:{company_id}:{user_email}:{key}"
        try:
            cached = self.cache.get(cache_key)
            if cached:
                logger.info("LLMService: cache hit for nl_to_sql")
                return json.loads(cached)
        except Exception:
            cached = None

        anon_q = re.sub(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", "[REDACTED_EMAIL]", question)

        result = None
        if settings.LLM_PROVIDER.lower() == "google" and settings.GOOGLE_API_KEY:
            try:
                # Reuse _call_google_generate but ask for SQL generation
                instructions = (
                    "You are a helpful assistant that converts natural language questions about an inventory database into a safe single SELECT SQL statement.\n"
                    "Return ONLY valid JSON with keys: sql (the SELECT statement), explanation (brief), confidence (0-1).\n"
                    f"Question: {anon_q}\n"
                )
                # Call the same endpoint but with different prompt
                resp = self._call_google_generate(instructions, company_id=company_id, user_email=user_email)
                # _call_google_generate returns suggested_sql/explanation/confidence
                result = {
                    "sql": resp.get("suggested_sql"),
                    "explanation": resp.get("explanation"),
                    "confidence": resp.get("confidence"),
                }
            except Exception as e:
                logger.warning(f"LLMService: google nl_to_sql failed, falling back: {str(e)}")

        if not result:
            # Very simple heuristics for common inventory questions
            q = anon_q.lower()
            explanation = "Generated by local heuristic."
            confidence = 0.2
            sql = None
            if "low stock" in q or "running low" in q or "reorder" in q:
                sql = f"SELECT p.id, p.sku, p.name, sb.quantity, p.reorder_point FROM products p JOIN stock_balance sb ON p.id = sb.product_id WHERE p.company_id = '{company_id}' AND sb.quantity <= p.reorder_point LIMIT 200"
                explanation = "List products where quantity <= reorder_point (heuristic)."
                confidence = 0.6
            elif "top" in q and ("selling" in q or "sold" in q):
                sql = f"SELECT p.id, p.sku, p.name, SUM(sm.quantity) as total FROM stock_movement sm JOIN product p ON sm.product_id = p.id WHERE sm.company_id = '{company_id}' AND sm.movement_type = 'dispatch' GROUP BY p.id ORDER BY total DESC LIMIT 50"
                explanation = "Top dispatched products (heuristic)."
                confidence = 0.4
            elif "count" in q and ("products" in q or "items" in q):
                sql = f"SELECT COUNT(1) as product_count FROM products WHERE company_id = '{company_id}' LIMIT 1"
                explanation = "Return product count for company."
                confidence = 0.5
            else:
                # Generic fallback: restrict to listing products by name match if a phrase present
                words = re.findall(r"[\\w']+", anon_q)
                if words:
                    like = "%" + "%".join(words[:5]) + "%"
                    sql = f"SELECT id, sku, name FROM products WHERE company_id = '{company_id}' AND name ILIKE '{like}' LIMIT 100"
                    explanation = "Search products by name (heuristic)."
                    confidence = 0.3
                else:
                    sql = "SELECT id, sku, name FROM products WHERE company_id = '{company_id}' LIMIT 50"

            result = {"sql": sql, "explanation": explanation, "confidence": confidence}

        # Cache
        try:
            self.cache.set(cache_key, json.dumps(result), ttl=300)
        except Exception:
            pass

        # Audit
        if self.repo:
            try:
                with self.repo.session_scope() as session:
                    event = AuditEvent(
                        id=str(uuid4()),
                        company_id=company_id or "-",
                        actor_email=user_email,
                        action="ai.nl_to_sql.request",
                        entity_type="nl_query",
                        entity_id=None,
                        metadata_json=json.dumps({"question_hash": key}),
                        created_at=datetime.utcnow(),
                    )
                    session.add(event)
            except Exception as e:
                logger.warning(f"LLMService: nl_to_sql audit failed: {str(e)}")

        return result

    def _estimate_tokens(self, *texts: str) -> int:
        """Rough token estimate: assume ~4 characters per token."""
        total_chars = 0
        for t in texts:
            if not t:
                continue
            total_chars += len(t)
        # avoid zero
        return max(0, int(total_chars / 4))

    def _record_usage(self, company_id: str, user_email: str, tokens: int, cost_cents: int):
        try:
            # increment token counters (integers)
            if tokens and self.cache:
                comp_key = f"ai:tokens:company:{company_id}"
                user_key = f"ai:tokens:user:{user_email}"
                self.cache.incr(comp_key, tokens)
                self.cache.incr(user_key, tokens)

            if cost_cents and self.cache:
                comp_cost = f"ai:cost_cents:company:{company_id}"
                user_cost = f"ai:cost_cents:user:{user_email}"
                self.cache.incr(comp_cost, cost_cents)
                self.cache.incr(user_cost, cost_cents)

            # best-effort audit log in DB
            if self.repo:
                with self.repo.session_scope() as session:
                    meta = {"tokens": tokens, "cost_cents": cost_cents}
                    event = AuditEvent(
                        id=str(uuid4()),
                        company_id=company_id or "-",
                        actor_email=user_email,
                        action="ai.usage.record",
                        entity_type="ai_usage",
                        entity_id=None,
                        metadata_json=json.dumps(meta),
                        created_at=datetime.utcnow(),
                    )
                    session.add(event)
        except Exception as e:
            logger.warning(f"LLMService: failed to record usage: {str(e)}")
