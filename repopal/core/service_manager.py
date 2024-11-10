"""Service connection management module"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from repopal.models import (
    ServiceConnection,
    ServiceType,
    ConnectionStatus,
    ServiceCredential,
    Organization
)
from repopal.utils.crypto import CredentialEncryption
from repopal.core.health import HealthCheckFactory, HealthStatus, HealthCheckResult

class ServiceConnectionManager:
    """Manages service connection lifecycle and operations"""

    def __init__(self, db: Session, encryption: CredentialEncryption):
        self.db = db
        self.encryption = encryption

    async def create_connection(
        self,
        organization_id: str,
        service_type: ServiceType,
        settings: dict,
        credentials: dict
    ) -> ServiceConnection:
        """Create a new service connection with credentials"""
        try:
            # Create connection
            connection = ServiceConnection(
                organization_id=organization_id,
                service_type=service_type,
                status=ConnectionStatus.PENDING,
                settings=settings
            )
            self.db.add(connection)
            
            # Store credentials
            for cred_type, value in credentials.items():
                credential = ServiceCredential(
                    service_connection_id=connection.id,
                    credential_type=cred_type
                )
                credential.set_credential(self.encryption, value)
                self.db.add(credential)
            
            await self.db.commit()
            return connection
            
        except SQLAlchemyError as e:
            await self.db.rollback()
            raise ValueError(f"Failed to create service connection: {str(e)}")

    async def get_connection(
        self,
        connection_id: str
    ) -> Optional[ServiceConnection]:
        """Get a service connection by ID"""
        return await self.db.query(ServiceConnection).get(connection_id)

    async def list_organization_connections(
        self,
        organization_id: str
    ) -> List[ServiceConnection]:
        """List all connections for an organization"""
        return await self.db.query(ServiceConnection).filter(
            ServiceConnection.organization_id == organization_id
        ).all()

    async def update_connection_status(
        self,
        connection_id: str,
        status: ConnectionStatus
    ) -> ServiceConnection:
        """Update connection status"""
        connection = await self.get_connection(connection_id)
        if not connection:
            raise ValueError(f"Connection {connection_id} not found")
        
        connection.status = status
        await self.db.commit()
        return connection

    async def delete_connection(self, connection_id: str) -> None:
        """Delete a service connection and its credentials"""
        connection = await self.get_connection(connection_id)
        if not connection:
            raise ValueError(f"Connection {connection_id} not found")
        
        await self.db.delete(connection)
        await self.db.commit()

    async def check_connection_health(
        self,
        connection_id: str
    ) -> HealthCheckResult:
        """Check health of a service connection"""
        connection = await self.get_connection(connection_id)
        if not connection:
            raise ValueError(f"Connection {connection_id} not found")

        # Get appropriate health checker
        checker = HealthCheckFactory.get_checker(connection.service_type)
        
        # Run health check
        result = await checker.check_health(connection_id)
        
        # Update connection status based on health
        new_status = ConnectionStatus.ACTIVE if result.status == HealthStatus.HEALTHY else ConnectionStatus.ERROR
        await self.update_connection_status(connection_id, new_status)
        
        return result

    async def validate_connection_settings(
        self,
        service_type: ServiceType,
        settings: Dict[str, Any]
    ) -> None:
        """Validate service-specific connection settings"""
        if service_type == ServiceType.GITHUB_APP:
            required = {"app_id", "installation_id"}
            if not all(key in settings for key in required):
                raise ValueError(f"Missing required GitHub App settings: {required}")
                
        elif service_type == ServiceType.SLACK:
            required = {"team_id", "bot_id"}
            if not all(key in settings for key in required):
                raise ValueError(f"Missing required Slack settings: {required}")

    async def rotate_credentials(
        self,
        connection_id: str,
        new_credentials: dict
    ) -> None:
        """Rotate connection credentials"""
        connection = await self.get_connection(connection_id)
        if not connection:
            raise ValueError(f"Connection {connection_id} not found")

        try:
            # Delete existing credentials
            await self.db.query(ServiceCredential).filter(
                ServiceCredential.service_connection_id == connection_id
            ).delete()

            # Store new credentials
            for cred_type, value in new_credentials.items():
                credential = ServiceCredential(
                    service_connection_id=connection_id,
                    credential_type=cred_type
                )
                credential.set_credential(self.encryption, value)
                self.db.add(credential)

            await self.db.commit()

        except SQLAlchemyError as e:
            await self.db.rollback()
            raise ValueError(f"Failed to rotate credentials: {str(e)}")
