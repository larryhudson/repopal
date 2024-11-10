"""Authentication routes for RepoPal"""
from typing import Optional
from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2AuthorizationCodeBearer
import httpx

from repopal.core.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])

oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl="https://github.com/login/oauth/authorize",
    tokenUrl="https://github.com/login/oauth/access_token",
)

@router.get("/login")
async def login():
    """Show login page"""
    return RedirectResponse(url="/auth/github")

@router.get("/github")
async def github_login():
    """Initiate GitHub OAuth flow"""
    params = {
        "client_id": settings.GITHUB_CLIENT_ID,
        "redirect_uri": f"{settings.API_V1_STR}/auth/github/callback",
        "scope": "repo user",
    }
    github_url = "https://github.com/login/oauth/authorize"
    redirect_url = f"{github_url}?{'&'.join(f'{k}={v}' for k,v in params.items())}"
    return RedirectResponse(url=redirect_url)

@router.get("/github/callback")
async def github_callback(code: str):
    """Handle GitHub OAuth callback"""
    if not code:
        raise HTTPException(status_code=400, detail="No code provided")

    token_request_data = {
        "client_id": settings.GITHUB_CLIENT_ID,
        "client_secret": settings.GITHUB_CLIENT_SECRET,
        "code": code,
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://github.com/login/oauth/access_token",
            headers={"Accept": "application/json"},
            data=token_request_data,
        )
        
        token_data = response.json()
        
        if "access_token" not in token_data:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to get access token: {token_data.get('error_description', str(token_data))}"
            )

        # Get user info
        user_response = await client.get(
            "https://api.github.com/user",
            headers={
                "Authorization": f"Bearer {token_data['access_token']}",
                "Accept": "application/json",
            },
        )
        user_data = user_response.json()

    return RedirectResponse(url="/auth/post-login")

@router.get("/github/installed")
async def github_installed(installation_id: Optional[str] = None):
    """Handle GitHub App installation callback"""
    if not installation_id:
        raise HTTPException(status_code=400, detail="No installation ID provided")
    
    return RedirectResponse(url="/")

@router.get("/post-login")
async def post_login():
    """Handle post-login flow"""
    return {
        "app_id": settings.GITHUB_APP_ID,
        "message": "Please complete GitHub App installation"
    }

@router.get("/logout")
async def logout(response: Response):
    """Log out user"""
    response.delete_cookie("session")
    return RedirectResponse(url="/auth/login")
