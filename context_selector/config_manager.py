# context_selector/config_manager.py

import os
import json
import pathlib # For getting home directory reliably

# --- Project Defaults Config (Existing) ---
PROJECT_CONFIG_FILENAME = ".context_curator_defaults.json"
PROJECT_CONFIG_VERSION = 1

def get_project_config_path(source_dir):
    """Constructs the full path to the project-specific config file."""
    if not source_dir or not os.path.isdir(source_dir):
        return None
    return os.path.join(source_dir, PROJECT_CONFIG_FILENAME)

def load_defaults_config(source_dir):
    """Loads the list of default selected paths for a specific project."""
    config_path = get_project_config_path(source_dir)
    # ... (Keep existing implementation - check file, load JSON, validate) ...
    if not config_path or not os.path.exists(config_path):
        # print(f"Project config file not found at: {config_path}") # Less verbose
        return None
    print(f"Loading project defaults from: {config_path}")
    try:
        with open(config_path, 'r', encoding='utf-8') as f: data = json.load(f)
        if not isinstance(data, dict): print(f"Error: Project config not JSON object: {config_path}"); return None
        if data.get("version") != PROJECT_CONFIG_VERSION: print(f"Warning: Project config version mismatch...")
        selected_paths = data.get("selected_paths")
        if selected_paths is None: print(f"Warning: Project config missing 'selected_paths': {config_path}"); return []
        if not isinstance(selected_paths, list): print(f"Error: 'selected_paths' not list: {config_path}"); return None
        if not all(isinstance(p, str) for p in selected_paths): print(f"Error: Not all 'selected_paths' are strings: {config_path}"); return None
        print(f"Successfully loaded {len(selected_paths)} project default paths.")
        return selected_paths
    except Exception as e: print(f"Error loading project config: {config_path}\n{e}"); return None


def save_defaults_config(source_dir, selected_paths):
    """Saves the list of selected relative paths for a specific project."""
    config_path = get_project_config_path(source_dir)
    # ... (Keep existing implementation - check path, create dict, dump JSON) ...
    if not config_path: print("Error: Cannot determine project config path."); return False
    data_to_save = {"version": PROJECT_CONFIG_VERSION, "selected_paths": selected_paths}
    print(f"Saving {len(selected_paths)} project default paths to: {config_path}")
    try:
        with open(config_path, 'w', encoding='utf-8') as f: json.dump(data_to_save, f, indent=2)
        print("Project defaults saved successfully.")
        return True
    except Exception as e: print(f"Error writing project config file: {config_path}\n{e}"); return False


# --- Application Settings Config (New) ---
APP_SETTINGS_FILENAME = ".context_curator_app_settings.json"
APP_SETTINGS_VERSION = 1

def get_app_settings_path():
    """Gets the path for the application settings file in the user's home directory."""
    try:
        home = pathlib.Path.home()
        return os.path.join(home, APP_SETTINGS_FILENAME)
    except Exception as e:
        print(f"Error finding home directory: {e}")
        return None

def load_app_settings():
    """
    Loads application settings (last used paths) from the config file.

    Returns:
        dict: A dictionary containing the loaded settings (e.g.,
              {'last_source_dir': '...', 'last_dest_dir': '...'}),
              or an empty dictionary if the file doesn't exist or is invalid.
    """
    settings_path = get_app_settings_path()
    if not settings_path or not os.path.exists(settings_path):
        # print(f"App settings file not found at: {settings_path}") # Normal on first run
        return {} # Return empty dict if no settings file yet

    print(f"Loading app settings from: {settings_path}")
    try:
        with open(settings_path, 'r', encoding='utf-8') as f:
            settings = json.load(f)

        if not isinstance(settings, dict):
            print(f"Error: App settings file content is not a JSON object: {settings_path}")
            return {} # Return empty on invalid format

        # Optional: Check version later if needed
        # if settings.get("version") != APP_SETTINGS_VERSION: ...

        print("App settings loaded successfully.")
        return settings

    except Exception as e:
        print(f"Error loading or parsing app settings file: {settings_path}\n{e}")
        return {} # Return empty dict on error

def save_app_settings(settings_dict):
    """
    Saves the application settings dictionary to the config file.

    Args:
        settings_dict (dict): The dictionary containing settings to save.

    Returns:
        bool: True on success, False on failure.
    """
    settings_path = get_app_settings_path()
    if not settings_path:
        print("Error: Cannot determine app settings path (home directory issue?).")
        return False

    # Ensure version is included (or add it if missing)
    settings_dict["version"] = APP_SETTINGS_VERSION

    print(f"Saving app settings to: {settings_path}")
    try:
        with open(settings_path, 'w', encoding='utf-8') as f:
            json.dump(settings_dict, f, indent=2)
        # print("App settings saved successfully.") # Can be noisy
        return True
    except Exception as e:
        print(f"Error writing app settings file: {settings_path}\n{e}")
        return False