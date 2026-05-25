from app.domain.user import User
from app.domain.query_history import QueryHistory
from app.domain.base import Base
from app.application.auth_service import AuthService
from app.config.settings import settings
from app.infrastructure.database import create_database_engine, create_session_factory
from app.infrastructure.security_logger import SecurityLogger

logger = SecurityLogger(__name__)

class UserRepository:
    """Repository for user persistence"""
    
    def __init__(self):
        if not settings.DATABASE_URL:
            raise ValueError("DATABASE_URL must be configured")
        
        self.engine = create_database_engine()
        self.SessionLocal = create_session_factory(self.engine)
        # Crear tabla si no existe
        Base.metadata.create_all(bind=self.engine)
    
    def create_user(self, email: str, password: str, full_name: str = "") -> User:
        """Create a new user"""
        session = self.SessionLocal()
        try:
            # Verificar si el usuario ya existe
            existing = session.query(User).filter(User.email == email).first()
            if existing:
                logger.warning(f"User creation attempt for existing email: {email}")
                raise ValueError(f"User with email {email} already exists")
            
            hashed_password = AuthService.hash_password(password)
            user = User(
                email=email,
                hashed_password=hashed_password,
                full_name=full_name,
                is_active=True
            )
            session.add(user)
            session.commit()
            session.refresh(user)
            logger.info(f"User created successfully: {email}")
            return user
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            session.rollback()
            raise
        finally:
            session.close()
    
    def get_user(self, email: str) -> User:
        """Get user by email"""
        session = self.SessionLocal()
        try:
            return session.query(User).filter(User.email == email).first()
        except Exception as e:
            logger.error(f"Error getting user: {str(e)}")
            raise
        finally:
            session.close()
    
    def authenticate_user(self, email: str, password: str) -> bool:
        """Authenticate a user by email and password"""
        try:
            user = self.get_user(email)
            if not user:
                logger.warning(f"Login attempt with non-existent email: {email}")
                return False
            if not user.is_active:
                logger.warning(f"Login attempt with inactive user: {email}")
                return False
            
            is_valid = AuthService.verify_password(password, user.hashed_password)
            if is_valid:
                logger.info(f"Successful login: {email}")
            else:
                logger.warning(f"Failed login attempt: {email}")
            
            return is_valid
        except Exception as e:
            logger.error(f"Error authenticating user: {str(e)}")
            return False
