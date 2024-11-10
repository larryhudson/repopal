"""Service connection and repository models"""

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.types import JSON
from sqlalchemy.orm import relationship

from repopal.models.base import Base
from repopal.models.connection_event import ConnectionEvent
from repopal.utils.crypto import CredentialEncryption


class ServiceType(str, Enum):
    """Supported service types"""

    GITHUB_APP = "github_app"
    SLACK = "slack"


class ConnectionStatus(str, Enum):
    """Service connection status"""

    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    PENDING = "pending"


class ServiceConnection(Base):
    """Service connection model for external integrations"""

    __tablename__ = "service_connections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False
    )
    service_type = Column(SQLEnum(ServiceType), nullable=False)
    status = Column(
        SQLEnum(ConnectionStatus), nullable=False, default=ConnectionStatus.PENDING
    )
    settings = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    organization = relationship("Organization", back_populates="service_connections")
    repositories = relationship(
        "Repository", back_populates="service_connection", cascade="all, delete-orphan"
    )
    credentials = relationship(
        "ServiceCredential",
        back_populates="service_connection",
        cascade="all, delete-orphan",
    )
    events = relationship(
        "ConnectionEvent",
        back_populates="service_connection",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<ServiceConnection {self.service_type} {self.organization_id}>"


class Repository(Base):
    """Repository model for GitHub repositories"""

    __tablename__ = "repositories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    service_connection_id = Column(
        UUID(as_uuid=True), ForeignKey("service_connections.id"), nullable=False
    )
    name = Column(String, nullable=False)
    github_id = Column(String, nullable=False)
    settings = Column(JSON, default=dict)
    slack_channels = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    service_connection = relationship(
        "ServiceConnection", back_populates="repositories"
    )

    def __repr__(self):
        return f"<Repository {self.name}>"


class ServiceCredential(Base):
    """Encrypted service credentials storage"""

    __tablename__ = "service_credentials"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    service_connection_id = Column(
        UUID(as_uuid=True), ForeignKey("service_connections.id"), nullable=False
    )
    credential_type = Column(
        String, nullable=False
    )  # e.g., 'access_token', 'refresh_token'
    encrypted_data = Column(String, nullable=False)
    metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    service_connection = relationship("ServiceConnection", back_populates="credentials")

    def __repr__(self):
        return (
            f"<ServiceCredential {self.credential_type} {self.service_connection_id}>"
        )

    def set_credential(self, encryption: "CredentialEncryption", value: str) -> None:
        """Encrypt and store a credential value"""
        self.encrypted_data = encryption.encrypt(value)

    def get_credential(self, encryption: "CredentialEncryption") -> str:
        """Decrypt and return the credential value"""
        return encryption.decrypt(self.encrypted_data)
