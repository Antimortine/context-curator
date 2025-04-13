
# Context Curator

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)

A simple GUI tool to help developers manually select relevant source files and documentation to build a focused context for Large Language Models (LLMs). It filters the project view based on ignore/whitelist/blacklist patterns and copies selected items into a flat structure suitable for LLM input.

## Problem

When trying to use LLMs for coding tasks (like implementing features, refactoring, or explaining code), providing the entire codebase as context is often infeasible due to token limits and performance degradation. The LLM gets overwhelmed or "loses focus" with too much irrelevant information (binaries, images, dependency folders, logs, etc.).

## Solution

Context Curator provides a simple graphical interface to:

1.  Visually browse your project's directory structure, automatically filtered to show likely relevant files.
2.  Manually select specific files and folders relevant to your current task using a checkbox-like interface.
3.  Save and load common selection sets *per project*.
4.  Remember the last used source and destination directories across sessions.
5.  Copy the selected files/folders into a designated destination folder.
6.  Copied files are renamed to include their original path (`path/to/file.ext` -> `path___to___file.ext.txt`) and have their original path prepended as a comment.
7.  Generate a `tree.txt` file in the destination, showing the complete *filtered* structure (what the tool considered potentially relevant).
8.  This curated set of files can then be easily concatenated or fed individually into your LLM prompt.

## Features

*   GUI based on Tkinter (standard Python library).
*   Browse and select source project directory.
*   Browse and select destination directory for curated context.
*   **Persistence:** Remembers last used source and destination paths between sessions.
*   **Advanced Filtering:**
    *   Directory ignore patterns (e.g., `.git`, `node_modules`, `venv`).
    *   File whitelist patterns (e.g., `*.py`, `*.js`, `*.md`, `Dockerfile`).
    *   Specific file blacklist patterns (e.g., `package-lock.json`, `*.jsx.html`).
*   Tree view display of the *filtered* source project structure.
*   Checkbox-like selection of files and folders.
*   Cascading selection (selecting/deselecting a folder affects its children).
*   **Project-Specific Defaults:** Save and load default file selections per project (`.context_curator_defaults.json`).
*   "Prepare Context" action:
    *   Copies selected files/folders (respecting filters when expanding selected folders).
    *   Flattens structure in destination using `___` as path separator.
    *   Prepends original source path inside copied files.
    *   Optionally clears destination directory (with confirmation).
    *   Generates `tree.txt` showing the filtered project structure.
*   "Clear Selection" button.

## Installation

1.  **Prerequisites:**
    *   Python 3.x (Tkinter is usually included, but ensure your Python installation has it: `python -m tkinter`).
    *   Git (for cloning).

2.  **Clone the repository:**
    ```bash
    git clone <your-repository-url>
    cd context-curator # Or your chosen project name
    ```

3.  **Set up a virtual environment (Recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

4.  **Install dependencies:**
    *(Currently, there should be no external dependencies if using only standard libraries)*
    ```bash
    # If requirements.txt exists and has content:
    # pip install -r requirements.txt
    ```

## Usage

1.  **Run the application:**
    ```bash
    python main.py
    ```
2.  **Select Directories:**
    *   Click "Browse..." for **Source Project Directory**. The application will remember your last choice.
    *   Click "Browse..." for **Destination Directory**. The application will remember your last choice.
3.  **View Filtered Tree:** The file tree will populate, showing only directories and files that pass the ignore/whitelist/blacklist filters defined in `app_window.py`.
4.  **Select Items:** Click on files or folders in the tree to select/deselect them. Selecting/deselecting a folder cascades to all its visible children.
5.  **Manage Defaults (Optional):**
    *   **Save Default:** Saves the current selection state to a `.context_curator_defaults.json` file *in the root of the selected Source Directory*. Useful for frequently needed files in a specific project.
    *   **Load Default:** Clears the current selection and applies the selections saved in the project's `.context_curator_defaults.json` file (if it exists).
    *   **Clear Selection:** Deselects all items in the tree.
6.  **Prepare Context:**
    *   Click the **"Prepare Context"** button.
    *   You will be asked to confirm if the destination directory should be created (if it doesn't exist).
    *   You will be asked to confirm if the destination directory should be cleared *only if* it already exists and contains files/folders (defaults to "No").
    *   The application copies the selected files and the contents of selected folders (respecting filters again during expansion) to the destination directory.
    *   Files are renamed (e.g., `src/utils/helpers.py` becomes `src___utils___helpers.py.txt`).
    *   A `tree.txt` file showing the complete filtered structure (not just selected items) is generated in the destination directory.
7.  **Use the Context:** The files in the destination directory (e.g., `src___utils___helpers.py.txt`) now contain the code/text with a header indicating the original path. You can concatenate these files or use them individually as context for your LLM. The `tree.txt` provides an overview.

## Configuration

Context Curator uses two types of configuration:

1.  **Application Settings (`~/.context_curator_app_settings.json`)**
    *   **Purpose:** Stores application-wide settings, currently the last used source and destination directory paths.
    *   **Location:** Saved automatically in your user home directory (`~` on Linux/macOS, `C:\Users\<YourUser>` on Windows).
    *   **Format:**
        ```json
        {
          "last_source_dir": "/path/to/your/last/project",
          "last_dest_dir": "/path/to/your/last/output",
          "version": 1
        }
        ```
    *   **Management:** Loaded on startup, saved automatically when you select directories via the "Browse..." buttons.

2.  **Project Defaults (`<SourceDir>/.context_curator_defaults.json`)**
    *   **Purpose:** Stores a specific set of selected files/folders *for a particular project*. Useful for quickly selecting core files, READMEs, etc.
    *   **Location:** Saved in the root of the **Source Project Directory** when you click "Save Default".
    *   **Format:**
        ```json
        {
          "version": 1,
          "selected_paths": [
            "README.md",
            "src/core/",
            "src/utils/helpers.py",
            "docs/architecture.md"
          ]
        }
        ```
        *(Note: Folder paths should end with the OS-specific separator, e.g., `/` or `\`)*
    *   **Management:** Loaded via the "Load Default" button, saved via the "Save Default" button.

*(Filtering patterns like ignore/whitelist/blacklist are currently hardcoded as constants in `context_selector/app_window.py`)*

## Contributing

Contributions are welcome! Please feel free to open an issue or submit a pull request. (Add more specific guidelines later if needed).

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.
