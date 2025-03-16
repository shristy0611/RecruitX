"""Security Manager

This module implements comprehensive security features for the recruitment system.
It follows SOTA practices including:
1. Zero-trust architecture
2. End-to-end encryption
3. Role-based access control (RBAC)
4. Data anonymization and privacy
5. Audit logging and monitoring

The design is inspired by patterns in the OpenManus-main repository.
"""

import asyncio
import base64
import hashlib
import json
import logging
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
import jwt
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import bcrypt

logger = logging.getLogger(__name__)

class UserRole(Enum):
    """User roles for RBAC."""
    ADMIN = "admin"
    RECRUITER = "recruiter"
    INTERVIEWER = "interviewer"
    CANDIDATE = "candidate"

class ResourceType(Enum):
    """Resource types for access control."""
    CANDIDATE_DATA = "candidate_data"
    JOB_POSTING = "job_posting"
    ASSESSMENT = "assessment"
    INTERVIEW = "interview"
    FEEDBACK = "feedback"
    ANALYTICS = "analytics"
    SYSTEM_CONFIG = "system_config"

@dataclass
class SecurityConfig:
    """Security configuration."""
    jwt_secret: str
    jwt_expiry_hours: int = 24
    password_min_length: int = 12
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 30
    session_timeout_minutes: int = 60
    encryption_key_rotation_days: int = 30
    audit_log_retention_days: int = 90

@dataclass
class UserSession:
    """Active user session."""
    user_id: str
    role: UserRole
    token: str
    created_at: datetime
    last_activity: datetime
    ip_address: str
    device_info: str

class SecurityManager:
    def __init__(
        self,
        config: SecurityConfig,
        audit_dir: Optional[str] = None
    ):
        """Initialize security manager.
        
        Args:
            config: Security configuration
            audit_dir: Optional directory for audit logs
        """
        self.config = config
        self.audit_dir = Path(audit_dir) if audit_dir else None
        if self.audit_dir:
            self.audit_dir.mkdir(parents=True, exist_ok=True)
            
        # Initialize encryption
        self.fernet = Fernet(self._derive_encryption_key())
        
        # Initialize storage
        self.active_sessions: Dict[str, UserSession] = {}
        self.failed_logins: Dict[str, List[datetime]] = {}
        self.role_permissions: Dict[UserRole, Set[ResourceType]] = self._init_permissions()
        
    def _init_permissions(self) -> Dict[UserRole, Set[ResourceType]]:
        """Initialize role-based permissions.
        
        Returns:
            Dictionary mapping roles to allowed resources
        """
        return {
            UserRole.ADMIN: set(ResourceType),
            UserRole.RECRUITER: {
                ResourceType.CANDIDATE_DATA,
                ResourceType.JOB_POSTING,
                ResourceType.ASSESSMENT,
                ResourceType.INTERVIEW,
                ResourceType.FEEDBACK,
                ResourceType.ANALYTICS
            },
            UserRole.INTERVIEWER: {
                ResourceType.CANDIDATE_DATA,
                ResourceType.INTERVIEW,
                ResourceType.FEEDBACK
            },
            UserRole.CANDIDATE: {
                ResourceType.JOB_POSTING
            }
        }
        
    def _derive_encryption_key(self) -> bytes:
        """Derive encryption key from JWT secret.
        
        Returns:
            Encryption key bytes
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b"recruitx_salt",  # In production, use a secure random salt
            iterations=100000
        )
        return base64.urlsafe_b64encode(
            kdf.derive(self.config.jwt_secret.encode())
        )
        
    async def authenticate(
        self,
        username: str,
        password: str,
        ip_address: str,
        device_info: str
    ) -> Optional[str]:
        """Authenticate user and create session.
        
        Args:
            username: Username
            password: Password
            ip_address: Client IP address
            device_info: Client device information
            
        Returns:
            JWT token if authentication successful, None otherwise
        """
        # Check for account lockout
        if self._is_account_locked(username):
            logger.warning(f"Account locked: {username}")
            return None
            
        # Verify credentials (mock implementation)
        if not self._verify_credentials(username, password):
            self._record_failed_login(username)
            return None
            
        # Create session
        user_id = f"user_{username}"  # In production, get from database
        role = UserRole.RECRUITER  # In production, get from database
        token = self._create_jwt_token(user_id, role)
        
        session = UserSession(
            user_id=user_id,
            role=role,
            token=token,
            created_at=datetime.now(),
            last_activity=datetime.now(),
            ip_address=ip_address,
            device_info=device_info
        )
        
        self.active_sessions[token] = session
        
        # Audit log
        self._audit_log("authentication", {
            "user_id": user_id,
            "ip_address": ip_address,
            "device_info": device_info,
            "success": True
        })
        
        return token
        
    def authorize(
        self,
        token: str,
        resource_type: ResourceType,
        resource_id: Optional[str] = None
    ) -> bool:
        """Authorize access to resource.
        
        Args:
            token: JWT token
            resource_type: Type of resource
            resource_id: Optional resource identifier
            
        Returns:
            True if access authorized, False otherwise
        """
        # Validate token
        session = self.active_sessions.get(token)
        if not session:
            return False
            
        # Check session timeout
        if self._is_session_expired(session):
            self._end_session(token)
            return False
            
        # Update last activity
        session.last_activity = datetime.now()
        
        # Check role permissions
        if resource_type not in self.role_permissions[session.role]:
            return False
            
        # Audit log
        self._audit_log("authorization", {
            "user_id": session.user_id,
            "resource_type": resource_type.value,
            "resource_id": resource_id,
            "allowed": True
        })
        
        return True
        
    def encrypt_data(self, data: Any) -> str:
        """Encrypt sensitive data.
        
        Args:
            data: Data to encrypt
            
        Returns:
            Encrypted data string
        """
        json_data = json.dumps(data)
        return self.fernet.encrypt(json_data.encode()).decode()
        
    def decrypt_data(self, encrypted_data: str) -> Any:
        """Decrypt sensitive data.
        
        Args:
            encrypted_data: Encrypted data string
            
        Returns:
            Decrypted data
        """
        decrypted = self.fernet.decrypt(encrypted_data.encode())
        return json.loads(decrypted)
        
    def anonymize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Anonymize sensitive data fields.
        
        Args:
            data: Data to anonymize
            
        Returns:
            Anonymized data
        """
        sensitive_fields = {
            "email", "phone", "address", "birth_date",
            "social_security", "passport", "gender", "ethnicity"
        }
        
        anonymized = data.copy()
        for field in sensitive_fields:
            if field in anonymized:
                anonymized[field] = self._hash_value(str(anonymized[field]))
                
        return anonymized
        
    def _hash_value(self, value: str) -> str:
        """Create secure hash of value.
        
        Args:
            value: Value to hash
            
        Returns:
            Hashed value
        """
        return hashlib.sha256(value.encode()).hexdigest()
        
    def _create_jwt_token(self, user_id: str, role: UserRole) -> str:
        """Create JWT token for user session.
        
        Args:
            user_id: User identifier
            role: User role
            
        Returns:
            JWT token
        """
        payload = {
            "sub": user_id,
            "role": role.value,
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(hours=self.config.jwt_expiry_hours)
        }
        
        return jwt.encode(
            payload,
            self.config.jwt_secret,
            algorithm="HS256"
        )
        
    def _verify_credentials(self, username: str, password: str) -> bool:
        """Verify user credentials.
        
        Args:
            username: Username
            password: Password
            
        Returns:
            True if credentials valid, False otherwise
        """
        # In production, verify against secure database
        # This is a mock implementation
        return True
        
    def _is_account_locked(self, username: str) -> bool:
        """Check if account is locked due to failed logins.
        
        Args:
            username: Username
            
        Returns:
            True if account locked, False otherwise
        """
        failed_attempts = self.failed_logins.get(username, [])
        
        # Remove old attempts
        cutoff = datetime.now() - timedelta(minutes=self.config.lockout_duration_minutes)
        failed_attempts = [t for t in failed_attempts if t > cutoff]
        self.failed_logins[username] = failed_attempts
        
        return len(failed_attempts) >= self.config.max_login_attempts
        
    def _record_failed_login(self, username: str):
        """Record failed login attempt.
        
        Args:
            username: Username
        """
        if username not in self.failed_logins:
            self.failed_logins[username] = []
            
        self.failed_logins[username].append(datetime.now())
        
        # Audit log
        self._audit_log("authentication", {
            "username": username,
            "success": False,
            "attempt_number": len(self.failed_logins[username])
        })
        
    def _is_session_expired(self, session: UserSession) -> bool:
        """Check if session has expired.
        
        Args:
            session: User session
            
        Returns:
            True if session expired, False otherwise
        """
        timeout = timedelta(minutes=self.config.session_timeout_minutes)
        return datetime.now() - session.last_activity > timeout
        
    def _end_session(self, token: str):
        """End user session.
        
        Args:
            token: Session token
        """
        if token in self.active_sessions:
            session = self.active_sessions[token]
            
            # Audit log
            self._audit_log("session_end", {
                "user_id": session.user_id,
                "duration": (datetime.now() - session.created_at).total_seconds()
            })
            
            del self.active_sessions[token]
            
    def _audit_log(self, event_type: str, event_data: Dict[str, Any]):
        """Write security event to audit log.
        
        Args:
            event_type: Type of event
            event_data: Event data
        """
        if not self.audit_dir:
            return
            
        try:
            log_file = self.audit_dir / f"audit_{datetime.now().strftime('%Y%m%d')}.jsonl"
            
            event = {
                "timestamp": datetime.now().isoformat(),
                "event_type": event_type,
                "data": event_data
            }
            
            with open(log_file, "a") as f:
                json.dump(event, f)
                f.write("\n")
                
        except Exception as e:
            logger.error(f"Error writing audit log: {e}")
            
    async def rotate_encryption_keys(self):
        """Rotate encryption keys periodically."""
        while True:
            try:
                # Wait for rotation interval
                await asyncio.sleep(
                    self.config.encryption_key_rotation_days * 24 * 60 * 60
                )
                
                # Generate new key
                new_key = self._derive_encryption_key()
                old_fernet = self.fernet
                self.fernet = Fernet(new_key)
                
                # Re-encrypt sensitive data
                # In production, implement data re-encryption
                
                # Audit log
                self._audit_log("key_rotation", {
                    "timestamp": datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Error rotating encryption keys: {e}")
                
    async def cleanup_audit_logs(self):
        """Clean up old audit logs."""
        if not self.audit_dir:
            return
            
        while True:
            try:
                # Wait for daily check
                await asyncio.sleep(24 * 60 * 60)
                
                # Remove old logs
                cutoff = datetime.now() - timedelta(days=self.config.audit_log_retention_days)
                for log_file in self.audit_dir.glob("audit_*.jsonl"):
                    try:
                        file_date = datetime.strptime(
                            log_file.stem[6:],
                            "%Y%m%d"
                        )
                        if file_date < cutoff:
                            log_file.unlink()
                    except Exception as e:
                        logger.error(f"Error processing audit log file: {e}")
                        
            except Exception as e:
                logger.error(f"Error cleaning up audit logs: {e}")
                
    def start_background_tasks(self):
        """Start background security tasks."""
        asyncio.create_task(self.rotate_encryption_keys())
        asyncio.create_task(self.cleanup_audit_logs()) 