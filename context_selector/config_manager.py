# context_selector/config_manager.py

import os
import json

CONFIG_FILENAME = ".context_curator_defaults.json"
CONFIG_VERSION = 1

def get_config_path(source_dir):
    """Constructs the full path to the config file in the source directory."""
    if not source_dir or not os.path.isdir(source_dir):
        return None
    return os.path.join(source_dir, CONFIG_FILENAME)

def load_defaults_config(source_dir):
    """
    Loads the list of default selected paths from the config file
    in the specified source directory.

    Args:
        source_dir (str): The path to the source project directory.

    Returns:
        list[str] | None: A list of relative paths (strings) selected by default,
                          or None if the file doesn't exist or is invalid.
                          Returns an empty list if the file exists but has no paths.
    """
    config_path = get_config_path(source_dir)
    if not config_path or not os.path.exists(config_path):
        print(f"Config file not found at: {config_path}")
        return None # Indicate file not found

    print(f"Loading defaults from: {config_path}")
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Basic validation
        if not isinstance(data, dict):
            print(f"Error: Config file content is not a JSON object: {config_path}")
            return None
        if data.get("version") != CONFIG_VERSION:
            # Handle version mismatch later if needed (e.g., migration)
            print(f"Warning: Config file version mismatch (expected {CONFIG_VERSION}, found {data.get('version')}). Trying to load anyway.")

        selected_paths = data.get("selected_paths")
        if selected_paths is None:
             print(f"Warning: Config file missing 'selected_paths' key: {config_path}")
             return [] # Return empty list if key is missing
        if not isinstance(selected_paths, list):
             print(f"Error: 'selected_paths' in config is not a list: {config_path}")
             return None # Indicate invalid format

        # Further validation: ensure all items are strings?
        if not all(isinstance(p, str) for p in selected_paths):
             print(f"Error: Not all items in 'selected_paths' are strings: {config_path}")
             return None

        print(f"Successfully loaded {len(selected_paths)} default paths.")
        return selected_paths

    except FileNotFoundError:
        # This case is handled by the os.path.exists check above, but good practice
        print(f"Config file not found (race condition?): {config_path}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from config file: {config_path}\n{e}")
        return None # Indicate invalid JSON
    except Exception as e:
        # Catch other potential errors during file reading/processing
        print(f"An unexpected error occurred loading config: {config_path}\n{e}")
        return None

def save_defaults_config(source_dir, selected_paths):
    """
    Saves the list of selected relative paths to the config file
    in the specified source directory.

    Args:
        source_dir (str): The path to the source project directory.
        selected_paths (list[str]): The list of relative paths to save.

    Returns:
        bool: True on success, False on failure.
    """
    config_path = get_config_path(source_dir)
    if not config_path:
        print("Error: Cannot determine config path (invalid source directory?).")
        return False

    data_to_save = {
        "version": CONFIG_VERSION,
        "selected_paths": selected_paths
    }

    print(f"Saving {len(selected_paths)} default paths to: {config_path}")
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(data_to_save, f, indent=2) # Use indent for readability
        print("Defaults saved successfully.")
        return True
    except IOError as e:
        print(f"Error writing config file: {config_path}\n{e}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred saving config: {config_path}\n{e}")
        return False