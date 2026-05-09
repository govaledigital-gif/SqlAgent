from typing import Optional
from app.domain.interfaces import SqlGeneratorInterface, SchemaRepositoryInterface
from app.infrastructure.repository import SchemaRepository
import os
import google.generativeai as genai

class SqlGeneratorService(SqlGeneratorInterface):
    """Service for SQL generation using Google Gemini"""
    
    def __init__(self, schema_repo: SchemaRepositoryInterface):
        self.schema_repo = schema_repo
        api_key = os.getenv("GOOGLE_API_KEY", "").strip()
        
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not set in environment variables")
        
        try:
            genai.configure(api_key=api_key)
            self.model = self._create_model()
        except Exception as e:
            raise ValueError(f"Failed to configure Gemini API: {str(e)}")

    def _create_model(self):
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
                    return genai.GenerativeModel(model_name)

            if available_models:
                return genai.GenerativeModel(available_models[0])
        except Exception:
            pass

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
            
            # Call Gemini API
            response = self.model.generate_content(full_prompt)
            query = response.text.strip()
            
            # Remove markdown code blocks if present
            if query.startswith("```"):
                query = query.split("```")[1]
                if query.startswith("sql"):
                    query = query[3:]
                query = query.strip()
            
            return query
        except Exception as e:
            raise Exception(f"Failed to generate SQL: {str(e)}")
    
    async def generate(self, prompt: str, schema: Optional[str] = None) -> str:
        """Interface implementation"""
        return await self.generate_sql(prompt, schema)
