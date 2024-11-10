from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from repopal.models.service_connection import (
    ServiceConnection,
    Repository,
    ServiceCredential,
    ConnectionStatus,
)
from repopal.repositories.base import BaseRepository


class ServiceConnectionRepository(BaseRepository[ServiceConnection]):
    """Repository for managing service connections"""

    def __init__(self):
        super().__init__(ServiceConnection)

    def get_by_organization(
        self, db: Session, organization_id: UUID
    ) -> List[ServiceConnection]:
        """Get all service connections for an organization"""
        return (
            db.query(self.model)
            .filter(ServiceConnection.organization_id == organization_id)
            .all()
        )

    def get_active_connections(self, db: Session) -> List[ServiceConnection]:
        """Get all active service connections"""
        return (
            db.query(self.model)
            .filter(ServiceConnection.status == ConnectionStatus.ACTIVE)
            .all()
        )


class RepositoryRepository(BaseRepository[Repository]):
    """Repository for managing repositories"""

    def __init__(self):
        super().__init__(Repository)

    def get_by_connection(
        self, db: Session, service_connection_id: UUID
    ) -> List[Repository]:
        """Get all repositories for a service connection"""
        return (
            db.query(self.model)
            .filter(Repository.service_connection_id == service_connection_id)
            .all()
        )

    def get_by_github_id(self, db: Session, github_id: str) -> Optional[Repository]:
        """Get repository by GitHub ID"""
        return (
            db.query(self.model)
            .filter(Repository.github_id == github_id)
            .first()
        )


class ServiceCredentialRepository(BaseRepository[ServiceCredential]):
    """Repository for managing service credentials"""

    def __init__(self):
        super().__init__(ServiceCredential)

    def get_by_connection_and_type(
        self,
        db: Session,
        service_connection_id: UUID,
        credential_type: str,
    ) -> Optional[ServiceCredential]:
        """Get credential by connection ID and type"""
        return (
            db.query(self.model)
            .filter(
                ServiceCredential.service_connection_id == service_connection_id,
                ServiceCredential.credential_type == credential_type,
            )
            .first()
        )
