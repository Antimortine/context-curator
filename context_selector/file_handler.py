import os
import fnmatch # For wildcard matching
import shutil  # For file copying and directory removal
import locale  # For fallback encoding detection

def scan_directory_structure(source_path,
                             ignore_patterns=None,
                             whitelist_patterns=None,
                             blacklist_file_patterns=None, # Added parameter
                             destination_path=None):
    """
    Scans a directory recursively and returns a structure representing
    relevant files and folders, using directory ignore patterns, file whitelist
    patterns, and specific file blacklist patterns.

    Args:
        source_path (str): The absolute path to the source directory to scan.
        ignore_patterns (set, optional): Dir names/globs to ignore descent.
        whitelist_patterns (set, optional): File names/globs to include. If empty/None,
                                             all non-blacklisted files pass this stage.
        blacklist_file_patterns (set, optional): File names/globs to specifically exclude,
                                                 even if they match the whitelist.
        destination_path (str, optional): Absolute path to the destination dir to ignore.

    Returns:
        dict: Nested dictionary structure, or None if source_path is invalid.
    """
    # Initialize pattern sets if None
    if ignore_patterns is None: ignore_patterns = set()
    if whitelist_patterns is None: whitelist_patterns = set()
    if blacklist_file_patterns is None: blacklist_file_patterns = set() # Initialize new set

    # --- DEBUG PRINTS (Optional) ---
    # print(f"DEBUG: scan_directory_structure called for '{source_path}'")
    # print(f"DEBUG: Received ignore_patterns count: {len(ignore_patterns)}")
    # print(f"DEBUG: Received whitelist_patterns count: {len(whitelist_patterns)}")
    # print(f"DEBUG: Received blacklist_file_patterns count: {len(blacklist_file_patterns)}")
    print(f"DEBUG SCAN HANDLER: Received blacklist patterns: {blacklist_file_patterns}")
    # ---

    if not os.path.isdir(source_path):
        print(f"Error: Source path is not a valid directory: {source_path}")
        return None

    structure = {}
    source_path = os.path.abspath(source_path)
    relative_dest_path = None
    # --- Prepare Destination Path for Exclusion ---
    if destination_path:
        destination_path = os.path.abspath(destination_path)
        if os.path.commonpath([source_path, destination_path]) == source_path and source_path != destination_path:
            relative_dest = os.path.relpath(destination_path, source_path)
            relative_dest_path = tuple(relative_dest.split(os.sep))
            # print(f"DEBUG: Dynamically ignoring destination path relative components: {relative_dest_path}")

    # --- Walk the Directory Tree ---
    for root, dirs, files in os.walk(source_path, topdown=True, onerror=lambda err: print(f"Warning: Error accessing {err.filename}: {err.strerror}")):
        current_rel_path_for_debug = os.path.relpath(root, source_path)
        # --- Filter Directories (using ignore_patterns) ---
        original_dirs = list(dirs); dirs[:] = [] # Copy and clear for modification
        for d in original_dirs:
             is_ignored_by_pattern = any(fnmatch.fnmatch(d, pattern) for pattern in ignore_patterns)
             # Destination path check
             current_full_dir_path = os.path.join(root, d)
             current_rel_path_parts = tuple(os.path.relpath(current_full_dir_path, source_path).split(os.sep))
             is_dest_path = False
             if relative_dest_path and len(current_rel_path_parts) <= len(relative_dest_path):
                  if current_rel_path_parts == relative_dest_path[:len(current_rel_path_parts)]:
                       is_dest_path = True
             # Keep directory if not ignored and not destination
             if not is_ignored_by_pattern and not is_dest_path: dirs.append(d)

        # --- Filter Files (using Whitelist AND Blacklist) ---
        original_files_in_dir = list(files)
        files_to_add_to_structure = []
        print(f"--- Debugging Files in: {current_rel_path_for_debug or '.'} ---") # Indicate directory
        for f in original_files_in_dir:
            # 1. Check Blacklist first
            is_blacklisted = False
            matched_blacklist_pattern = None
            for pattern in blacklist_file_patterns:
                if fnmatch.fnmatch(f, pattern):
                    # *** THIS IS THE KEY DEBUG PRINT ***
                    print(f"    MATCHED BLACKLIST pattern '{pattern}'! Setting is_blacklisted=True.")
                    is_blacklisted = True
                    matched_blacklist_pattern = pattern
                    break # Stop checking blacklist patterns once matched

            if is_blacklisted:
                print(f"    --> RESULT: File '{f}' is blacklisted (pattern: '{matched_blacklist_pattern}'). SKIPPING.")
                continue # Skip this file entirely if blacklisted

            # 2. Check Whitelist (only if not blacklisted)
            is_whitelisted = not whitelist_patterns or any(fnmatch.fnmatch(f, pattern) for pattern in whitelist_patterns)

            if is_whitelisted:
                print(f"    --> RESULT: File '{f}' is NOT blacklisted and IS whitelisted. ADDING.")
                files_to_add_to_structure.append(f)
            else:
                print(f"    --> RESULT: File '{f}' is NOT blacklisted and NOT whitelisted. SKIPPING.")

        # --- Build the Nested Dictionary Structure ---
        rel_path = os.path.relpath(root, source_path)
        current_level = structure
        if rel_path != ".":
            try:
                for part in rel_path.split(os.sep): current_level = current_level.setdefault(part, {})
            except Exception as e: print(f"Warning: Error processing path component '{part}' for '{rel_path}': {e}"); continue
        # Add kept directories and filtered files
        for d in dirs: current_level.setdefault(d, {})
        for f in files_to_add_to_structure: current_level[f] = None

    return structure

# --- File Copying Logic ---
def copy_selected_files(source_root, dest_root, selected_relative_paths,
                        ignore_patterns=None, whitelist_patterns=None,
                        blacklist_file_patterns=None, # Added blacklist parameter
                        clear_dest=False, prepend_path=True):
    """
    Copies the selected files/folders from the source to the destination,
    flattening the structure and renaming files. Respects ignore/whitelist/blacklist
    patterns when expanding selected folders.

    (Args updated to include blacklist_file_patterns)
    ... rest of args ...

    Returns:
        tuple[int, list]: Count of copied files and list of errors (path, message).
    """
    print("\n--- Starting File Copy Process ---")
    print(f"Source:      {source_root}")
    print(f"Destination: {dest_root}")
    print(f"Selected paths count: {len(selected_relative_paths)}")
    print(f"Clear destination:  {clear_dest}")
    print(f"Prepend path comment: {prepend_path}")

    copied_count = 0
    errors = []

    # Initialize pattern sets if None
    if ignore_patterns is None: ignore_patterns = set()
    if whitelist_patterns is None: whitelist_patterns = set()
    if blacklist_file_patterns is None: blacklist_file_patterns = set() # Initialize blacklist

    # --- 1. Validate Paths / 2. Clear Destination / 3. Ensure Destination Exists ---
    if not os.path.isdir(source_root): errors.append((source_root, "Source path is not a valid directory.")); print(f"Error: Source path is not a valid directory: {source_root}"); return copied_count, errors
    if clear_dest:
        if os.path.abspath(source_root) == os.path.abspath(dest_root): errors.append((dest_root, "Destination cannot be the same as the source when clearing.")); print("Error: Destination cannot be the same as source when clearing."); return copied_count, errors
        if os.path.exists(dest_root):
            print(f"Attempting to clear destination directory: {dest_root}")
            try:
                for filename in os.listdir(dest_root):
                    file_path = os.path.join(dest_root, filename)
                    try:
                        if os.path.isfile(file_path) or os.path.islink(file_path): os.unlink(file_path)
                        elif os.path.isdir(file_path): shutil.rmtree(file_path)
                    except Exception as e: print(f"  - Warning: Error removing {file_path} during clear: {e}"); errors.append((file_path, f"Failed to remove during clear: {e}"))
                print("Destination directory contents removed (or attempted).")
            except Exception as e: print(f"Error accessing destination directory for clearing: {e}"); errors.append((dest_root, f"Failed to access for clearing: {e}"))
    try:
        os.makedirs(dest_root, exist_ok=True); print(f"Ensured destination directory exists: {dest_root}")
    except OSError as e: print(f"Fatal Error: Could not create destination directory: {dest_root}. Error: {e}"); errors.append((dest_root, f"Failed to create destination: {e}")); return copied_count, errors

    # --- 4. Identify All Individual Files to Copy (Respecting Filters) ---
    files_to_process_relative = set()
    print("Identifying individual files from selections...")

    # Helper function (same as before)
    def get_files_from_structure(structure_dict, current_rel_path=""):
        found_files = set();
        for name, content in structure_dict.items():
            item_rel_path = os.path.join(current_rel_path, name) if current_rel_path else name
            if content is None: found_files.add(item_rel_path)
            elif isinstance(content, dict): found_files.update(get_files_from_structure(content, item_rel_path))
        return found_files

    # Process user selections
    for rel_path in selected_relative_paths:
        is_folder = rel_path.endswith(os.sep)
        clean_rel_path = rel_path.rstrip(os.sep)
        abs_source_item_path = os.path.join(source_root, clean_rel_path)

        if is_folder:
            print(f"  - Processing selected folder: {rel_path}")
            if os.path.isdir(abs_source_item_path):
                print(f"    Scanning sub-folder '{abs_source_item_path}' respecting filters...")
                # Pass all filters to the sub-scan
                sub_structure = scan_directory_structure(
                    source_path=abs_source_item_path,
                    ignore_patterns=ignore_patterns,
                    whitelist_patterns=whitelist_patterns,
                    blacklist_file_patterns=blacklist_file_patterns, # Pass blacklist
                    destination_path=None # Assuming dest isn't inside selected folders
                )
                if sub_structure:
                    files_in_sub = get_files_from_structure(sub_structure)
                    for sub_file_rel in files_in_sub:
                        full_rel_path = os.path.join(clean_rel_path, sub_file_rel)
                        files_to_process_relative.add(full_rel_path)
                    print(f"    Found {len(files_in_sub)} filtered files within.")
                else: print(f"    Sub-scan of '{rel_path}' returned no structure.")
            else: msg = f"Selected folder path not found: {abs_source_item_path}"; print(f"    Warning: {msg}"); errors.append((rel_path, msg))
        else: # Selected item is a file
            print(f"  - Processing selected file: {rel_path}")
            if os.path.isfile(abs_source_item_path):
                file_name = os.path.basename(clean_rel_path)
                # Check blacklist first
                is_blacklisted = any(fnmatch.fnmatch(file_name, p) for p in blacklist_file_patterns)
                if is_blacklisted:
                    msg = "Selected file matches blacklist pattern"; print(f"    Warning: Skipping {clean_rel_path} ({msg})"); errors.append((rel_path, msg)); continue
                # Check whitelist (optional but good for robustness)
                is_whitelisted = not whitelist_patterns or any(fnmatch.fnmatch(file_name, p) for p in whitelist_patterns)
                if is_whitelisted: files_to_process_relative.add(clean_rel_path)
                else: msg = "Selected file does not match whitelist patterns"; print(f"    Warning: {msg}: {clean_rel_path}"); errors.append((rel_path, msg))
            else: msg = f"Selected file path not found: {abs_source_item_path}"; print(f"    Warning: {msg}"); errors.append((rel_path, msg))

    print(f"Total unique files identified for copying: {len(files_to_process_relative)}")
    if not files_to_process_relative: print("No valid files found based on selection and filters."); return copied_count, errors

    # --- 5. Perform the Copy Operation for Each Unique File ---
    print("Starting copy operation...")
    for rel_file_path in sorted(list(files_to_process_relative)):
        abs_source_file = os.path.join(source_root, rel_file_path)
        flat_name_base = rel_file_path.replace(os.sep, '___').replace('\\', '___')
        dest_filename = f"{flat_name_base}.txt"
        abs_dest_file = os.path.join(dest_root, dest_filename)
        try:
            if not os.path.isfile(abs_source_file): raise FileNotFoundError(f"Source file gone missing before copy: {abs_source_file}")
            print(f"  - Copying: '{rel_file_path}'\n      -> '{dest_filename}'")
            content = None; detected_encoding = None
            try: # Read with encoding detection
                with open(abs_source_file, 'r', encoding='utf-8') as f_in: content = f_in.read(); detected_encoding = 'utf-8'
            except UnicodeDecodeError:
                 try:
                      fallback_encoding = locale.getpreferredencoding(False) or 'latin-1'
                      # print(f"    Warning: UTF-8 decode failed for '{rel_file_path}'. Trying fallback '{fallback_encoding}'.")
                      with open(abs_source_file, 'r', encoding=fallback_encoding) as f_in: content = f_in.read(); detected_encoding = fallback_encoding
                 except Exception as enc_e: msg = f"Cannot decode file content (tried utf-8, {fallback_encoding}): {enc_e}"; print(f"    Error: {msg}"); errors.append((rel_file_path, msg)); continue
            with open(abs_dest_file, 'w', encoding='utf-8') as f_out: # Write as UTF-8
                if prepend_path: encoding_info = f" (source encoding: {detected_encoding})" if detected_encoding else ""; f_out.write(f"--- Source Path: {rel_file_path}{encoding_info} ---\n\n")
                f_out.write(content)
            copied_count += 1
        except FileNotFoundError as e: print(f"  Error: {e}"); errors.append((rel_file_path, str(e)))
        except IOError as e: print(f"  Error copying file '{rel_file_path}' (I/O Error): {e}"); errors.append((rel_file_path, f"IO Error: {e}"))
        except OSError as e: print(f"  Error copying file '{rel_file_path}' (OS Error): {e}"); errors.append((rel_file_path, f"OS Error: {e}"))
        except Exception as e: print(f"  Unexpected error copying file '{rel_file_path}': {e}"); errors.append((rel_file_path, f"Unexpected error: {e}"))

    # --- 6. Final Report ---
    print(f"--- File Copy Process Finished ---"); print(f"Successfully copied: {copied_count} files")
    if errors:
        print(f"Errors encountered ({len(errors)}):"); max_errors_to_show = 10
        for i, (path, msg) in enumerate(errors):
            if i < max_errors_to_show: print(f"  - {path}: {msg}")
            elif i == max_errors_to_show: print(f"  ... ({len(errors) - max_errors_to_show} more errors not shown)"); break
    return copied_count, errors