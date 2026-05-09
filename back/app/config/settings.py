from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    """Application settings"""
    database_url: str = "mysql+pymysql://root:root@localhost/projects_db"
    openai_api_key: str = ""
    app_name: str = "SQL Architect"
    debug: bool = False
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()
