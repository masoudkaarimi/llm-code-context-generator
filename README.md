# LLM Code Context Generator

[![PyPI version](https://badge.fury.io/py/llm-code-context-generator.svg)](https://badge.fury.io/py/llm-code-context-generator)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/llm-code-context-generator)
[![License: MIT](https://img.shields.io/github/license/masoudkaarimi/llm-code-context-generator.svg)](https://opensource.org/licenses/MIT)

![Demo of LLM Code Context Generator](https://raw.githubusercontent.com/masoudkaarimi/llm-code-context-generator/master/demo.gif)

A powerful command-line tool that scans any project, intelligently filters files, and combines all relevant source code into a single, clean file perfectly formatted for Large
Language Models (LLMs).

---

## The Problem

AI models like GPT-4, Claude, and Gemini are powerful, but they can't see your entire project. When you ask for help, you often get generic answers because the AI lacks the full
context. Manually copying and pasting code is slow, messy, and nearly impossible for large projects.

## The Solution

**LLM Code Context Generator** fixes this. It walks through your project directory, uses your .gitignore file, comprehensive built-in defaults, and a custom config to skip
irrelevant files, and creates one single, organized Markdown file.

You can paste this file into your favorite AI chat to give it the deep understanding it needs to provide truly helpful, project-aware answers.

## Key Features

- **🚀 Fast and Local**: Runs entirely on your machine, ensuring your code stays private and the process is quick.
- **🧠 Smart Filtering**: Automatically uses your `.gitignore` rules, plus powerful built-in defaults to skip common noise (like node_modules, .git, .log files, and media).
- **⚙️ Standardized Configuration**: Configure the tool using the standard `pyproject.toml` file, keeping your project root clean.
- **✨ Priority Overrides**: Explicitly allow specific files or extensions (like `.env` or `.md`) to bypass and override all ignore rules.
- **🤖 AI-Friendly Format**: The output is clean Markdown with language-specific code blocks, making it easy for LLMs to parse.
- **✅ Easy to Use**: Install with a single command and run it from anywhere on your system.

## Installation

You can install the tool directly from PyPI:

```bash
pip install llm-code-context-generator
```

After installation, the `llmcontext` command will be available in your terminal. You may need to restart your terminal for the command to be recognized the first time.

You can verify the installation by checking the help message:

```bash
llmcontext --help
```

## How to Use

Using the tool is simple and straightforward.

### Basic Usage

1. Open your terminal and navigate to your project's main folder:
   ```bash
   cd /path/to/your/project
   ```
2. Run the command:
   ```bash
   llmcontext
   ```

This will scan the current directory and create a context file named `[your-project-name]_context.md`.

### Advanced Usage

#### Scanning a Different Directory

You can scan any project folder without `cd`-ing into it first:

```bash
llmcontext /path/to/another/project
```

#### Specifying an Output File

Use the `-o` or `--output` flag to set a custom name and location for the context file:

```bash
llmcontext . -o my-api-context.md
```

## Configuration (via `pyproject.toml`)

For precise control, you can add a dedicated section to your project's `pyproject.toml` file. The tool will automatically find and use it. This is the recommended way to handle
project-specific configurations.

### Sample Configuration

Add a `[tool.llmcontext]` section to your `pyproject.toml` file like this:

```toml
# In your pyproject.toml file

[tool.llmcontext]

# --- IGNORE LISTS (Blacklists) ---
# These are added to the built-in defaults

# A list of directory names to ignore everywhere.
ignored_dirs = [
    "tests",
    "docs",
    "assets",
    "migrations"
]

# A list of exact filenames to ignore.
ignored_files = [
    "config.js",
    "docker-compose.yml",
    "manage.py"
]

# A list of file extensions to ignore.
ignored_extensions = [
    ".log",
    ".tmp",
    ".bak"
]


# --- ALLOW LISTS (Whitelists with Priority) ---

# A list of top-level directories to exclusively include.
# If not empty, only these directories will be scanned.
allowed_dirs = ["src", "app", "core"]

# A list of exact filenames to FORCE include,
# even if they are in .gitignore or default ignore lists.
allowed_files = [
    ".env.example",
    "README.md"
]

# A list of file extensions to FORCE include,
# even if they are ignored by default (e.g., .md, .json).
allowed_extensions = [
    ".md",
    ".json"
]
```

### Configuration Keys Explained

#### Blacklists (What to Ignore)

- `ignored_dirs`: An array of strings. The tool will completely skip any folder with these names (e.g., `"tests"`).
- `ignored_files`: An array of strings. The tool will skip any file that has one of these exact names (e.g., `"docker-compose.yml"`).
- `ignored_extensions`: An array of strings. The tool will skip any file ending with one of these extensions (e.g., `".log"`).

#### Whitelists (What to Include)

- `allowed_dirs`: An array of strings. If you add folders here (e.g., `"src"`), the tool will only look inside those folders at the top level.
- `allowed_files`: (Priority) An array of strings. Any file matching these exact names/paths (e.g., `"README.md"`) will be included, even if it's ignored by `.gitignore` or
  `ignored_extensions`.
- `allowed_extensions`: (Priority) An array of strings. Any file with these extensions (e.g., `".md"`) will be included, even if it's ignored by default. This is the key to
  including documentation or config files.

#### How Filtering and Priority Works

The tool applies rules in a specific order to give you maximum control:

1. `Priority 'Allow' Rules`: If a file matches `allowed_files` or `allowed_extensions`, it is always included. This overrides all other ignore rules.
2. `'Allowed Dirs' Rule`: If `allowed_dirs` is not empty, any file outside of those directories is skipped.
3. `'Ignore' Rules`: If a file matches any rule in `ignored_dirs`, `ignored_files`, `ignored_extensions`, the built-in defaults, or your `.gitignore` file, it is skipped.
4. `Default Include`: If a file is not caught by any of the rules above, it is included.

## Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the [issues page](https://github.com/masoudkaarimi/llm-code-context-generator/issues).

## License

This project is licensed under the MIT License.