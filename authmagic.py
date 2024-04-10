from canvasmagic import get_user_profile
from config import save_config
from datetime import datetime
from flask import request

def register_token(token, app, bcrypt, config_lock):
    """Registers or updates a token in the application's configuration.

    This function generates a hash for the given token, checks if it already
    exists in the app's configuration, and accordingly updates the last verified
    time or registers a new token. It only registers tokens not associated with
    student emails and saves the updated configuration back to the file.

    Args:
        token (str): The token to be registered or updated.
        app (Flask): The Flask application instance containing the configuration.
        bcrypt (Bcrypt): An instance of Flask-Bcrypt for password hashing.
        config_lock (threading.RLock): A lock to ensure thread-safe operations on
            the app's configuration.

    Returns:
        str: 'registered' if a new token was successfully added,
             'updated' if an existing token's last verified time was updated,
             False if the token is associated with a student email or if the
             profile response status code is not 200.
    """
    token_hash = bcrypt.generate_password_hash(token).decode("utf-8")

    with config_lock:
        stored_tokens = app.config["SETTINGS"]["base"]["canvas"]["tokens"]
        response = get_user_profile(token)

        if response.status_code == 200:
            json_data = response.json()
            if "student" in json_data["primary_email"]:
                return False
            
            for entry in stored_tokens:
                if bcrypt.check_password_hash(entry["hash"], token):
                    entry["last_verified"] = datetime.now().isoformat()
                    save_config(app, config_lock)
                    return "updated"
            
            entry = {
                "hash": token_hash,
                "sortable_name": json_data["sortable_name"],
                "last_verified" : datetime.now().isoformat(),
            }
            stored_tokens.append(entry)
            save_config(app, config_lock)
            return "registered"
        else:
            return False

def get_token_from_header():
    """Extracts the token from the Authorization header.

    This function parses the incoming request to extract a bearer token
    from the Authorization header. The expected format of the header is
    "Bearer <token>", where <token> represents the actual token string.

    Returns:
        str or None: The token as a string if the Authorization header is present
        and correctly formatted. Returns None if the header is missing, or not
        formatted as expected.
    """
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        return auth_header[7:]
    return None

def check_token(token, app, bcrypt):
    stored_tokens = app.config["SETTINGS"]["base"]["canvas"]["tokens"]

    if len(stored_tokens) >= 1:
        for field in stored_tokens:
            if bcrypt.check_password_hash(field["hash"], token):
                return True
    return False
