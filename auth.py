import bcrypt
import secrets
import hashlib
from datetime import datetime, timedelta
from werkzeug.security import check_password_hash
from database import execute_write, fetch_one, execute_batch


class AuthManager:
    """Handles user authentication with password hashing and session management."""
    
    @staticmethod
    def hash_password(password):
        """Hash a password using bcrypt."""
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    @staticmethod
    def verify_password(password, password_hash):
        """Verify a password against its hash."""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
        except Exception:
            return False
    
    @staticmethod
    def create_user(username, password, role='student'):
        """Create a new user with hashed password."""
        password_hash = AuthManager.hash_password(password)
        execute_write(
            """
            INSERT INTO users (username, password_hash, password, role, is_active)
            VALUES (?, ?, ?, ?, 1)
            """,
            (username, password_hash, password_hash, role)
        )
    
    @staticmethod
    def authenticate_user(username, password):
        """Authenticate a user and return user data if valid."""
        user = fetch_one(
            "SELECT id, username, role, password_hash, password FROM users WHERE username = ? ORDER BY id DESC LIMIT 1",
            (username,)
        )
        
        if not user:
            return None
        
        user_id, uname, role, password_hash, legacy_password = user
        stored_secret = password_hash or legacy_password or ''

        if not stored_secret:
            return None

        # Current bcrypt format.
        if stored_secret.startswith('$2'):
            if not AuthManager.verify_password(password, stored_secret):
                return None
        # Legacy Werkzeug hashes from previous app versions.
        elif stored_secret.startswith('pbkdf2:') or stored_secret.startswith('scrypt:'):
            if not check_password_hash(stored_secret, password):
                return None
            new_hash = AuthManager.hash_password(password)
            execute_write(
                "UPDATE users SET password_hash = ?, password = ? WHERE id = ?",
                (new_hash, new_hash, user_id)
            )
        else:
            # Very old plain text password fallback.
            if password != stored_secret:
                return None
            new_hash = AuthManager.hash_password(password)
            execute_write(
                "UPDATE users SET password_hash = ?, password = ? WHERE id = ?",
                (new_hash, new_hash, user_id)
            )
        
        return {'id': user_id, 'username': uname, 'role': role}
    
    @staticmethod
    def create_session_token(username, exam_id):
        """Create a session token for exam access."""
        token = secrets.token_urlsafe(32)
        start_time = datetime.now().isoformat()
        
        execute_write(
            """
            INSERT INTO exam_sessions (username, exam_id, session_token, start_time, is_active)
            VALUES (?, ?, ?, ?, 1)
            """,
            (username, exam_id, token, start_time)
        )
        
        return token
    
    @staticmethod
    def validate_session_token(token, exam_id):
        """Validate if a session token is valid."""
        session = fetch_one(
            """
            SELECT username, exam_id, is_active FROM exam_sessions
            WHERE session_token = ? AND exam_id = ? AND is_active = 1
            """,
            (token, exam_id)
        )
        return session is not None
    
    @staticmethod
    def end_session(token):
        """End an exam session."""
        execute_write(
            "UPDATE exam_sessions SET is_active = 0, end_time = ? WHERE session_token = ?",
            (datetime.now().isoformat(), token)
        )
    
    @staticmethod
    def create_admin_session(admin_id, ip_address, user_agent):
        """Create an admin session with security tracking."""
        session_token = secrets.token_urlsafe(32)
        created_at = datetime.now().isoformat()
        expires_at = (datetime.now() + timedelta(hours=8)).isoformat()
        
        execute_write(
            """
            INSERT INTO admin_sessions (admin_id, session_token, ip_address, user_agent, created_at, expires_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (admin_id, session_token, ip_address, user_agent, created_at, expires_at)
        )
        
        return session_token
    
    @staticmethod
    def validate_admin_session(session_token, ip_address=None):
        """Validate admin session and check if not expired."""
        session = fetch_one(
            """
            SELECT admin_id FROM admin_sessions
            WHERE session_token = ? AND expires_at > ?
            """,
            (session_token, datetime.now().isoformat())
        )
        
        if session and ip_address:
            # Optional: Check IP for additional security
            pass
        
        return session is not None
    
    @staticmethod
    def revoke_admin_session(session_token):
        """Revoke an admin session."""
        execute_write(
            "DELETE FROM admin_sessions WHERE session_token = ?",
            (session_token,)
        )
    
    @staticmethod
    def cleanup_expired_sessions():
        """Clean up expired sessions."""
        statements = [
            ("DELETE FROM admin_sessions WHERE expires_at < ?", (datetime.now().isoformat(),)),
            ("UPDATE exam_sessions SET is_active = 0 WHERE is_active = 1 AND DATE(end_time) < DATE('now')", ()),
        ]
        execute_batch(statements)
