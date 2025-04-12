# Context Curator

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)

A simple GUI tool to help developers manually select relevant source files and documentation to build a focused context for Large Language Models (LLMs). Think of it as a "RAG for the poor" approach, prioritizing manual curation over complex automated retrieval.

## Problem

When trying to use LLMs for coding tasks (like implementing features, refactoring, or explaining code), providing the entire codebase as context is often infeasible due to token limits and performance degradation. The LLM gets overwhelmed or "loses focus" with too much irrelevant information.

## Solution

Context Curator provides a simple graphical interface to:

1.  Visually browse your project's directory structure.
2.  Manually select specific files and folders relevant to your current task.
3.  Copy the selected files into a designated folder, renaming them to include their original path (`path/to/file.ext` -> `path___to___file.ext.txt`).
4.  This curated set of files can then be easily concatenated or fed individually into your LLM prompt.

## Features

*   GUI based on Tkinter (standard Python library).
*   Browse and select source project directory.
*   Browse and select destination directory for curated context.
*   Tree view display of the source project structure.
*   Checkbox-like selection of files and folders (selecting a folder selects its contents recursively).
*   Save and load default file selections for common project configurations (`.context_defaults.json`).
*   Copies selected files to the destination folder with path-encoded names.
*   (Future) Option to prepend the original path inside the copied file.
*   (Future) Ignore patterns (like `.gitignore`).


## Installation

1.  **Prerequisites:**
    *   Python 3.x (Tkinter is usually included, but ensure your Python installation has it).
    *   Git (for cloning).

2.  **Clone the repository:**
    ```bash
    git clone <your-repository-url>
    cd context-curator
    ```

3.  **Set up a virtual environment (Recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

4.  **Install dependencies (if any added later):**
    ```bash
    pip install -r requirements.txt
    ```
    *(Currently, there might be no external dependencies if using only standard libraries like Tkinter)*

## Usage

1.  **Run the application:**
    ```bash
    python main.py
    ```
2.  Click "Browse..." to select your **Source Project Directory**.
3.  Click "Browse..." to select your **Destination Directory** (where curated files will be copied). The destination directory will be cleared before copying (or you'll be prompted).
4.  The file tree of your source project will appear.
5.  Click on files or folders in the tree to select/deselect them. Use the buttons ("Load Default", "Save Default", "Clear Selection") to manage common selections.
6.  Once you've selected all relevant files/folders, click **"Prepare Context"**.
7.  The selected files will be copied and renamed in the destination directory.
8.  You can now use the contents of the destination directory as context for your LLM.

## Configuration (Default Selections)

You can save a set of frequently used file/folder selections as defaults.
*   Click **"Save current selection as default"** to save the currently selected paths.
*   This creates/overwrites a `.context_defaults.json` file in the root of your **Source Project Directory**.
*   Click **"Load default selection"** to automatically select the paths listed in `.context_defaults.json`.

The `.context_defaults.json` file looks like this:

```json
{
  "version": 1,
  "selected_paths": [
    "README.md",
    "src/core/",
    "src/models/user.py",
    "docs/architecture.md"
  ]
}
```

## Contributing

Contributions are welcome! Please feel free to open an issue or submit a pull request.

## License

This project is licensed under the [Apache License, Version 2.0](LICENSE).


