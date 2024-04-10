import json

NFC_DATA_FILE = 'nfc_data.json'

def read_config():
    """Reads the app configuration from a JSON file.

    Args: none

    Returns:
        - A dictionary containing the set configuration parameters for the
          application, such as webhook url, hashed list of tokens,
          and any other configuration settings.
    """
    try:
        with open('config.json', 'r') as file:
            return json.load(file)
    except:
        return { "base": {
                    "logging": {
                        "webhook": "https://discord.com/api/webhooks/WEBHOOKID/APIKEYHERE"
                        },
                    "canvas": {
                        "base_url": "https://hv.instructure.com/api/v1/",
                        "tokens" : []
                        }
                    }
                }

def save_config(app, config_lock):
    """Saves the application's settings to a JSON file.

    This function attempts to save the current settings from the application's
    configuration to a file named 'config.json'. It serializes the settings
    dictionary to JSON format with an indentation of 2 spaces for readability.
    If an error occurs during file writing or serialization, it prints an error
    message. The operation is thread-safe, protected by a lock.

    Args:
        app: The Flask application instance containing the settings in its
             'config' attribute.
        config_lock: A threading.Lock object used to synchronize access to
                     the configuration file.

    Returns:
        bool: True if the settings were successfully saved to the file,
              False otherwise.
    """
    with config_lock:
        settings = app.config.get("SETTINGS", {})
        try:
            with open('config.json', 'w') as file:
                json.dump(settings, file, indent=2)
            return True
        except IOError as e:
            print(f"Error saving configuration: {e}")
        except TypeError as e:
            print(f"Error serializing configuration: {e}")
        return False
    
def read_nfc_data(file_path):
    """Reads and returns NFC data from a specified JSON file.

    This function attempts to open and read a JSON file located at the given
    file path. If successful, it parses the JSON content into a Python
    dictionary and returns it. If the file does not exist, or if an error occurs
    during the parsing of the JSON data, it returns an empty dictionary.

    Args:
        file_path: A string specifying the path to the JSON file to be read.

    Returns:
        A dictionary containing the NFC data read from the file. Returns an
        empty dictionary if the file is not found or if a JSON decoding error
        occurs.
    """
    try:
        with open(file_path, 'r') as nfc_file:
            return json.load(nfc_file)
    except FileNotFoundError:
        return dict()
    except json.JSONDecodeError as e:
        return dict()

def write_nfc_data(nfc_data, file_path):
    """Writes NFC data to a specified JSON file.

    Attempts to serialize and write the given NFC data (a Python dictionary) 
    to a JSON file at the specified path. The JSON data is written with an 
    indentation of 2 spaces to improve readability. If an IOError occurs during
    file writing, the function catches the exception and returns False to 
    indicate failure.

    Args:
        nfc_data: A dictionary containing the data to be written to the file.
        file_path: A string specifying the path to the JSON file.

    Returns:
        bool: True if the data was successfully written, False otherwise.
    """
    try:
        with open(file_path, 'w') as file:
            json.dump(nfc_data, file, indent=2)
            return True
    except IOError as e:
        return False

