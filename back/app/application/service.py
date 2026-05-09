from typing import Optional
from app.domain.interfaces import SqlGeneratorInterface, SchemaRepositoryInterface
from app.infrastructure.repository import SchemaRepository
from app.config.settings import settings
from app.infrastructure.security_logger import SecurityLogger
import google.generativeai as genai
import asyncio

logger = SecurityLogger(__name__)

class SqlGeneratorService(SqlGeneratorInterface):
    """Service for SQL generation using Google Gemini"""
    
    def __init__(self, schema_repo: SchemaRepositoryInterface):
        self.schema_repo = schema_repo
        
        # Validar API key en settings
        api_key = settings.GOOGLE_API_KEY
        if not api_key:
            logger.error("GOOGLE_API_KEY is not configured")
            raise ValueError("GOOGLE_API_KEY is not configured in settings")
        
        try:
            genai.configure(api_key=api_key)
            self.model = self._create_model()
            logger.info(f"Gemini API initialized with model: {self.model.model_name}")
        except Exception as e:
            logger.error(f"Failed to configure Gemini API: {str(e)}")
            raise ValueError(f"Failed to configure Gemini API: {str(e)}")

    def _create_model(self):
        """Create Gemini model with fallback logic"""
        preferred_models = [
            "gemini-1.5-flash-latest",
            "gemini-1.5-flash",
            "gemini-1.5-pro-latest",
            "gemini-1.5-pro",
            "gemini-pro",
        ]

        try:
            available_models = [
                model.name.split("/", 1)[-1]
                for model in genai.list_models()
                if "generateContent" in getattr(model, "supported_generation_methods", [])
            ]

            for model_name in preferred_models:
                if model_name in available_models:
                    logger.info(f"Selected model: {model_name}")
                    return genai.GenerativeModel(model_name)

            if available_models:
                selected = available_models[0]
                logger.warning(f"Preferred models not available, using: {selected}")
                return genai.GenerativeModel(selected)
        except Exception as e:
            logger.warning(f"Error listing models, using default: {str(e)}")

        logger.info(f"Using fallback model: {preferred_models[0]}")
        return genai.GenerativeModel(preferred_models[0])
    
    async def generate_sql(self, prompt: str, schema: Optional[str] = None) -> str:
        """
        Generate optimized SQL query from natural language
        
        Args:
            prompt: Natural language description
            schema: Optional schema context
            
        Returns:
            Generated SQL query
        """
        try:
            # Validar tamaño del prompt
            if len(prompt) > settings.MAX_PROMPT_LENGTH:
                error_msg = f"Prompt exceeds maximum length of {settings.MAX_PROMPT_LENGTH}"
                logger.warning(error_msg)
                raise ValueError(error_msg)
            
            # Get schema if not provided
            if not schema:
                schema = await self.schema_repo.get_schema()
            
            # Create the full prompt
            full_prompt = f"""You are an expert SQL developer. Your task is to generate optimized MySQL queries from natural language descriptions.

Database Schema:
{schema}

User Request:
{prompt}

Generate ONLY the SQL query without any explanation or markdown formatting. Return just the raw SQL query.
For example: SELECT * FROM users WHERE age > 18;"""
            
            # Call Gemini API with timeout and retries
            logger.info("Calling Gemini API for SQL generation")
            loop = asyncio.get_event_loop()
            response = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: self.model.generate_content(full_prompt)
                ),
                timeout=settings.LLM_TIMEOUT_SECONDS
            )
            
            query = response.text.strip()
            
            # Remove markdown code blocks if present
            if query.startswith("```"):
                query = query.split("```")[1]
                if query.startswith("sql"):
                    query = query[3:]
                query = query.strip()
            
            logger.info(f"SQL generated successfully, length: {len(query)}")
            return query
        except asyncio.TimeoutError:
            error_msg = f"LLM request timed out after {settings.LLM_TIMEOUT_SECONDS} seconds"
            logger.error(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            logger.error(f"Failed to generate SQL: {str(e)}")
            raise Exception(f"Failed to generate SQL: {str(e)}")
    
    async def generate(self, prompt: str, schema: Optional[str] = None) -> str:
        """Interface implementation"""
        return await self.generate_sql(prompt, schema)
