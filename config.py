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
    
def read_nfc_data(file_path):
    """Reads NFC data from a JSON file.

    Args:
        file_path: A string path to the JSON file to be read.

    Returns:
        - A dictionary with the contents read from the file, or an empty dict
          if an error occurs.
    """
    try:
        with open(file_path, 'r') as nfc_file:
            return json.load(nfc_file)
    except FileNotFoundError:
        return dict()
    except json.JSONDecodeError as e:
        return dict()

def write_nfc_data(nfc_data, file_path):
    """Writes NFC data to a JSON file.

    Args:
        nfc_data: A dictionary containing NFC data to be written to the file.
        file_path: A string path to the JSON file to be written.

    Returns:
        - A boolean indicating the success status of the write operation.
    """
    try:
        with open(file_path, 'w') as file:
            json.dump(nfc_data, file, indent=2)
            return True
    except IOError as e:
        return False

