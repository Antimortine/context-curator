import os
import fnmatch # For wildcard matching
import shutil # For file copying later

def scan_directory_structure(source_path, ignore_patterns=None, whitelist_patterns=None, destination_path=None):
    """
    Scans a directory recursively and returns a structure representing
    relevant files and folders, using directory ignore patterns and file whitelist patterns.

    Args:
        source_path (str): The absolute path to the source directory to scan.
        ignore_patterns (set, optional): A set of directory names or glob patterns to ignore.
                                         Defaults to an empty set.
        whitelist_patterns (set, optional): A set of file names or glob patterns to include.
                                            If None or empty, all files in allowed directories pass.
                                            Defaults to None.
        destination_path (str, optional): The absolute path to the destination directory.
                                          If it's inside the source_path, it will be ignored.

    Returns:
        dict: A nested dictionary representing the directory structure.
              Keys are item names (files/folders), values are either:
              - Another dict for subdirectories.
              - None for files.
              Returns None if source_path is invalid.
    """
    # Initialize pattern sets if None
    if ignore_patterns is None:
        ignore_patterns = set()
    if whitelist_patterns is None:
         whitelist_patterns = set()

    # --- START DEBUG PRINTS ---
    print(f"DEBUG: scan_directory_structure called for '{source_path}'")
    print(f"DEBUG: Received ignore_patterns count: {len(ignore_patterns)}")
    print(f"DEBUG: Received whitelist_patterns count: {len(whitelist_patterns)}")
    # Optionally print the whole whitelist to be sure:
    # print(f"DEBUG: Whitelist patterns: {whitelist_patterns}")
    # --- END DEBUG PRINTS ---

    if not os.path.isdir(source_path):
        print(f"Error: Source path is not a valid directory: {source_path}")
        return None # Source path is not a valid directory

    structure = {}
    source_path = os.path.abspath(source_path)
    relative_dest_path = None

    # --- Prepare Destination Path for Exclusion ---
    if destination_path:
        destination_path = os.path.abspath(destination_path)
        # Check if destination is *strictly* inside source (not the source itself)
        if os.path.commonpath([source_path, destination_path]) == source_path and source_path != destination_path:
            relative_dest = os.path.relpath(destination_path, source_path)
            relative_dest_path = tuple(relative_dest.split(os.sep))
            print(f"DEBUG: Dynamically ignoring destination path relative components: {relative_dest_path}") # Debug

    # --- Walk the Directory Tree ---
    for root, dirs, files in os.walk(source_path, topdown=True, onerror=lambda err: print(f"Error accessing {err.filename}: {err.strerror}")):

        current_rel_path_for_debug = os.path.relpath(root, source_path)
        # --- START DEBUG PRINTS ---
        # print(f"DEBUG: Walking directory: {current_rel_path_for_debug}")
        # print(f"DEBUG: Original dirs: {dirs}")
        # print(f"DEBUG: Original files: {files}")
        # --- END DEBUG PRINTS ---


        # --- Filter Directories (using ignore_patterns) ---
        original_dirs = list(dirs) # Make a copy to iterate over while modifying dirs
        dirs[:] = [] # Clear the original list; add back the ones we want to descend into

        for d in original_dirs:
            current_full_dir_path = os.path.join(root, d)
            current_rel_path_parts = tuple(os.path.relpath(current_full_dir_path, source_path).split(os.sep))

            # 1. Check against directory ignore patterns (exact match or glob)
            is_ignored_by_pattern = any(fnmatch.fnmatch(d, pattern) for pattern in ignore_patterns)

            # 2. Check if it's the destination directory (or part of its path)
            is_dest_path = False
            if relative_dest_path and len(current_rel_path_parts) <= len(relative_dest_path):
                 if current_rel_path_parts == relative_dest_path[:len(current_rel_path_parts)]:
                      is_dest_path = True

            if not is_ignored_by_pattern and not is_dest_path:
                dirs.append(d) # Keep this directory, os.walk will descend into it
            # else:
            #    print(f"DEBUG: Ignoring directory '{d}' (ignored: {is_ignored_by_pattern}, is_dest: {is_dest_path})")


        # --- Filter Files (using whitelist_patterns) ---
        # Important: Use the ORIGINAL list of files from os.walk (`files` before modification by whitelist logic)
        # when deciding which files to check. The modified `files` list should only contain whitelisted ones.
        original_files_in_dir = list(files) # Get the original list before it's potentially replaced

        if whitelist_patterns: # Check if filtering is active
             whitelisted_files = []
             # --- START DEBUG PRINTS ---
             # print(f"DEBUG: Applying whitelist filter in '{current_rel_path_for_debug}'...")
             # --- END DEBUG PRINTS ---
             for f in original_files_in_dir: # Iterate original files
                 is_whitelisted = any(fnmatch.fnmatch(f, pattern) for pattern in whitelist_patterns)
                 # --- START DEBUG PRINTS ---
                 print(f"DEBUG: Checking file '{f}' in '{current_rel_path_for_debug}': Whitelisted = {is_whitelisted}")
                 # --- END DEBUG PRINTS ---
                 if is_whitelisted:
                     whitelisted_files.append(f)
             # --- START DEBUG PRINTS ---
             print(f"DEBUG: Files after whitelist in '{current_rel_path_for_debug}': {whitelisted_files}")
             # --- END DEBUG PRINTS ---
             files_to_add_to_structure = whitelisted_files # Use the filtered list
        else:
            # --- START DEBUG PRINTS ---
            print(f"DEBUG: No whitelist patterns provided or empty set, using all files in '{current_rel_path_for_debug}'.")
            # --- END DEBUG PRINTS ---
            files_to_add_to_structure = original_files_in_dir # Use the original list


        # --- Build the Nested Dictionary Structure ---
        rel_path = os.path.relpath(root, source_path)
        current_level = structure
        if rel_path != ".": # If not the root directory itself
            try:
                for part in rel_path.split(os.sep):
                    current_level = current_level.setdefault(part, {})
            except KeyError:
                 print(f"Warning: Could not find path component '{part}' in structure for path '{rel_path}'. Skipping files/dirs here.")
                 continue # Skip adding files/dirs for this iteration


        # Add filtered subdirectories and files to the current level in the structure
        for d in dirs: # Add folders that we decided to keep (and descend into)
            current_level.setdefault(d, {}) # Ensure folder entry exists
        for f in files_to_add_to_structure: # Add files that passed the filter (or all)
            current_level[f] = None # Add file entry


    return structure


# --- Placeholder for File Copying Logic ---

def copy_selected_files(source_root, dest_root, selected_relative_paths, clear_dest=False, prepend_path=True):
    """
    Copies the selected files/folders from the source to the destination,
    flattening the structure and renaming files.

    Args:
        source_root (str): Absolute path to the source project directory.
        dest_root (str): Absolute path to the destination directory for curated files.
        selected_relative_paths (list[str]): List of relative paths (from source_root)
                                             of files/folders selected by the user.
                                             Folders end with os.sep.
        clear_dest (bool): If True, cleans the destination directory before copying.
                           Defaults to False. USE WITH CAUTION.
        prepend_path (bool): If True, prepends the original relative path as a comment
                             or header in the copied text file. Defaults to True.

    Returns:
        tuple[int, list]: A tuple containing:
                          - count (int): Number of files successfully copied.
                          - errors (list): A list of tuples (path, error_message) for failures.
    """
    print("--- Starting File Copy Process ---")
    print(f"Source: {source_root}")
    print(f"Destination: {dest_root}")
    print(f"Selected paths count: {len(selected_relative_paths)}")
    print(f"Clear destination: {clear_dest}")
    print(f"Prepend path comment: {prepend_path}")

    copied_count = 0
    errors = []

    # 1. Clear destination directory (optional, use cautiously)
    if clear_dest:
        if os.path.exists(dest_root):
            # IMPORTANT: Add confirmation or be very sure before enabling this!
            print(f"WARNING: Clearing destination directory: {dest_root}")
            try:
                for filename in os.listdir(dest_root):
                    file_path = os.path.join(dest_root, filename)
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                print("Destination directory cleared.")
            except Exception as e:
                print(f"Error clearing destination directory: {e}")
                errors.append((dest_root, f"Failed to clear: {e}"))
                # Decide if you want to stop here or continue
                # return copied_count, errors # Example: Stop if clearing fails

        # Ensure destination exists after clearing attempt (or if it didn't exist)
        if not os.path.exists(dest_root):
             try:
                  os.makedirs(dest_root)
                  print(f"Created destination directory: {dest_root}")
             except OSError as e:
                  print(f"Error creating destination directory: {e}")
                  errors.append((dest_root, f"Failed to create: {e}"))
                  return copied_count, errors # Stop if creation fails


    # 2. Iterate through selected paths and copy files
    files_to_copy_queue = set() # Use a set to avoid duplicates if folder and sub-file are selected

    for rel_path in selected_relative_paths:
        is_folder = rel_path.endswith(os.sep)
        clean_rel_path = rel_path.rstrip(os.sep)
        abs_source_path = os.path.join(source_root, clean_rel_path)

        if is_folder:
            # If a folder is selected, find all files within it recursively
            # Respecting the original ignore/whitelist logic is complex here,
            # Easiest is to just walk the selected subfolder and copy all files found.
            # A more accurate way would re-use scan_directory_structure logic for sub-paths.
            print(f"Processing selected folder: {rel_path}")
            if os.path.isdir(abs_source_path):
                for sub_root, _, sub_files in os.walk(abs_source_path):
                     for file in sub_files:
                          abs_file_path = os.path.join(sub_root, file)
                          rel_file_path = os.path.relpath(abs_file_path, source_root)
                          # TODO: Should probably re-apply whitelist here too for consistency?
                          files_to_copy_queue.add(rel_file_path) # Add relative path from original source_root
            else:
                msg = f"Selected folder path not found or not a directory: {abs_source_path}"
                print(f"Warning: {msg}")
                errors.append((rel_path, msg))
        else:
            # If a file is selected, add it directly
            print(f"Processing selected file: {rel_path}")
            if os.path.isfile(abs_source_path):
                files_to_copy_queue.add(clean_rel_path)
            else:
                msg = f"Selected file path not found or not a file: {abs_source_path}"
                print(f"Warning: {msg}")
                errors.append((rel_path, msg))


    print(f"Total unique files identified for copying: {len(files_to_copy_queue)}")

    # 3. Perform the actual copy for unique files
    for rel_file_path in files_to_copy_queue:
        abs_source_file = os.path.join(source_root, rel_file_path)

        # Generate flattened destination name: path_to_file.ext -> path___to___file.ext.txt
        # Replace separators and add .txt extension
        flat_name_base = rel_file_path.replace(os.sep, '___')
        # Consider potential collisions if names become identical after replacement
        # (e.g., 'a/b.txt' and 'a_b.txt' if source used underscores)
        # For simplicity, we'll ignore this for now.
        dest_filename = f"{flat_name_base}.txt"
        abs_dest_file = os.path.join(dest_root, dest_filename)

        try:
            # Ensure the source file still exists
            if not os.path.isfile(abs_source_file):
                 raise FileNotFoundError(f"Source file gone missing: {abs_source_file}")

            print(f"  Copying: '{rel_file_path}' -> '{dest_filename}'")

            # Read source content (assuming text files)
            # Handle potential encoding issues
            content = ""
            try:
                with open(abs_source_file, 'r', encoding='utf-8') as f_in:
                    content = f_in.read()
            except UnicodeDecodeError:
                 try:
                      # Try fallback encoding (e.g., system default or latin-1)
                      import locale
                      fallback_encoding = locale.getpreferredencoding(False)
                      print(f"    Warning: UTF-8 decode failed for {rel_file_path}. Trying {fallback_encoding}.")
                      with open(abs_source_file, 'r', encoding=fallback_encoding) as f_in:
                           content = f_in.read()
                 except Exception as enc_e:
                      print(f"    Error: Could not decode file {rel_file_path}. Skipping content. Error: {enc_e}")
                      errors.append((rel_file_path, f"File decode error: {enc_e}"))
                      # Copy file raw if decode fails? Or skip? Skipping content for now.
                      # shutil.copy2(abs_source_file, abs_dest_file) # Option: raw copy
                      # copied_count += 1
                      continue # Skip writing this file if content couldn't be read


            # Write to destination file, potentially prepending path
            with open(abs_dest_file, 'w', encoding='utf-8') as f_out:
                if prepend_path:
                    # Add a clear header/comment
                    f_out.write(f"--- Source Path: {rel_file_path} ---\n\n")
                f_out.write(content)

            copied_count += 1

        except Exception as e:
            print(f"  Error copying file {rel_file_path}: {e}")
            errors.append((rel_file_path, str(e)))

    print(f"--- File Copy Process Finished ---")
    print(f"Successfully copied: {copied_count} files")
    if errors:
        print(f"Errors encountered: {len(errors)}")
        for path, msg in errors:
            print(f"  - {path}: {msg}")

    return copied_count, errors