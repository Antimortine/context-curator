import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
from .file_handler import scan_directory_structure
# Import config_manager later when needed for load/save defaults
# from .config_manager import load_defaults_config, save_defaults_config

class AppWindow:
    """
    Main application window for Context Curator.
    Handles UI setup, event handling, and orchestrates backend logic.
    """
    # Blacklist for DIRECTORIES (prevents descending into them)
    DEFAULT_IGNORE_DIR_PATTERNS = {
        # Version Control - Standard directory names
        ".git", ".svn", ".hg",

        # Python specific build/cache/env directories
        "__pycache__",
        ".Python", # Often created by installers
        "build",
        "dist",
        "eggs",
        ".eggs",
        "lib",     # Often part of venv or build artifacts
        "lib64",   # Often part of venv or build artifacts
        "parts",   # Common in buildout
        "sdist",
        "var",     # Can be used for logs/data, might be too broad? Review if needed.
        "wheels",
        "venv",
        ".venv",
        "env",
        "ENV",

        # Test specific directories
        ".pytest_cache",
        ".tox",
        ".nox",
        "htmlcov", # Typically output directory for coverage reports

        # IDE / Editor specific config directories
        ".vscode",
        ".idea",
        ".settings", # Common in Eclipse

        # Node specific dependencies directory
        "node_modules",

        # Common output/build folders
        "output",
        "out",
        "target", # Common in Java/Rust
        "bin",    # Often contains executables/scripts
        "obj",    # Common build artifact directory (C/C++)

        # OS metadata directories (less common but possible)
        # ".DS_Store", # Typically a file, safe to remove unless needed
        # "Thumbs.db", # Typically a file

        # Other common tool/framework directories
        ".vite",  # Vite cache/build directory
        ".nuxt",  # Nuxt build directory
        ".next",  # Next.js build directory
        "cache",  # Generic cache folder, might be too broad? Review if needed.
        ".cache", # Common Linux cache directory pattern

        # Add other common directory patterns specific to your projects if needed
        "chroma_db",
        "logs",
        "temp"
        "tmp",
        "user_projects",
        "data",
    }
    # Whitelist for file patterns/names (used AFTER directory ignore)
    DEFAULT_WHITELIST_FILE_PATTERNS = {
        # Common Code Files
        "*.py", "*.js", "*.ts", "*.jsx", "*.tsx", "*.java", "*.kt", "*.scala",
        "*.c", "*.cpp", "*.h", "*.hpp", "*.cs", "*.go", "*.rs", "*.rb", "*.php",
        "*.swift", "*.m", "*.mm", "*.pl", "*.pm", "*.lua", "*.dart", "*.groovy",
        "*.r", "*.sh", "*.bash", "*.zsh", "*.ps1", "*.bat", "*.cmd",
        # Common Config Files
        "*.json", "*.yaml", "*.yml", "*.xml", "*.toml", "*.ini", "*.cfg", "*.conf",
        "*.properties", "*.env.example", ".*rc", # e.g., .bashrc, .npmrc
        # Common Documentation / Text Files
        "*.md", "*.txt", "*.rst", "*.tex", "*.log", "*.csv", "*.tsv",
        # Web Files
        "*.html", "*.htm", "*.css", "*.scss", "*.sass", "*.less", "*.vue", "*.svelte",
        "*.sql", "*.graphql", "*.gql",
        # Build System / Infra Files (Exact Matches)
        "Dockerfile", "docker-compose.yml", "docker-compose.yaml",
        "Makefile", "CMakeLists.txt", "requirements.txt", "requirements.in", "Pipfile",
        "pyproject.toml", "package.json", "pom.xml", "build.gradle", "settings.gradle",
        "Cargo.toml", "go.mod", "go.sum", "composer.json", "Gemfile",
        # Common Root Files (Exact Matches)
        "README", "README.*", # README.md, README.txt etc.
        "LICENSE", "LICENSE.*",
        "CONTRIBUTING", "CONTRIBUTING.*",
        "CHANGELOG", "CHANGELOG.*",
        "NOTICE",
        # Add any other specific text-based formats relevant to your work
    }

    def __init__(self, master):
        """
        Initialize the main application window.

        Args:
            master: The root Tkinter window (tk.Tk).
        """
        self.master = master
        self.master.title("Context Curator")
        self.master.minsize(700, 500) # Width, Height in pixels

        # --- Variables ---
        self.source_dir_var = tk.StringVar(master=self.master, value="No source selected")
        self.dest_dir_var = tk.StringVar(master=self.master, value="No destination selected")
        # Store item states (checked/unchecked) - maps Treeview item ID to boolean
        self._item_states = {}
        # Store mapping from relative path to treeview item ID for loading defaults
        self._path_to_item_id = {}


        # --- Create and Grid the Main Frame ---
        main_frame = ttk.Frame(self.master, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # --- Configure Grid Weights for Resizing ---
        # Allow the main frame (row 0, col 0) of the root window to expand
        self.master.rowconfigure(0, weight=1)
        self.master.columnconfigure(0, weight=1)

        # Configure main_frame's grid weights (rows/columns inside main_frame)
        main_frame.rowconfigure(2, weight=1) # Treeview row expands vertically
        main_frame.columnconfigure(0, weight=1) # Treeview column expands horizontally


        # --- Create Widgets INSIDE main_frame ---

        # 1. Source Directory Selection
        src_frame = ttk.LabelFrame(main_frame, text="Source Project Directory", padding="5")
        src_frame.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 5))
        src_frame.columnconfigure(1, weight=1) # Allow label to expand

        src_label = ttk.Label(src_frame, textvariable=self.source_dir_var, relief="sunken", background="white", anchor=tk.W)
        src_label.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 5))
        src_button = ttk.Button(src_frame, text="Browse...", command=self._browse_source_directory)
        src_button.grid(row=0, column=2, sticky=tk.E)

        # 2. Destination Directory Selection
        dest_frame = ttk.LabelFrame(main_frame, text="Destination Directory (for curated files)", padding="5")
        dest_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        dest_frame.columnconfigure(1, weight=1) # Allow label to expand

        dest_label = ttk.Label(dest_frame, textvariable=self.dest_dir_var, relief="sunken", background="white", anchor=tk.W)
        dest_label.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 5))
        dest_button = ttk.Button(dest_frame, text="Browse...", command=self._browse_dest_directory)
        dest_button.grid(row=0, column=2, sticky=tk.E)

        # 3. File Tree View Area
        tree_frame = ttk.LabelFrame(main_frame, text="Select Files and Folders", padding="5")
        tree_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S))
        tree_frame.rowconfigure(0, weight=1)    # Allow treeview inside to expand vertically
        tree_frame.columnconfigure(0, weight=1) # Allow treeview inside to expand horizontally

        # --- Create the Treeview ---
        # 'none' prevents default Tk selection behavior; we handle clicks for checkboxes.
        self.tree = ttk.Treeview(tree_frame, selectmode='none', show='tree headings') # show='tree' hides the default '#' column header
        self.tree.heading('#0', text='Project Structure', anchor=tk.W) # Set header for the tree column
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Add Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        vsb.grid(row=0, column=1, sticky=(tk.N, tk.S))
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        hsb.grid(row=1, column=0, sticky=(tk.W, tk.E))
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        # --- Bind Click Event for Checkbox Simulation ---
        # Button-1 is the left mouse button
        self.tree.bind("<Button-1>", self._handle_click)

        # 4. Control Buttons Frame
        button_frame = ttk.Frame(main_frame, padding="5")
        button_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.S), pady=(10, 0))

        load_button = ttk.Button(button_frame, text="Load Default", command=self._load_defaults)
        load_button.grid(row=0, column=0, padx=(0, 5))

        save_button = ttk.Button(button_frame, text="Save Default", command=self._save_defaults)
        save_button.grid(row=0, column=1, padx=(0, 5))

        clear_button = ttk.Button(button_frame, text="Clear Selection", command=self._clear_selection)
        clear_button.grid(row=0, column=2, padx=(0, 5))

        # 5. Prepare Context Button (Aligned Right)
        prepare_button = ttk.Button(main_frame, text="Prepare Context", command=self._prepare_context)
        prepare_button.grid(row=3, column=2, sticky=(tk.E, tk.S), pady=(10, 0))

        # --- Initialize checkbox images (needs assets folder) ---
        self._initialize_checkbox_images()


    # --- Checkbox Image Handling ---

    def _initialize_checkbox_images(self):
        """Pre-loads or prepares checkbox images using BitmapImage or text fallback."""
        if hasattr(self, '_checkbox_images') and self._checkbox_images:
            return # Already initialized

        self._checkbox_images = {} # Cache for images: {True: checked_img, False: unchecked_img}
        try:
            from tkinter import BitmapImage
            assets_dir = os.path.join(os.path.dirname(__file__), 'assets')
            checked_path = os.path.join(assets_dir, 'checked.xbm')
            unchecked_path = os.path.join(assets_dir, 'unchecked.xbm')

            # Try to load checked image
            if os.path.exists(checked_path):
                self._checkbox_images[True] = BitmapImage(file=checked_path, foreground="black", background="white")
            else:
                print(f"Warning: Checkbox image not found: {checked_path}. Using text fallback '[x]'.")
                self._checkbox_images[True] = "[x]" # Text fallback

            # Try to load unchecked image
            if os.path.exists(unchecked_path):
                 self._checkbox_images[False] = BitmapImage(file=unchecked_path, foreground="black", background="white")
            else:
                 print(f"Warning: Checkbox image not found: {unchecked_path}. Using text fallback '[ ]'.")
                 self._checkbox_images[False] = "[ ]" # Text fallback

        except tk.TclError as e:
            # Handle cases where XBM files are invalid or tk fails
            print(f"Error loading checkbox bitmap images: {e}. Using text fallback.")
            self._checkbox_images[True] = "[x]"
            self._checkbox_images[False] = "[ ]"
        except ImportError:
            # Fallback if BitmapImage isn't available (less likely)
            print("Warning: tkinter.BitmapImage not available. Using text fallback.")
            self._checkbox_images[True] = "[x]"
            self._checkbox_images[False] = "[ ]"
        except Exception as e:
             # Catch any other unexpected error during image loading
             print(f"Unexpected error loading checkbox images: {e}. Using text fallback.")
             self._checkbox_images[True] = "[x]"
             self._checkbox_images[False] = "[ ]"

    def _get_checkbox_image(self, checked):
        """Retrieves the pre-loaded checkbox image or text fallback."""
        # Ensure initialization happened (should have been called in __init__)
        if not hasattr(self, '_checkbox_images') or not self._checkbox_images:
            self._initialize_checkbox_images()
        # Return preloaded image or fallback text
        return self._checkbox_images.get(checked, "[?]") # Default fallback


    # --- Treeview Population and Management ---

    def _populate_treeview(self, structure, parent_id="", current_rel_path=""):
        """
        Recursively populates the ttk.Treeview based on the scanned structure.

        Args:
            structure (dict): The nested dictionary from scan_directory_structure.
            parent_id (str): The Treeview ID of the parent item.
            current_rel_path (str): The relative path built up to this level.
        """
        # Sort items alphabetically, folders first then files
        sorted_items = sorted(
            structure.items(),
            key=lambda item: (isinstance(item[1], dict), item[0].lower()) # Sort key: (is_folder, name)
        )

        for name, content in sorted_items:
            item_type = "folder" if isinstance(content, dict) else "file"
            # Construct the full relative path for this item
            rel_path = os.path.join(current_rel_path, name) if current_rel_path else name

            # Insert item into the tree
            item_id = self.tree.insert(parent_id, 'end', text=name, open=False, tags=(item_type,))

            # Store state and path mapping
            self._item_states[item_id] = False
            self._path_to_item_id[rel_path] = item_id

            # Set initial visual state (unchecked checkbox image via tags)
            # The 'unchecked' tag must be configured with the image beforehand
            self.tree.item(item_id, tags=(item_type, 'unchecked'))

            if item_type == "folder":
                # Add a placeholder node if folder is empty, allows expansion visualization
                if not content:
                     self.tree.insert(item_id, 'end', text="...", tags=('placeholder',))
                else:
                    # Recursively add children for non-empty folders
                    self._populate_treeview(content, item_id, rel_path)


    # --- CORRECTED _update_treeview method ---
    def _update_treeview(self):
        """Clears and repopulates the treeview based on current settings."""
        source_dir = self.source_dir_var.get()
        dest_dir = self.dest_dir_var.get()

        # --- Pre-Update Cleanup and Validation ---
        self.tree.delete(*self.tree.get_children()) # Clear existing tree content
        self._item_states.clear()                   # Clear stored states
        self._path_to_item_id.clear()               # Clear path mapping

        if not source_dir or "No source selected" in source_dir or not os.path.isdir(source_dir):
            # Keep tree empty if source is invalid or not selected
            return

        # --- Prepare Scan Parameters ---
        # CORRECT: Use the renamed constant for ignore dirs
        ignore_dirs = set(self.DEFAULT_IGNORE_DIR_PATTERNS)
        # CORRECT: Create the set for whitelist files
        whitelist_files = set(self.DEFAULT_WHITELIST_FILE_PATTERNS)

        # Debug print to confirm counts BEFORE calling the function
        print(f"DEBUG (app_window): Preparing scan. Ignore Dirs Count = {len(ignore_dirs)}, Whitelist Files Count = {len(whitelist_files)}")
        if not whitelist_files:
             print("DEBUG (app_window): Whitelist Files set is EMPTY!")


        valid_dest = dest_dir and "No destination selected" not in dest_dir and os.path.exists(dest_dir)
        dest_to_ignore = dest_dir if valid_dest else None

        # --- Scan Directory ---
        # CORRECT: Update print statement
        print(f"Scanning {source_dir} (ignoring dirs matching {len(ignore_dirs)} patterns, "
              f"whitelisting files matching {len(whitelist_files)} patterns, "
              f"ignoring dest: {dest_to_ignore})...")
        try:
            structure = scan_directory_structure(
                source_path=source_dir,
                ignore_patterns=ignore_dirs,          # Pass directory ignore list
                whitelist_patterns=whitelist_files,   # CORRECT: Pass file whitelist
                destination_path=dest_to_ignore
            )
        except Exception as e:
            messagebox.showerror("Scanning Error", f"An error occurred while scanning '{source_dir}':\n{e}")
            structure = None # Ensure structure is None on error
        print("Scan complete.")

        # --- Configure Treeview Tags (Before Populating) ---
        # Ensure images are ready
        self._initialize_checkbox_images()
        # Configure tags with the corresponding images
        self.tree.tag_configure('checked', image=self._get_checkbox_image(True))
        self.tree.tag_configure('unchecked', image=self._get_checkbox_image(False))
        self.tree.tag_configure('placeholder', foreground='gray') # Style for empty folder placeholders


        # --- Populate Tree ---
        if structure is not None:
            self._populate_treeview(structure) # Pass the scanned structure
        elif source_dir: # Check if structure is None despite valid source_dir
            print("Scan returned no structure.") # Log if scan failed silently

    # --- Selection Handling ---

    def _handle_click(self, event):
        """Handles left-clicks on tree items to toggle their selection state."""
        region = self.tree.identify_region(event.x, event.y)

        # Only process clicks on the 'tree' area (where checkboxes/text are)
        if region != "tree":
            return

        item_id = self.tree.identify_row(event.y)
        if not item_id:
            return # Clicked in the tree area but not on an item

        # Ignore clicks on placeholder items
        if 'placeholder' in self.tree.item(item_id, 'tags'):
            return

        # Toggle the state
        current_state = self._item_states.get(item_id, False)
        new_state = not current_state
        self._set_item_state(item_id, new_state)

        # --- Cascade changes ---
        if 'folder' in self.tree.item(item_id, 'tags'):
            self._update_descendants_state(item_id, new_state)

        # Update ancestor states based on children
        self._update_ancestors_state(item_id)

    def _set_item_state(self, item_id, checked):
        """Sets the visual and internal state of a tree item."""
        if item_id not in self._item_states:
            print(f"Warning: Attempted to set state for unknown item_id: {item_id}")
            return

        # Update internal state map
        self._item_states[item_id] = checked

        # Update visual state using tags
        tags = list(self.tree.item(item_id, 'tags'))
        # Remove old state tag, add new one
        if 'checked' in tags: tags.remove('checked')
        if 'unchecked' in tags: tags.remove('unchecked')
        # Ensure base type tag (file/folder) remains
        if 'placeholder' not in tags: # Don't change state of placeholder
            tags.append('checked' if checked else 'unchecked')
            self.tree.item(item_id, tags=tuple(tags))

    def _update_descendants_state(self, item_id, checked):
        """Recursively updates the state of all descendant items."""
        children = self.tree.get_children(item_id)
        for child_id in children:
            if 'placeholder' in self.tree.item(child_id, 'tags'):
                continue # Skip placeholders
            self._set_item_state(child_id, checked)
            # Recurse only if it's a folder itself
            if 'folder' in self.tree.item(child_id, 'tags'):
                self._update_descendants_state(child_id, checked)

    def _update_ancestors_state(self, item_id):
        """Updates the state of ancestor folders based on children states."""
        parent_id = self.tree.parent(item_id)
        if not parent_id:
            return # Reached the root of the tree

        # Check state of all siblings (direct children of the parent)
        all_siblings = self.tree.get_children(parent_id)
        # Filter out placeholders when determining parent state
        relevant_siblings = [sid for sid in all_siblings if 'placeholder' not in self.tree.item(sid, 'tags')]

        if not relevant_siblings: # Parent only contains placeholders or is empty
             # Decide parent state - perhaps default to unchecked?
             self._set_item_state(parent_id, False)
        else:
            # Determine if all relevant siblings are checked
            all_checked = all(self._item_states.get(sib_id, False) for sib_id in relevant_siblings)
            # Optional: Implement partial check state here if desired
            self._set_item_state(parent_id, all_checked)

        # Recurse up the tree
        self._update_ancestors_state(parent_id)

    def _get_selected_paths(self, parent_id="", current_path=""):
        """
        Recursively traverses the tree state and returns a list of relative paths
        for selected items (files or folders).

        Returns:
            list[str]: A list of relative paths. Folders have a trailing separator.
        """
        selected = []
        children = self.tree.get_children(parent_id)

        for item_id in children:
            if 'placeholder' in self.tree.item(item_id, 'tags'):
                continue # Skip placeholder items

            item_text = self.tree.item(item_id, 'text')
            # Build relative path safely using os.path.join
            rel_path = os.path.join(current_path, item_text) if current_path else item_text
            is_folder = 'folder' in self.tree.item(item_id, 'tags')
            is_checked = self._item_states.get(item_id, False)

            if is_checked:
                # If an item is checked, add its path
                path_to_add = rel_path
                if is_folder:
                    # Append OS-specific separator to indicate it's a directory
                    path_to_add += os.sep
                selected.append(path_to_add)
                # Important: If a folder is checked, we DO NOT recurse further into it.
                # Its selection implies selecting everything within it.
            elif is_folder:
                 # If a folder is NOT checked, recurse into it to find selected children
                 selected.extend(self._get_selected_paths(item_id, rel_path))
            # else: file is not checked, do nothing

        return selected


    # --- Button Actions ---

    def _browse_source_directory(self):
        """Opens a dialog to select the source project directory and updates the tree."""
        directory = filedialog.askdirectory(
            title="Select Source Project Folder",
            initialdir=self.source_dir_var.get() if os.path.isdir(self.source_dir_var.get()) else None
        )
        if directory: # If a directory was selected (not cancelled)
            print(f"Source directory selected: {directory}")
            self.source_dir_var.set(directory)
            self._update_treeview() # Populate tree after selecting source
        else:
            print("Source directory selection cancelled.")

    def _browse_dest_directory(self):
        """Opens a dialog to select the destination directory and potentially updates the tree."""
        directory = filedialog.askdirectory(
            title="Select Destination Folder",
            initialdir=self.dest_dir_var.get() if os.path.isdir(self.dest_dir_var.get()) else None
            )
        if directory:
            print(f"Destination directory selected: {directory}")
            old_dest = self.dest_dir_var.get()
            self.dest_dir_var.set(directory)
            # Re-scan ONLY if the destination actually changed AND
            # the new destination is inside the source (or the old one was and the new one isn't)
            source_dir = self.source_dir_var.get()
            if source_dir and "No source selected" not in source_dir and directory != old_dest:
                 abs_source = os.path.abspath(source_dir)
                 abs_new_dest = os.path.abspath(directory)
                 new_dest_is_inside = os.path.commonpath([abs_source, abs_new_dest]) == abs_source

                 old_dest_was_inside = False
                 if old_dest and "No destination selected" not in old_dest and os.path.exists(old_dest):
                      abs_old_dest = os.path.abspath(old_dest)
                      old_dest_was_inside = os.path.commonpath([abs_source, abs_old_dest]) == abs_source

                 if new_dest_is_inside or old_dest_was_inside:
                      print("Destination changed and affects source view, updating tree...")
                      self._update_treeview() # Re-populate tree to reflect ignore changes
        else:
            print("Destination directory selection cancelled.")


    def _load_defaults(self):
        """Loads default file selections from config."""
        print("Load Defaults button clicked")
        source_dir = self.source_dir_var.get()
        if not source_dir or "No source selected" in source_dir or not os.path.isdir(source_dir):
             messagebox.showwarning("Load Defaults", "Please select a valid source directory first.")
             return

        if not self._path_to_item_id:
            messagebox.showinfo("Load Defaults", "Tree is empty or not yet populated.")
            return

        # --- Placeholder for loading from config_manager ---
        # Example: defaults_list = config_manager.load_defaults_config(source_dir)
        defaults_list = [ # Dummy data for testing
             "README.md",
             "context_selector" + os.sep, # Select the whole folder
             # "main.py" # Example of a specific file
             ]
        if not defaults_list:
             messagebox.showinfo("Load Defaults", "No default selection found or loaded.")
             return
        # --- End Placeholder ---

        print(f"Applying defaults: {defaults_list}")
        # Clear current selection first
        self._clear_selection()

        # Apply loaded defaults
        applied_count = 0
        for path in defaults_list:
            is_folder_path = path.endswith(os.sep)
            clean_path = path.rstrip(os.sep) # Remove trailing slash for lookup

            item_id = self._path_to_item_id.get(clean_path)
            if item_id:
                # Check if the item type matches the path type (folder vs file)
                is_tree_item_folder = 'folder' in self.tree.item(item_id, 'tags')
                if is_folder_path == is_tree_item_folder:
                    self._set_item_state(item_id, True)
                    if is_tree_item_folder:
                        self._update_descendants_state(item_id, True)
                    self._update_ancestors_state(item_id) # Update parents after setting child
                    applied_count += 1
                    print(f"  Applied default: {path}")
                else:
                    print(f"  Skipping default (type mismatch): {path}")

            else:
                print(f"  Warning: Default path not found in tree: {path}")

        if applied_count > 0:
            messagebox.showinfo("Load Defaults", f"Applied {applied_count} default selections.")
        else:
            messagebox.showwarning("Load Defaults", "Could not apply any of the loaded default selections.")


    def _save_defaults(self):
        """Saves current file selections as defaults."""
        print("Save Defaults button clicked")
        source_dir = self.source_dir_var.get()
        if not source_dir or "No source selected" in source_dir or not os.path.isdir(source_dir):
             messagebox.showwarning("Save Defaults", "Please select a valid source directory first.")
             return

        selected_paths = self._get_selected_paths()
        if not selected_paths:
             if not messagebox.askyesno("Save Defaults", "No items are currently selected.\nDo you want to save an empty default selection?"):
                 return
             else:
                  print("Saving empty selection as default.")

        # --- Placeholder for saving via config_manager ---
        try:
             # result = config_manager.save_defaults_config(source_dir, selected_paths)
             # if result:
             #     messagebox.showinfo("Save Defaults", f"Current selection saved as default for:\n{source_dir}")
             # else:
             #     messagebox.showerror("Save Defaults", "Failed to save default selection.")
             print(f"Attempting to save {len(selected_paths)} selected paths for {source_dir}:")
             for p in selected_paths: print(f"  - {p}")
             messagebox.showinfo("Save Defaults", "Default selection saved (simulation).") # Placeholder message
        except Exception as e:
             messagebox.showerror("Save Defaults", f"An error occurred while saving defaults:\n{e}")
        # --- End Placeholder ---


    def _clear_selection(self):
        """Clears the current selection in the treeview."""
        print("Clear Selection button clicked")
        if not self._item_states: # Tree is empty or not populated
            return
        # Set all top-level items to unchecked, which will cascade down via _set_item_state -> _update_descendants
        for item_id in self.tree.get_children():
             if self._item_states.get(item_id, False): # Only trigger update if it was checked
                self._set_item_state(item_id, False)
                if 'folder' in self.tree.item(item_id, 'tags'):
                    self._update_descendants_state(item_id, False)


    def _prepare_context(self):
        """Starts the process of copying selected files."""
        source_dir = self.source_dir_var.get()
        dest_dir = self.dest_dir_var.get()

        # --- Validation ---
        if not source_dir or "No source selected" in source_dir or not os.path.isdir(source_dir):
             messagebox.showerror("Prepare Context", "Please select a valid source directory.")
             return
        if not dest_dir or "No destination selected" in dest_dir:
             messagebox.showerror("Prepare Context", "Please select a destination directory.")
             return

        # Ensure destination exists or ask to create it
        if not os.path.isdir(dest_dir):
            try:
                if messagebox.askyesno("Create Directory?", f"Destination directory does not exist:\n{dest_dir}\n\nCreate it?"):
                    os.makedirs(dest_dir)
                    print(f"Created destination directory: {dest_dir}")
                else:
                    print("Destination directory creation cancelled by user.")
                    return # Stop if user cancels creation
            except OSError as e:
                messagebox.showerror("Prepare Context", f"Failed to create destination directory:\n{dest_dir}\n\n{e}")
                return

        # --- Get Selected Items ---
        selected_paths = self._get_selected_paths()
        if not selected_paths:
             messagebox.showinfo("Prepare Context", "No files or folders selected to prepare context.")
             return

        print(f"Prepare Context button clicked!")
        print(f"  Source: {source_dir}")
        print(f"  Destination: {dest_dir}")
        print(f"  Selected relative paths ({len(selected_paths)}):")
        for p in selected_paths: print(f"    - {p}")


        # --- Placeholder for file copying logic ---
        # This should ideally be in file_handler.py
        # It needs to:
        # 1. Clear the destination directory (maybe ask user first?)
        # 2. Iterate through selected_paths:
        #    - If it's a file path, calculate source/destination paths.
        #    - If it's a folder path (ends in /), find all files recursively within that source subfolder.
        # 3. For each file to copy:
        #    - Generate the flattened destination filename (e.g., path___to___file.ext.txt)
        #    - Copy the file.
        #    - Optionally prepend the original path comment inside the copied file.
        # 4. Handle potential errors (permissions, file not found etc.)
        # 5. Show progress/completion message.

        try:
            # Example call (function doesn't exist yet in file_handler):
            # from .file_handler import copy_selected_files
            # copied_count, errors = copy_selected_files(source_dir, dest_dir, selected_paths, clear_dest=True)
            # if errors:
            #     messagebox.showwarning("Prepare Context", f"Context prepared with {len(errors)} errors. Copied {copied_count} files.")
            # else:
            #     messagebox.showinfo("Prepare Context", f"Context prepared successfully. Copied {copied_count} files to:\n{dest_dir}")

            # Simulation for now:
            messagebox.showinfo("Prepare Context", f"Context preparation initiated (simulation).\nWould copy files related to {len(selected_paths)} selected paths.\nCheck console for details.")

        except Exception as e:
            messagebox.showerror("Prepare Context", f"An unexpected error occurred during context preparation:\n{e}")
        # --- End Placeholder ---