#!/usr/bin/env python3

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
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None

# --- Default Configuration ---
CONFIG_FILENAME = "pyproject.toml"

# --- IGNORED LISTS (Defaults) ---
DEFAULT_IGNORED_DIRS: Set[str] = {
    # VCS / IDE / Env
    '.git', '.github', '.vscode', '.idea', 'node_modules', '__pycache__', 'venv',
    # Common Python/Tooling envs
    '.venv', 'env', '.env', '.pytest_cache', '.mypy_cache', '.tox', 'htmlcov',
    # Build & dist outputs
    'build', 'dist', 'target', 'out', 'bin', 'obj', 'wheels', 'dist-packages',
    # OS & Cache
    '__MACOSX', '*.egg-info', 'site-packages', 'docs_build', 'builddocs',
    # Other common package manager dirs
    'bower_components', 'jspm_packages',
}

DEFAULT_IGNORED_FILES: Set[str] = {
    # Env files (these often contain secrets)
    '.env', '.env.local', '.env.production', '.env.development', '.env.test', '.env.*',
    # Lock files (not source code)
    'package-lock.json', 'yarn.lock', 'pnpm-lock.yaml',
    'poetry.lock', 'Pipfile.lock', 'composer.lock', 'Gemfile.lock', 'go.sum',
    # Editor swap/temp files
    '*.swp', '*.swo', '*.swn', '.*.swp',
    # OS temp/config files
    'thumbs.db',
    # CI/CD config files (can be noisy)
    '.travis.yml', 'circle.yml', 'appveyor.yml', 'Jenkinsfile',
}

DEFAULT_IGNORED_EXTENSIONS: Set[str] = {
    # --- Media: Images ---
    '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.webp', '.bmp', '.tiff', '.psd',
    # --- Media: Video & Audio ---
    '.mp4', '.mov', '.avi', '.mkv', '.webm', '.flv', 'wmv',
    '.mp3', '.wav', '.ogg', '.flac', '.m4a', 'aac',
    # --- Fonts ---
    '.woff', '.woff2', '.ttf', '.otf', '.eot',
    # --- Archives & Documents ---
    '.zip', '.rar', '.tar', '.gz', '.7z', '.bz2', 'tgz',
    '.pdf', '.docx', '.xlsx', '.pptx', '.epub', '.mobi', '.csv', '.xls', '.doc', '.ppt',
    # --- Python compiled/cache files ---
    '.pyc', '.pyo', '.pyd', '.o', '.so', '.a',
    # --- Logs / DBs / System ---
    '.log', '.lock', '.db', '.sqlite3', '.sqlitedb', '.dump', 'bak', '.tmp', '.dat',
    # --- OS & System Files ---
    '.DS_Store',
    # --- Compiled code from other languages ---
    '.class',  # Java
    '.dll', '.exe', '.lib',  # Windows/C++
    '.bin', '.iso', '.out', '.elf',  # Linux/Binary
    '.obj', '.o',  # Object files
    '.jar',  # Java Archive
    '.wasm',  # WebAssembly
    # --- Secrets / Keys (Crucial to ignore) ---
    '.key', '.pem', '.crt', '.cer', '.p12', '.pfx', '.jks', '.p7b', 'gpg',
    # --- Config / Docs / Scripts (from your original list) ---
    '.gitignore', '.gitattributes', '.dockerignore', '.gitkeep',
    '.md', '.markdown', '.rst',  # Documentation
    '.sh', '.bat', '.ps1', '.cmd',  # Shell scripts
    # --- Common Config Files (can be noisy) ---
    '.xml', '.json', '.yaml', '.yml', '.toml', '.ini',
}

# --- ALLOWED LISTS (Defaults) ---
DEFAULT_ALLOWED_DIRS: Set[str] = set()
DEFAULT_ALLOWED_FILES: Set[str] = set()
DEFAULT_ALLOWED_EXTENSIONS: Set[str] = set()


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
    """
    Loads configuration from pyproject.toml if it exists.
    - 'Ignored' lists from TOML are *added* to the defaults.
    - 'Allowed' lists from TOML *replace* the defaults.
    """

    config = {
        "allowed_dirs": DEFAULT_ALLOWED_DIRS.copy(),
        "allowed_files": DEFAULT_ALLOWED_FILES.copy(),
        "allowed_extensions": DEFAULT_ALLOWED_EXTENSIONS.copy(),
        "ignored_dirs": DEFAULT_IGNORED_DIRS.copy(),
        "ignored_files": DEFAULT_IGNORED_FILES.copy(),
        "ignored_extensions": DEFAULT_IGNORED_EXTENSIONS.copy(),
    }
    config_path = os.path.join(root_path, CONFIG_FILENAME)

    if tomllib and os.path.isfile(config_path):
        logging.info(f"Loading project configuration from: {CONFIG_FILENAME}")
        try:
            with open(config_path, 'rb') as f:
                pyproject_data = tomllib.load(f)
            # Config is under [tool.llmcontext]
            user_config = pyproject_data.get("tool", {}).get("llmcontext", {})

            if user_config:
                logging.info("Found [tool.llmcontext] section. Applying custom config.")

                # 'Allowed' lists *replace* the defaults
                config["allowed_dirs"] = set(user_config.get("allowed_dirs", DEFAULT_ALLOWED_DIRS))
                config["allowed_files"] = set(user_config.get("allowed_files", DEFAULT_ALLOWED_FILES))
                config["allowed_extensions"] = set(user_config.get("allowed_extensions", DEFAULT_ALLOWED_EXTENSIONS))

                # 'Ignored' lists *add to* the defaults
                config["ignored_dirs"].update(user_config.get("ignored_dirs", []))
                config["ignored_files"].update(user_config.get("ignored_files", []))
                config["ignored_extensions"].update(user_config.get("ignored_extensions", []))
            else:
                logging.info(f"No [tool.llmcontext] section found in {CONFIG_FILENAME}. Using defaults.")
        except Exception as e:
            logging.error(f"Error reading or parsing {CONFIG_FILENAME}: {e}")
    else:
        if not tomllib:
            logging.warning("TOML library not found. Skipping pyproject.toml. Install with 'pip install tomli' for Python < 3.11")
        else:
            logging.info(f"No {CONFIG_FILENAME} found. Using default ignore lists.")
    return config


def load_gitignore_spec(root_path: str) -> Optional[pathspec.PathSpec]:
    """Loads .gitignore rules from the root directory if it exists."""
    gitignore_path = os.path.join(root_path, '.gitignore')
    if os.path.isfile(gitignore_path):
        logging.info("Loading .gitignore rules.")
        with open(gitignore_path, 'r', encoding='utf-8') as f:
            return pathspec.PathSpec.from_lines('gitwildmatch', f)
    return None


def discover_files(root_path: str, config: Dict[str, Any], spec: Optional[pathspec.PathSpec]) -> List[str]:
    """
    Discovers all files to be processed, applying priority filtering.

    The filter priority is:
    1. (Priority) Include if in 'allowed_files' or 'allowed_extensions'.
    2. Exclude if not in 'allowed_dirs' (if 'allowed_dirs' is set).
    3. Exclude if in 'ignored_dirs', 'ignored_files', or 'ignored_extensions'.
    4. Exclude if matched by .gitignore ('spec').
    5. Include if not excluded by any above rule.
    """
    files_to_process = []

    allowed_dirs = config["allowed_dirs"]
    allowed_files = config["allowed_files"]
    allowed_extensions = config["allowed_extensions"]
    ignored_dirs = config["ignored_dirs"]
    ignored_files = config["ignored_files"]
    ignored_extensions = config["ignored_extensions"]

    # Ensure allowed_dirs are in POSIX format for consistent matching
    allowed_paths = [p.replace(os.path.sep, '/') for p in allowed_dirs]

    for dirpath, dirnames, filenames in os.walk(root_path, topdown=True):

        # --- Directory Filtering ---
        dirs_to_remove = set()
        for d in dirnames:
            # Check config 'ignored_dirs' (by name or relative path)
            relative_dir_path = os.path.relpath(os.path.join(dirpath, d), root_path).replace(os.path.sep, '/')
            if d in ignored_dirs or relative_dir_path in ignored_dirs:
                dirs_to_remove.add(d)

        # Check .gitignore
        if spec:
            for d in dirnames:
                if d in dirs_to_remove: continue
                relative_dir_path = os.path.relpath(os.path.join(dirpath, d), root_path).replace(os.path.sep, '/')
                # Add a trailing slash for directories to match .gitignore behavior
                if spec.match_file(relative_dir_path + '/'):
                    dirs_to_remove.add(d)

        dirnames[:] = [d for d in dirnames if d not in dirs_to_remove]

        # --- File Filtering (with Priority Logic) ---
        for filename in filenames:
            full_path = os.path.join(dirpath, filename)
            relative_path = os.path.relpath(full_path, root_path).replace(os.path.sep, '/')
            _, extension = os.path.splitext(filename)  # Use filename for extension

            # --- 1. Priority 'Allow' Check (Overrides all ignores) ---
            is_force_allowed = relative_path in allowed_files or \
                               (extension and extension in allowed_extensions)

            if is_force_allowed:
                files_to_process.append(full_path)
                continue  # Skip all other ignore checks

            # --- 2. 'allowed_dirs' Check (if specified) ---
            if allowed_paths:
                # Check if the file's path starts with any of the allowed directory paths
                is_allowed = any(relative_path.startswith(p) for p in allowed_paths)
                if not is_allowed:
                    continue  # Skip if not in an allowed path

            # --- 3. 'Ignored' Config Check ---
            if filename in ignored_files or \
                    relative_path in ignored_files or \
                    (extension and extension in ignored_extensions):
                continue

            # --- 4. '.gitignore' Check ---
            if spec and spec.match_file(relative_path):
                continue

            # --- 5. Add File ---
            # If it passed all checks, add it
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

        if not files_to_process:
            logging.warning("No files found to process. Check your ignore/allow configuration.")
            return

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

                except UnicodeDecodeError:
                    logging.warning(f"Skipping binary or non-UTF-8 file: {relative_path}")
                except Exception as e:
                    logging.warning(f"Could not read or process file {full_path}: {e}")

        logging.info(f"✅ Successfully created context file: {output_file}")

    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}", exc_info=True)


if __name__ == "__main__":
    main()
