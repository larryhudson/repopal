"""GitHub installation service"""
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from repopal.models.service_connection import (
    ServiceConnection,
    ServiceType,
    ConnectionStatus
)
from repopal.core.service_manager import ServiceConnectionManager

def handle_installation_event(
    db: Session,
    payload: Dict[str, Any],
    service_manager: "ServiceConnectionManager"
) -> Optional[ServiceConnection]:
    """Handle GitHub App installation event"""
    from flask import current_app
    
    # Extract installation data
    installation = payload.get('installation', {})
    installation_id = installation.get('id')
    account = installation.get('account', {})
    action = payload.get('action')
    repositories = payload.get('repositories', [])

    # Only handle new installations
    if action != 'created':
        current_app.logger.info(
            f"Ignoring installation {action} event",
            extra={'installation_id': installation_id}
        )
        return None
    
    current_app.logger.info(
        "Handling installation event",
        extra={
            'installation_id': installation_id,
            'account': account,
            'action': action,
            'repository_count': len(repositories),
            'repository_names': [repo.get('full_name') for repo in repositories],
            'permissions': installation.get('permissions'),
            'events': installation.get('events')
        }
    )
    
    if not installation_id:
        current_app.logger.error("No installation ID in payload")
        return None
        
    try:
        current_app.logger.info(
            "Creating organization for installation",
            extra={
                'account_login': account.get('login'),
                'account_id': account.get('id'),
                'account_type': account.get('type')
            }
        )
        
        # Create organization first
        from repopal.models import Organization
        org = Organization(
            name=account.get('login'),
            github_org_id=str(account.get('id')),
            settings={
                'type': account.get('type'),
                'url': account.get('url')
            }
        )
        db.add(org)
        db.flush()  # Get the org ID
        
        current_app.logger.info(
            "Organization created successfully",
            extra={
                'org_id': str(org.id),
                'org_name': org.name
            }
        )

        # Create service connection using manager
        connection = ServiceConnection(
            organization_id=org.id,
            service_type=ServiceType.GITHUB_APP,
            status=ConnectionStatus.ACTIVE,
            settings={
                'installation_id': installation_id,
                'account_id': account.get('id'),
                'account_login': account.get('login'),
                'account_type': account.get('type'),
                'repository_selection': installation.get('repository_selection'),
                'app_id': payload.get('app_id')
            }
        )
        
        current_app.logger.info(
            "Creating service connection",
            extra={
                'installation_id': installation_id,
                'account_login': account.get('login'),
                'service_type': ServiceType.GITHUB_APP.value
            }
        )
        
        db.add(connection)
        db.commit()
        
        current_app.logger.info(
            "Service connection created successfully",
            extra={'connection_id': str(connection.id)}
        )
        
    except Exception as e:
        current_app.logger.error(
            "Failed to create service connection",
            extra={
                'error': str(e),
                'installation_id': installation_id,
                'account_login': account.get('login')
            }
        )
        db.rollback()
        raise
    
    return connection
