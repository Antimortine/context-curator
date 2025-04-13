import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext # Import scrolledtext
import os
import traceback # For printing full tracebacks on error

# Import functions from local modules
from .file_handler import scan_directory_structure, copy_selected_files, save_tree_file
from .config_manager import (
    load_defaults_config, save_defaults_config, # Project defaults
    load_app_settings, save_app_settings        # App settings
)

class AppWindow:
    """
    Main application window for Context Curator.
    Handles UI setup, event handling, and orchestrates backend logic.
    """
    # Blacklist for DIRECTORIES (prevents descending into them)
    # Keeping user-provided list as requested
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

        # IDE / Editor specific config directories (Includes file patterns, kept as requested)
        ".vscode",
        ".idea",
        "*.sublime-project",
        "*.sublime-workspace",
        ".project",
        ".classpath",
        ".settings",
        ".windsurfrules",

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

        # Code coverage reporting
        ".lcov",
        ".nyc_output",
        "coverage",

        # Other
        "chroma_db",
        "logs",
        "temp",
        "tmp",
        "user_projects",
        "data",
    }
    # Whitelist for file patterns/names (used AFTER directory ignore)
    # Keeping user-provided list as requested
    DEFAULT_WHITELIST_FILE_PATTERNS = {
        # Common Code Files
        "*.py", "*.js", "*.ts", "*.jsx", "*.tsx", "*.java", "*.kt", "*.scala",
        "*.c", "*.cpp", "*.h", "*.hpp", "*.cs", "*.go", "*.rs", "*.rb", "*.php",
        "*.swift", "*.m", "*.mm", "*.pl", "*.pm", "*.lua", "*.dart", "*.groovy",
        "*.r", "*.sh", "*.bash", "*.zsh", "*.ps1", "*.bat", "*.cmd", "*.kts",
        # Common Config Files
        "*.json", "*.yaml", "*.yml", "*.xml", "*.toml", "*.ini", "*.cfg", "*.conf",
        "*.properties", "*.env.example", ".*rc", # e.g., .bashrc, .npmrc
        # Common Documentation / Text Files
        "*.md", "*.txt", "*.rst", "*.tex", "*.log", "*.csv", "*.tsv", "*.adoc",
        # Web Files
        "*.html", "*.htm", "*.css", "*.scss", "*.sass", "*.less", "*.vue", "*.svelte",
        "*.sql", "*.graphql", "*.gql",
        # Build System / Infra Files (Exact Matches)
        "Dockerfile", "docker-compose.yml", "docker-compose.yaml",
        "Makefile", "CMakeLists.txt", "requirements.txt", "requirements.in", "Pipfile",
        "pyproject.toml", "package.json", "pom.xml", "build.gradle", "settings.gradle",
        "gradlew", "gradlew.bat",
        "Cargo.toml", "go.mod", "go.sum", "composer.json", "Gemfile", "Rakefile",
        # Common Root Files (Exact Matches)
        "README", "README.*", # README.md, README.txt etc.
        "LICENSE", "LICENSE.*",
        "CONTRIBUTING", "CONTRIBUTING.*",
        "CHANGELOG", "CHANGELOG.*",
        "NOTICE", "AUTHORS", "SECURITY.md",
        # Add any other specific text-based formats relevant to your work
        '.env.example'
    }
    # Blacklist for specific FILES (applied AFTER whitelist)
    DEFAULT_BLACKLIST_FILE_PATTERNS = {
        "package-lock.json",
        "yarn.lock",
        "pnpm-lock.yaml",
        "*.jsx.html",
        ".DS_Store",
        "Thumbs.db",
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
        self._item_states = {} # Maps Treeview item ID -> bool (checked state)
        self._path_to_item_id = {} # Maps relative path -> Treeview item ID
        self._scanned_structure = None # Stores result of the last successful scan

        # --- Load Last Used Paths ---
        self._load_last_paths() # Call helper method

        # --- Create and Grid the Main Frame ---
        main_frame = ttk.Frame(self.master, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # --- Configure Grid Weights for Resizing ---
        self.master.rowconfigure(0, weight=1)
        self.master.columnconfigure(0, weight=1)
        # Adjust main_frame grid config slightly for new row
        main_frame.rowconfigure(2, weight=1) # Treeview row still expands most
        main_frame.rowconfigure(3, weight=0) # Text area row doesn't expand vertically by default
        main_frame.columnconfigure(0, weight=1) # Treeview/Text area column expands horizontally

        # --- Create Widgets INSIDE main_frame ---
        # 1. Source Directory Selection
        src_frame = ttk.LabelFrame(main_frame, text="Source Project Directory", padding="5")
        src_frame.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 5))
        src_frame.columnconfigure(1, weight=1)
        src_label = ttk.Label(src_frame, textvariable=self.source_dir_var, relief="sunken", background="white", anchor=tk.W)
        src_label.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 5))
        src_button = ttk.Button(src_frame, text="Browse...", command=self._browse_source_directory)
        src_button.grid(row=0, column=2, sticky=tk.E)

        # 2. Destination Directory Selection
        dest_frame = ttk.LabelFrame(main_frame, text="Destination Directory (for curated files)", padding="5")
        dest_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        dest_frame.columnconfigure(1, weight=1)
        dest_label = ttk.Label(dest_frame, textvariable=self.dest_dir_var, relief="sunken", background="white", anchor=tk.W)
        dest_label.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 5))
        dest_button = ttk.Button(dest_frame, text="Browse...", command=self._browse_dest_directory)
        dest_button.grid(row=0, column=2, sticky=tk.E)

        # 3. File Tree View Area
        tree_frame = ttk.LabelFrame(main_frame, text="Select Files and Folders", padding="5")
        tree_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S))
        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)

        # --- Create the Treeview ---
        self.tree = ttk.Treeview(tree_frame, selectmode='none', show='tree headings')
        self.tree.heading('#0', text='Project Structure', anchor=tk.W)
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        vsb.grid(row=0, column=1, sticky=(tk.N, tk.S))
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        hsb.grid(row=1, column=0, sticky=(tk.W, tk.E))
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.bind("<Button-1>", self._handle_click)

        # --- ADD: Text Area for Path Input ---
        text_input_frame = ttk.LabelFrame(main_frame, text="Apply Paths from Text", padding="5")
        text_input_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 5))
        text_input_frame.columnconfigure(0, weight=1) # Allow text area to expand horizontally

        self.path_text_area = scrolledtext.ScrolledText(text_input_frame, height=6, width=60, wrap=tk.WORD)
        self.path_text_area.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0,5))

        apply_text_button = ttk.Button(text_input_frame, text="Apply Paths", command=self._apply_paths_from_text)
        apply_text_button.grid(row=0, column=1, sticky=(tk.N, tk.E))
        # --- END ADD ---

        # --- Control Buttons Frame (Adjust row index) ---
        button_frame = ttk.Frame(main_frame, padding="5")
        button_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.S), pady=(5, 0)) # Row 4
        load_button = ttk.Button(button_frame, text="Load Default", command=self._load_defaults)
        load_button.grid(row=0, column=0, padx=(0, 5))
        save_button = ttk.Button(button_frame, text="Save Default", command=self._save_defaults)
        save_button.grid(row=0, column=1, padx=(0, 5))
        clear_button = ttk.Button(button_frame, text="Clear Selection", command=self._clear_selection)
        clear_button.grid(row=0, column=2, padx=(0, 5))

        # --- Prepare Context Button (Adjust row index) ---
        prepare_button = ttk.Button(main_frame, text="Prepare Context", command=self._prepare_context)
        prepare_button.grid(row=4, column=2, sticky=(tk.E, tk.S), pady=(5, 0)) # Row 4

        # --- Initialize checkbox images ---
        self._initialize_checkbox_images()

        # --- Initial Tree Population if Source Path was Restored ---
        restored_source = self.source_dir_var.get()
        if restored_source and "No source selected" not in restored_source and os.path.isdir(restored_source):
             print(f"Restored source path '{restored_source}', performing initial scan...")
             self.master.after(50, self._update_treeview) # Use small delay

    # --- NEW Helper Method ---
    def _load_last_paths(self):
        """Loads last used source and destination paths from app settings."""
        print("Attempting to load last used paths...")
        settings = load_app_settings()
        if not settings: print("No previous app settings found or failed to load."); return

        last_source = settings.get("last_source_dir")
        last_dest = settings.get("last_dest_dir")

        if last_source and os.path.isdir(last_source):
            print(f"Restoring last source directory: {last_source}"); self.source_dir_var.set(last_source)
        else:
            if last_source:
                print(f"Last source directory not found or invalid: {last_source}"); self.source_dir_var.set("No source selected")

        if last_dest and os.path.isdir(last_dest):
            print(f"Restoring last destination directory: {last_dest}"); self.dest_dir_var.set(last_dest)
        else:
            if last_dest:
                print(f"Last destination directory not found or invalid: {last_dest}"); self.dest_dir_var.set("No destination selected")

    # --- Checkbox Image Handling ---
    def _initialize_checkbox_images(self):
        """Pre-loads or prepares checkbox images using BitmapImage or text fallback."""
        if hasattr(self, '_checkbox_images') and self._checkbox_images: return
        self._checkbox_images = {}
        try:
            from tkinter import BitmapImage
            assets_dir = os.path.join(os.path.dirname(__file__), 'assets')
            checked_path = os.path.join(assets_dir, 'checked.xbm')
            unchecked_path = os.path.join(assets_dir, 'unchecked.xbm')
            if os.path.exists(checked_path): self._checkbox_images[True] = BitmapImage(file=checked_path, foreground="black", background="white")
            else: print(f"Warning: Checkbox image not found: {checked_path}. Using text fallback '[x]'."); self._checkbox_images[True] = "[x]"
            if os.path.exists(unchecked_path): self._checkbox_images[False] = BitmapImage(file=unchecked_path, foreground="black", background="white")
            else: print(f"Warning: Checkbox image not found: {unchecked_path}. Using text fallback '[ ]'."); self._checkbox_images[False] = "[ ]"
        except tk.TclError as e: print(f"Error loading checkbox bitmap images: {e}. Using text fallback."); self._checkbox_images[True] = "[x]"; self._checkbox_images[False] = "[ ]"
        except ImportError: print("Warning: tkinter.BitmapImage not available. Using text fallback."); self._checkbox_images[True] = "[x]"; self._checkbox_images[False] = "[ ]"
        except Exception as e: print(f"Unexpected error loading checkbox images: {e}. Using text fallback."); self._checkbox_images[True] = "[x]"; self._checkbox_images[False] = "[ ]"

    def _get_checkbox_image(self, checked):
        """Retrieves the pre-loaded checkbox image or text fallback."""
        if not hasattr(self, '_checkbox_images') or not self._checkbox_images: self._initialize_checkbox_images()
        return self._checkbox_images.get(checked, "[?]")

    # --- Treeview Population and Management ---
    def _populate_treeview(self, structure, parent_id="", current_rel_path=""):
        """Recursively populates the ttk.Treeview based on the scanned structure."""
        sorted_items = sorted(structure.items(), key=lambda item: (isinstance(item[1], dict), item[0].lower()))
        for name, content in sorted_items:
            item_type = "folder" if isinstance(content, dict) else "file"
            rel_path = os.path.join(current_rel_path, name) if current_rel_path else name
            item_id = self.tree.insert(parent_id, 'end', text=name, open=False, tags=(item_type,))
            self._item_states[item_id] = False; self._path_to_item_id[rel_path] = item_id
            self.tree.item(item_id, tags=(item_type, 'unchecked'))
            if item_type == "folder":
                if not content: self.tree.insert(item_id, 'end', text="...", tags=('placeholder',))
                else: self._populate_treeview(content, item_id, rel_path)

    def _update_treeview(self):
        """Clears and repopulates the treeview based on current settings."""
        source_dir = self.source_dir_var.get(); dest_dir = self.dest_dir_var.get()
        self.tree.delete(*self.tree.get_children())
        self._item_states.clear(); self._path_to_item_id.clear()
        self._scanned_structure = None # Reset stored structure

        if not source_dir or "No source selected" in source_dir or not os.path.isdir(source_dir): return

        ignore_dirs = set(self.DEFAULT_IGNORE_DIR_PATTERNS)
        whitelist_files = set(self.DEFAULT_WHITELIST_FILE_PATTERNS)
        blacklist_files = set(self.DEFAULT_BLACKLIST_FILE_PATTERNS)
        # print(f"DEBUG (app_window): Preparing scan. Ignore Dirs: {len(ignore_dirs)}, Whitelist Files: {len(whitelist_files)}, Blacklist Files: {len(blacklist_files)}")

        valid_dest = dest_dir and "No destination selected" not in dest_dir and os.path.exists(dest_dir)
        dest_to_ignore = dest_dir if valid_dest else None
        print(f"Scanning {source_dir} (ignoring dirs:{len(ignore_dirs)}, whitelisting files:{len(whitelist_files)}, blacklisting files:{len(blacklist_files)}, ignoring dest: {dest_to_ignore})...")

        structure = None # Initialize structure
        try:
            structure = scan_directory_structure(
                source_path=source_dir, ignore_patterns=ignore_dirs,
                whitelist_patterns=whitelist_files, blacklist_file_patterns=blacklist_files,
                destination_path=dest_to_ignore
            )
            self._scanned_structure = structure # Store the result on success
        except Exception as e:
            messagebox.showerror("Scanning Error", f"An error occurred while scanning '{source_dir}':\n{e}")
            # Keep self._scanned_structure as None
        print("Scan complete.")

        self._initialize_checkbox_images()
        self.tree.tag_configure('checked', image=self._get_checkbox_image(True))
        self.tree.tag_configure('unchecked', image=self._get_checkbox_image(False))
        self.tree.tag_configure('placeholder', foreground='gray')

        # Populate tree using the stored structure (if scan was successful)
        if self._scanned_structure is not None:
            self._populate_treeview(self._scanned_structure)
        elif source_dir:
            print("Scan returned no structure or failed.")

    # --- Selection Handling ---
    def _handle_click(self, event):
        """Handles left-clicks on tree items to toggle their selection state."""
        region = self.tree.identify_region(event.x, event.y);
        if region != "tree": return
        item_id = self.tree.identify_row(event.y)
        if not item_id or 'placeholder' in self.tree.item(item_id, 'tags'): return
        current_state = self._item_states.get(item_id, False); new_state = not current_state
        self._set_item_state(item_id, new_state)
        if 'folder' in self.tree.item(item_id, 'tags'): self._update_descendants_state(item_id, new_state)
        self._update_ancestors_state(item_id)

    def _set_item_state(self, item_id, checked):
        """Sets the visual and internal state of a tree item."""
        if item_id not in self._item_states: return
        self._item_states[item_id] = checked
        tags = list(self.tree.item(item_id, 'tags')); base_tag = tags[0]
        state_tag = 'checked' if checked else 'unchecked'
        if 'placeholder' not in tags: self.tree.item(item_id, tags=(base_tag, state_tag))

    def _update_descendants_state(self, item_id, checked):
        """Recursively updates the state of all descendant items."""
        for child_id in self.tree.get_children(item_id):
            if 'placeholder' in self.tree.item(child_id, 'tags'): continue
            self._set_item_state(child_id, checked)
            if 'folder' in self.tree.item(child_id, 'tags'): self._update_descendants_state(child_id, checked)

    def _update_ancestors_state(self, item_id):
        """Updates the state of ancestor folders based on children states."""
        parent_id = self.tree.parent(item_id);
        if not parent_id: return
        all_siblings = self.tree.get_children(parent_id)
        relevant_siblings = [sid for sid in all_siblings if 'placeholder' not in self.tree.item(sid, 'tags')]
        if not relevant_siblings: self._set_item_state(parent_id, False)
        else: all_checked = all(self._item_states.get(sib_id, False) for sib_id in relevant_siblings); self._set_item_state(parent_id, all_checked)
        self._update_ancestors_state(parent_id)

    def _get_selected_paths(self, parent_id="", current_path=""):
        """Recursively traverses tree state returning relative paths for selected items."""
        selected = []
        for item_id in self.tree.get_children(parent_id):
            if 'placeholder' in self.tree.item(item_id, 'tags'): continue
            item_text = self.tree.item(item_id, 'text')
            rel_path = os.path.join(current_path, item_text) if current_path else item_text
            is_folder = 'folder' in self.tree.item(item_id, 'tags')
            is_checked = self._item_states.get(item_id, False)
            if is_checked: selected.append(rel_path + os.sep if is_folder else rel_path)
            elif is_folder: selected.extend(self._get_selected_paths(item_id, rel_path))
        return selected

    # --- Button Actions ---
    def _browse_source_directory(self):
        """Opens dialog to select source dir, updates tree, and saves path."""
        initial_dir = self.source_dir_var.get()
        if not initial_dir or "No source selected" in initial_dir or not os.path.isdir(initial_dir): initial_dir = None
        directory = filedialog.askdirectory(title="Select Source Project Folder", initialdir=initial_dir)
        if directory:
            print(f"Source directory selected: {directory}")
            self.source_dir_var.set(directory)
            current_settings = load_app_settings(); current_settings["last_source_dir"] = directory; save_app_settings(current_settings)
            self._update_treeview()
        else: print("Source directory selection cancelled.")

    def _browse_dest_directory(self):
        """Opens dialog to select destination dir, potentially updates tree, and saves path."""
        initial_dir = self.dest_dir_var.get()
        if not initial_dir or "No destination selected" in initial_dir or not os.path.isdir(initial_dir): initial_dir = None
        directory = filedialog.askdirectory(title="Select Destination Folder", initialdir=initial_dir)
        if directory:
            print(f"Destination directory selected: {directory}"); old_dest = self.dest_dir_var.get(); self.dest_dir_var.set(directory)
            current_settings = load_app_settings(); current_settings["last_dest_dir"] = directory; save_app_settings(current_settings)
            source_dir = self.source_dir_var.get()
            if source_dir and "No source selected" not in source_dir and directory != old_dest:
                 abs_source = os.path.abspath(source_dir); abs_new_dest = os.path.abspath(directory)
                 new_dest_is_inside = os.path.commonpath([abs_source, abs_new_dest]) == abs_source and abs_source != abs_new_dest
                 old_dest_was_inside = False
                 if old_dest and "No destination selected" not in old_dest and os.path.exists(old_dest): abs_old_dest = os.path.abspath(old_dest); old_dest_was_inside = os.path.commonpath([abs_source, abs_old_dest]) == abs_source and abs_source != abs_old_dest
                 if new_dest_is_inside or old_dest_was_inside: print("Destination changed and affects source view, updating tree..."); self._update_treeview()
        else: print("Destination directory selection cancelled.")

    def _load_defaults(self):
        """Loads default file selections from config file in source directory."""
        print("Load Defaults button clicked")
        source_dir = self.source_dir_var.get()
        if not source_dir or "No source selected" in source_dir or not os.path.isdir(source_dir): messagebox.showwarning("Load Defaults", "Please select a valid source directory first."); return
        if not self._path_to_item_id: messagebox.showinfo("Load Defaults", "Project tree is not populated."); return

        defaults_list = load_defaults_config(source_dir)
        if defaults_list is None:
            config_path = os.path.join(source_dir, ".context_curator_defaults.json")
            if not os.path.exists(config_path): messagebox.showinfo("Load Defaults", "No default config file found.")
            else: messagebox.showerror("Load Defaults", f"Failed to load defaults config file.\nCheck console for details.")
            return
        if not defaults_list: messagebox.showinfo("Load Defaults", "No default selections found in config file."); return

        print(f"Applying {len(defaults_list)} defaults..."); self._clear_selection()
        applied_count = 0
        items_to_update_ancestors_for = set()
        successfully_applied_item_ids = set() # <-- Keep track of applied IDs

        for path in defaults_list:
            is_folder_path = path.endswith(os.sep); clean_path = path.rstrip(os.sep)
            item_id = self._path_to_item_id.get(clean_path)
            if item_id:
                is_tree_item_folder = 'folder' in self.tree.item(item_id, 'tags')
                if is_folder_path == is_tree_item_folder:
                    self._set_item_state(item_id, True)
                    items_to_update_ancestors_for.add(item_id)
                    successfully_applied_item_ids.add(item_id) # <-- Add ID here
                    if is_tree_item_folder: self._update_descendants_state(item_id, True)
                    applied_count += 1
                else: print(f"  Skipping default (type mismatch): {path}")
            else: print(f"  Warning: Default path not found in tree: {path}")

        print("Updating ancestor states...")
        for item_id in items_to_update_ancestors_for: self._update_ancestors_state(item_id)
        print("Ancestor update complete.")

        # --- ADD: Ensure visibility ---
        print("Ensuring selected items are visible...")
        for item_id in successfully_applied_item_ids:
            self._ensure_visible(item_id)
        print("Visibility update complete.")
        # --- END ADD ---
        if applied_count > 0: messagebox.showinfo("Load Defaults", f"Applied {applied_count} default selections.")
        else: messagebox.showwarning("Load Defaults", "Could not apply any loaded defaults.")

    def _save_defaults(self):
        """Saves current file selections as defaults in the source directory."""
        print("Save Defaults button clicked")
        source_dir = self.source_dir_var.get()
        if not source_dir or "No source selected" in source_dir or not os.path.isdir(source_dir): messagebox.showwarning("Save Defaults", "Please select a valid source directory first."); return
        selected_paths = self._get_selected_paths()
        if not selected_paths:
             if not messagebox.askyesno("Save Defaults", "No items selected. Save empty default selection?"): print("Saving empty selection cancelled."); return
             else: print("Saving empty selection as default.")
        success = save_defaults_config(source_dir, selected_paths)
        if success: messagebox.showinfo("Save Defaults", f"Selection ({len(selected_paths)} items) saved as default for:\n{source_dir}")
        else: messagebox.showerror("Save Defaults", f"Failed to save default config file.\nCheck console for details.")

    def _clear_selection(self):
        """Clears the current selection in the treeview."""
        print("Clear Selection button clicked")
        if not self._item_states:
            print("No items in the tree state to clear.")
            return # No items to clear

        items_cleared = 0
        # Iterate through top-level items (direct children of the root '')
        for item_id in self.tree.get_children():
             # Check if the item exists in our state dictionary AND is currently checked
             if item_id in self._item_states and self._item_states[item_id]:
                # Set the state of this top-level item to False
                self._set_item_state(item_id, False)
                items_cleared += 1
                # --- Explicitly cascade the change downwards ---
                # Check if it's a folder before trying to update descendants
                # Use try-except just in case item somehow disappeared
                try:
                    if 'folder' in self.tree.item(item_id, 'tags'):
                        print(f"  Cascading clear for folder: {self.tree.item(item_id, 'text')}")
                        self._update_descendants_state(item_id, False)
                except tk.TclError:
                     print(f"  Warning: Could not access item '{item_id}' during clear cascade.")

        if items_cleared > 0:
             print(f"Cleared selection state for {items_cleared} top-level items and their descendants.")
             # Optional: Add a messagebox confirmation?
             # messagebox.showinfo("Clear Selection", "Selection cleared.")
        else:
             print("No items were selected to clear.")

    # --- ADD NEW Helper Method ---
    def _ensure_visible(self, item_id):
        """
        Ensures a treeview item is visible by expanding its ancestors.
        """
        parent_id = self.tree.parent(item_id)
        while parent_id: # Loop until we reach the root ('')
            # Check if already open to potentially avoid unnecessary calls (optional)
            # if not self.tree.item(parent_id, 'open'):
            #     self.tree.item(parent_id, open=True)
            # Simpler: just call open=True, it's idempotent if already open
            try:
                self.tree.item(parent_id, open=True)
            except tk.TclError:
                 # Handle cases where parent_id might be invalid unexpectedly
                 print(f"Warning: TclError trying to open parent '{parent_id}' for item '{item_id}'")
                 break # Stop trying to go further up if error occurs
            parent_id = self.tree.parent(parent_id) # Move to the next parent

    # --- End NEW Helper Method ---

    # --- NEW Method: Apply Paths from Text Area ---
    def _parse_paths_from_text(self, text_content):
        """Parses lines of text to extract relative paths, ignoring comments."""
        paths = set() # Use set to avoid duplicates
        lines = text_content.splitlines()
        for line in lines:
            stripped_line = line.strip()
            if not stripped_line: continue # Skip empty lines
            space_index = stripped_line.find(' ')
            path_part = stripped_line[:space_index].strip() if space_index != -1 else stripped_line
            if path_part:
                 normalized_path = path_part.replace('/', os.sep).replace('\\', os.sep) # Normalize to OS sep
                 paths.add(normalized_path)
        return list(paths) # Return as a list

    def _apply_paths_from_text(self):
        """Applies the selection based on paths parsed from the text area."""
        print("Apply Paths from Text button clicked")
        source_dir = self.source_dir_var.get()
        if not source_dir or "No source selected" in source_dir or not os.path.isdir(source_dir): messagebox.showwarning("Apply Paths", "Please select a valid source directory first."); return
        if not self._path_to_item_id: messagebox.showinfo("Apply Paths", "Project tree is not populated."); return

        text_content = self.path_text_area.get("1.0", tk.END)
        if not text_content.strip(): messagebox.showinfo("Apply Paths", "Text area is empty."); return

        paths_to_select = self._parse_paths_from_text(text_content)
        if not paths_to_select: messagebox.showinfo("Apply Paths", "No valid paths found in the text area."); return

        print(f"Applying {len(paths_to_select)} paths from text...")
        clear_first = messagebox.askyesno("Apply Paths", "Clear existing selection before applying?", default='yes', icon='question')
        if clear_first: print("Clearing existing selection..."); self._clear_selection()

        applied_count = 0
        not_found_count = 0
        items_to_update_ancestors_for = set()
        successfully_applied_item_ids = set() # <-- Keep track of applied IDs
        for path in paths_to_select:
            is_folder_path = path.endswith(os.sep); clean_path = path.rstrip(os.sep)
            item_id = self._path_to_item_id.get(clean_path)
            if item_id:
                self._set_item_state(item_id, True)
                items_to_update_ancestors_for.add(item_id)
                successfully_applied_item_ids.add(item_id) # <-- Add ID here
                if 'folder' in self.tree.item(item_id, 'tags'): self._update_descendants_state(item_id, True)
                applied_count += 1
            else: print(f"  Warning: Path from text not found in tree: {path}"); not_found_count += 1

        print("Updating ancestor states...")
        for item_id in items_to_update_ancestors_for: self._update_ancestors_state(item_id)
        print("Ancestor update complete.")

        # --- ADD: Ensure visibility ---
        print("Ensuring selected items are visible...")
        for item_id in successfully_applied_item_ids:
            self._ensure_visible(item_id)
        print("Visibility update complete.")
        # --- END ADD ---

        summary_message = f"Applied {applied_count} paths from text."
        if not_found_count > 0: summary_message += f"\nCould not find {not_found_count} paths in the tree."
        messagebox.showinfo("Apply Paths Complete", summary_message)
        # Optional: Clear text area after applying?
        # self.path_text_area.delete("1.0", tk.END)

    # --- Prepare Context Action ---
    def _prepare_context(self):
        """Validates inputs, gets confirmation, calls copy_selected_files, and saves tree.txt."""
        source_dir = self.source_dir_var.get(); dest_dir = self.dest_dir_var.get()
        # Validation
        if not source_dir or "No source selected" in source_dir or not os.path.isdir(source_dir): messagebox.showerror("Error", "Please select a valid source directory."); return
        if not dest_dir or "No destination selected" in dest_dir: messagebox.showerror("Error", "Please select a destination directory."); return
        if os.path.abspath(source_dir) == os.path.abspath(dest_dir): messagebox.showerror("Error", "Source and destination directories cannot be the same."); return
        # Get Selection
        selected_paths = self._get_selected_paths()
        if not selected_paths: messagebox.showinfo("Prepare Context", "No files or folders selected."); return
        # Check Scan Data
        if self._scanned_structure is None: messagebox.showerror("Error", "Project structure not scanned or scan failed."); return
        # Confirmations
        if not os.path.isdir(dest_dir):
            if not messagebox.askyesno("Create Directory?", f"Destination directory does not exist:\n{dest_dir}\n\nCreate it?", icon='question', default='yes'): print("Destination directory creation cancelled."); return
        should_clear = False
        try:
             if os.path.exists(dest_dir) and os.listdir(dest_dir):
                  should_clear = messagebox.askyesno("Clear Destination?", f"The destination directory:\n{dest_dir}\n\nis not empty. Do you want to remove its contents before copying?\n\nWARNING: This cannot be undone!", icon='warning', default='no')
                  print(f"User chose {'not ' if not should_clear else ''}to clear destination directory.")
        except OSError as e: messagebox.showerror("Error", f"Could not check destination directory contents:\n{e}"); return
        # Log Intent
        print(f"\n--- Initiating Prepare Context ---"); print(f"Source: {source_dir}"); print(f"Destination: {dest_dir}"); print(f"Selected paths ({len(selected_paths)}):");
        for i, p in enumerate(selected_paths):
            if i < 10: print(f"  - {p}")
            elif i == 10: print("  ..."); break
        print(f"Clear destination confirmed: {should_clear}")
        # Call Copy Logic
        try:
            ignore_dirs = set(self.DEFAULT_IGNORE_DIR_PATTERNS); whitelist_files = set(self.DEFAULT_WHITELIST_FILE_PATTERNS); blacklist_files = set(self.DEFAULT_BLACKLIST_FILE_PATTERNS)
            copied_count, errors = copy_selected_files(
                source_root=source_dir, dest_root=dest_dir, selected_relative_paths=selected_paths,
                ignore_patterns=ignore_dirs, whitelist_patterns=whitelist_files, blacklist_file_patterns=blacklist_files,
                clear_dest=should_clear, prepend_path=True
            )
            # Generate Tree File
            tree_save_success = False
            if self._scanned_structure is not None:
                 tree_save_success = save_tree_file(self._scanned_structure, dest_dir)
                 if not tree_save_success: errors.append(("tree.txt", "Failed to save filtered tree structure file."))
            # Display Results
            if errors:
                error_summary = f"Context prepared with {len(errors)} errors.\nCopied {copied_count} files."
                if not tree_save_success and ("tree.txt", "Failed to save filtered tree structure file.") in errors: error_summary += "\nFailed to save tree.txt."
                elif tree_save_success: error_summary += "\nGenerated tree.txt."
                error_summary += "\n\nFirst few errors:\n"; max_err = 5
                for i, (path, msg) in enumerate(errors):
                    if i < max_err: error_summary += f"- {path}: {msg}\n"
                    elif i == max_err: error_summary += f"... ({len(errors) - max_err} more errors)"; break
                messagebox.showwarning("Prepare Context Complete (with errors)", error_summary)
            elif copied_count > 0:
                tree_msg = "\nGenerated tree.txt." if tree_save_success else "\nFailed to generate tree.txt."
                messagebox.showinfo("Prepare Context Complete", f"Successfully copied {copied_count} files to:\n{dest_dir}{tree_msg}")
            else:
                 tree_msg = "\nGenerated tree.txt." if tree_save_success else "\nFailed to generate tree.txt."
                 messagebox.showinfo("Prepare Context Complete", f"No files were copied.\n(Check selection and filters if unexpected).{tree_msg}")
        except Exception as e:
            print(f"FATAL Error during prepare context call: {e}"); traceback.print_exc();
            messagebox.showerror("Prepare Context Failed", f"An unexpected error occurred:\n{e}\n\nCheck console for details.")

# --- End of AppWindow class ---