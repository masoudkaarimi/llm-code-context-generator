import argparse
import logging
import os
from typing import Any, Dict, List, Optional, Set

import pathspec
from tqdm import tqdm

# Import TOML library with fallback for older Python versions
try:
    import tomllib
except ImportError:
    # For Python < 3.11, tomli is required
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None

# Default Configuration
DEFAULT_ALLOWED_DIRS: List[str] = []
DEFAULT_IGNORED_DIRS: Set[str] = {'.git', '.github', '.vscode', '.idea', 'node_modules', '__pycache__', 'venv'}
DEFAULT_IGNORED_FILES: Set[str] = {'.env', '.env.example', '.env.local', '.env.production', '.env.development', }
DEFAULT_IGNORED_EXTENSIONS: Set[str] = {'.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.zip', '.pdf', '.pyc', '.o', '.so', '.lock', '.log', '.DS_Store'}


def setup_logging():
    """Configures basic logging for the script."""
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


def setup_arg_parser() -> argparse.ArgumentParser:
    """Sets up the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="A CLI tool to consolidate project source code into a single context file for LLMs.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "root_directory",
        type=str,
        nargs='?',
        default=".",
        help="The root directory of the project to scan. Defaults to the current directory."
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default=None,
        help="Path to the output file. Defaults to '[project_name]_context.md'."
    )
    return parser


def load_config(root_path: str) -> Dict[str, Any]:
    """Loads configuration from pyproject.toml if it exists, merging with defaults."""
    config = {
        "allowed_dirs": DEFAULT_ALLOWED_DIRS,
        "ignored_dirs": DEFAULT_IGNORED_DIRS.copy(),
        "ignored_files": DEFAULT_IGNORED_FILES.copy(),
        "ignored_extensions": DEFAULT_IGNORED_EXTENSIONS.copy(),
    }
    config_path = os.path.join(root_path, 'pyproject.toml')

    if tomllib and os.path.isfile(config_path):
        logging.info(f"Loading project configuration from: pyproject.toml")

        try:
            with open(config_path, 'rb') as f:
                pyproject_data = tomllib.load(f)

            user_config = pyproject_data.get("tool", {}).get("llmcontext", {})

            if user_config:
                logging.info("Found [tool.llmcontext] section. Applying custom config.")
                config["allowed_dirs"] = user_config.get("allowed_dirs", DEFAULT_ALLOWED_DIRS)
                config["ignored_dirs"].update(user_config.get("ignored_dirs", []))
                config["ignored_files"].update(user_config.get("ignored_files", []))
                config["ignored_extensions"].update(user_config.get("ignored_extensions", []))
            else:
                logging.info("No [tool.llmcontext] section found in pyproject.toml. Using default ignore lists.")

        except Exception as e:
            logging.error(f"Error reading or parsing pyproject.toml: {e}")
    else:
        if not tomllib:
            logging.warning("TOML library isn't found (install with 'pip install tomli' for Python < 3.11). Skipping pyproject.toml.")
        else:
            logging.info("No pyproject.toml found. Using default ignore lists.")

    return config


def load_gitignore_spec(root_path: str) -> Optional[pathspec.PathSpec]:
    """Loads .gitignore rules from the root directory if it exists."""
    gitignore_path = os.path.join(root_path, '.gitignore')
    if os.path.isfile(gitignore_path):
        with open(gitignore_path, 'r', encoding='utf-8') as f:
            return pathspec.PathSpec.from_lines('gitwildmatch', f)
    return None


def discover_files(root_path: str, config: Dict[str, Any], spec: Optional[pathspec.PathSpec]) -> List[str]:
    """Discovers all files to be processed, filtering ignored ones."""
    files_to_process = []
    for dirpath, dirnames, filenames in os.walk(root_path, topdown=True):
        if config["allowed_dirs"] and os.path.samefile(dirpath, root_path):
            dirnames[:] = [d for d in dirnames if d in config["allowed_dirs"]]

        dirnames[:] = [d for d in dirnames if d not in config["ignored_dirs"]]

        if spec:
            dirs_to_remove = {d for d in dirnames if spec.match_file(os.path.relpath(os.path.join(dirpath, d), root_path).replace(os.path.sep, '/'))}
            dirnames[:] = [d for d in dirnames if d not in dirs_to_remove]

        for filename in filenames:
            if filename in config["ignored_files"] or any(filename.endswith(ext) for ext in config["ignored_extensions"]):
                continue

            full_path = os.path.join(dirpath, filename)
            relative_path = os.path.relpath(full_path, root_path).replace(os.path.sep, '/')
            if spec and spec.match_file(relative_path):
                continue

            files_to_process.append(full_path)
    return files_to_process


def main():
    """Main execution function."""
    setup_logging()
    parser = setup_arg_parser()
    args = parser.parse_args()

    root_directory = os.path.abspath(args.root_directory)
    if not os.path.isdir(root_directory):
        logging.error(f"Error: Root directory not found at '{root_directory}'")
        return

    try:
        config = load_config(root_directory)
        project_name = os.path.basename(root_directory)
        output_file = args.output or f"{project_name}_context.md"

        logging.info(f"Starting to process project: '{project_name}'")

        gitignore_spec = load_gitignore_spec(root_directory)
        files_to_process = discover_files(root_directory, config, gitignore_spec)

        with open(output_file, 'w', encoding='utf-8', errors='ignore') as f:
            f.write(f"# Context for Project: {project_name}\n\n")
            logging.info(f"Processing {len(files_to_process)} files...")

            for full_path in tqdm(files_to_process, desc="Writing context file", unit="file"):
                try:
                    with open(full_path, 'r', encoding='utf-8', errors='ignore') as content_handle:
                        content = content_handle.read()
                    relative_path = os.path.relpath(full_path, root_directory).replace(os.path.sep, '/')
                    _, extension = os.path.splitext(relative_path)
                    lang = extension.lstrip('.')
                    f.write(f"## File: `{relative_path}`\n\n```{lang}\n{content}\n```\n\n---\n\n")
                except Exception as e:
                    logging.warning(f"Could not read or process file {full_path}: {e}")

        logging.info(f"✅ Successfully created context file: {output_file}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}", exc_info=False)


if __name__ == "__main__":
    main()
