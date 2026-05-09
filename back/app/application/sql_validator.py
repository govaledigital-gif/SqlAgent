import sqlparse
from sqlparse.sql import IdentifierList, Identifier, Where, Comparison
from typing import Tuple

class SqlValidator:
    """Service for validating SQL queries"""
    
    # Comandos bloqueados
    DANGEROUS_COMMANDS = [
        "DROP", "DELETE", "TRUNCATE", "ALTER", "CREATE", 
        "GRANT", "REVOKE", "INSERT", "UPDATE"
    ]
    
    # Solo permitimos SELECT en el MVP
    ALLOWED_COMMANDS = ["SELECT"]
    
    @staticmethod
    def validate(query: str) -> Tuple[bool, str]:
        """
        Validate a SQL query for security and syntax.
        Returns (is_valid, error_message)
        """
        if not query or not query.strip():
            return False, "Query cannot be empty"
        
        try:
            # Parsear la query
            parsed = sqlparse.parse(query)
            if not parsed:
                return False, "Invalid SQL syntax"
            
            statement = parsed[0]
            
            # Obtener el tipo de comando
            stmt_type = statement.get_type().upper()
            
            # Validar que sea un comando permitido
            if stmt_type not in SqlValidator.ALLOWED_COMMANDS:
                return False, f"Command '{stmt_type}' is not allowed. Only SELECT queries are supported."
            
            # Verificar que no haya comandos peligrosos en la query
            tokens = [token.ttype for token in statement.tokens]
            token_values = [str(token).strip().upper() for token in statement.tokens]
            
            for dangerous in SqlValidator.DANGEROUS_COMMANDS:
                if dangerous in token_values:
                    return False, f"Command '{dangerous}' is not allowed for security reasons."
            
            # Validar sintaxis básica
            if not SqlValidator._validate_syntax(statement):
                return False, "Invalid SQL syntax"
            
            return True, ""
        
        except Exception as e:
            return False, f"SQL validation error: {str(e)}"
    
    @staticmethod
    def _validate_syntax(statement) -> bool:
        """Basic syntax validation"""
        # Verificar que tenga al menos una cláusula SELECT
        has_select = False
        for token in statement.tokens:
            if token.ttype is None and token.get_type() == "SELECT":
                has_select = True
                break
            if str(token).strip().upper() == "SELECT":
                has_select = True
                break
        
        return has_select
    
    @staticmethod
    def sanitize(query: str) -> str:
        """Basic sanitization (remove comments, normalize whitespace)"""
        # Remover comentarios
        parsed = sqlparse.parse(query)
        if not parsed:
            return query
        
        statement = parsed[0]
        
        # Reconstruir sin comentarios
        tokens_clean = []
        for token in statement.tokens:
            if token.ttype not in (sqlparse.tokens.Comment.Single, 
                                   sqlparse.tokens.Comment.Multiline,
                                   sqlparse.tokens.Newline):
                tokens_clean.append(str(token))
        
        result = "".join(tokens_clean)
        # Normalizar espacios
        result = " ".join(result.split())
        return result.strip()
