from canvasmagic import get_user_profile
from config import save_config
from datetime import datetime

def register_token(response, app, bcrypt, config_lock):
    """Registers a new token if it doesn't already exist.

    This function first checks if the token is already registered by calling 
    `check_token`. If not, it retrieves the user profile associated with the 
    token. If the retrieval is successful and returns a 200 status code, the 
    function generates a bcrypt hash of the token, stores it along with the 
    user's sortable name and the current timestamp into the application's 
    configuration, and then saves the configuration.

    Args:
        response: The response object containing the token to be registered.
        app: The Flask application instance for the configuration.
        bcrypt: The bcrypt object for hashing tokens.
        config_lock: A threading.Lock object to ensure thread-safe 
                     modifications to the configuration.

    Returns:
        bool: True if the token was successfully registered or if the 
              configuration was successfully saved, False otherwise.
    """    
    token = bcrypt.generate_password_hash(response["token"]).decode("utf-8")
    
    if not check_token(response, app, bcrypt):
        stored_tokens = app.config["SETTINGS"]["base"]["canvas"]["tokens"]
        response = get_user_profile(response["token"])    
        if response.status_code == 200:
            json_data = response.json()
            if "student" in json_data["primary_email"]:
                return False
            print(json_data)
            entry = {
                "hash": token,
                "sortable_name": json_data["sortable_name"],
                "last_verified" : datetime.now().isoformat(),
            }
            stored_tokens.append(entry)
            return save_config(app, config_lock)
        else:
            return False

def check_token(response, app, bcrypt):
    """Checks if a given token is already registered.

    Iterates through the stored tokens in the application's configuration. 
    Utilizes bcrypt to safely compare the given token against the stored 
    bcrypt hashes. If a match is found, it indicates that the token has 
    already been registered.

    Args:
        response: The response object containing the token to check.
        app: The Flask application instance for accessing the configuration.
        bcrypt: The bcrypt object for hash verification.

    Returns:
        bool: True if the token is already registered, False otherwise.
    """
    stored_tokens = app.config["SETTINGS"]["base"]["canvas"]["tokens"]

    if len(stored_tokens) >= 1:
        for field in stored_tokens:
            # the token already exists
            if bcrypt.check_password_hash(field["hash"], response["token"]):
                return True
    return False
