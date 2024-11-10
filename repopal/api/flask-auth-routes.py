"""Authentication routes for RepoPal"""

from functools import wraps

import requests
from flask import (
    Blueprint,
    current_app,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

# Create auth blueprint
auth_bp = Blueprint("auth", __name__, template_folder="../templates", url_prefix="/auth")


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)

    return decorated_function


@auth_bp.route("/login")
def login():
    """Show login page"""
    return render_template("auth/login.html")


@auth_bp.route("/github")
def github_login():
    """Initiate GitHub OAuth flow"""
    github_url = "https://github.com/login/oauth/authorize"
    params = {
        "client_id": current_app.config["GITHUB_CLIENT_ID"],
        "redirect_uri": url_for("api.auth.github_callback", _external=True),
        "scope": "repo user",
    }
    return redirect(f"{github_url}?{'&'.join(f'{k}={v}' for k,v in params.items())}")


@auth_bp.route("/github/callback")
def github_callback():
    """Handle GitHub OAuth callback"""
    code = request.args.get("code")
    if not code:
        return jsonify({"error": "No code provided"}), 400

    # Exchange code for access token
    token_request_data = {
        "client_id": current_app.config["GITHUB_CLIENT_ID"],
        "client_secret": current_app.config["GITHUB_CLIENT_SECRET"],
        "code": code,
    }
    
    current_app.logger.info(f"Exchanging code for token with data: {token_request_data}")
    
    response = requests.post(
        "https://github.com/login/oauth/access_token",
        headers={"Accept": "application/json"},
        data=token_request_data,
    )

    token_data = response.json()
    current_app.logger.info(f"Token exchange response status: {response.status_code}")
    current_app.logger.debug(f"Token exchange response data: {token_data}")
    
    if "access_token" not in token_data:
        error_msg = f"Failed to get access token. Error: {token_data.get('error_description', token_data)}"
        current_app.logger.error(error_msg)
        return jsonify({"error": error_msg}), 400

    # Get user info
    user_response = requests.get(
        "https://api.github.com/user",
        headers={
            "Authorization": f"Bearer {token_data['access_token']}",
            "Accept": "application/json",
        },
    )
    user_data = user_response.json()

    # Store in session
    session["user_id"] = user_data["id"]
    session["username"] = user_data["login"]
    session["access_token"] = token_data["access_token"]

    return redirect(url_for("api.auth.post_login"))


@auth_bp.route("/github/installed")
def github_installed():
    """Handle GitHub App installation callback"""
    installation_id = request.args.get("installation_id")
    if installation_id:
        # Store installation ID in session
        session["installation_id"] = installation_id
        return redirect(url_for("home"))
    return jsonify({"error": "No installation ID provided"}), 400


@auth_bp.route("/post-login")
@login_required
def post_login():
    """Handle post-login flow"""
    return render_template(
        "auth/install.html",
        username=session["username"],
        app_id=current_app.config["GITHUB_APP_ID"],
    )


@auth_bp.route("/logout")
def logout():
    """Log out user"""
    session.clear()
    return redirect(url_for("auth.login"))
