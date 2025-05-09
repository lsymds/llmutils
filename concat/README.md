# llmutils-concat

A utility for concatenating files while respecting gitignore patterns. Perfect for creating context files for LLM prompts.

Completely and shamelessly inspired by [Simon Willison's Files to Prompt](https://github.com/simonw/files-to-prompt/) project.

## Installation

```bash
pip install -e .
```

## Usage

After installation, the `llmutils-concat` command will be available in your terminal:

```bash
# Concatenate all files, respecting .gitignore
llmutils-concat

# Bypass gitignore patterns
llmutils-concat --bypass-gitignore

# Specify additional patterns to ignore
llmutils-concat --ignore "*.log" --ignore "temp/*"

# Specify specific paths to include
llmutils-concat "*.py" "src/*.js"

# Combine options
llmutils-concat "*.py" --ignore "__pycache__/*" --bypass-gitignore
```

## Options

- `-b, --bypass-gitignore`: Ignore .gitignore files when scanning for files to concatenate
- `-i, --ignore TEXT`: Path patterns to ignore (can be used multiple times)
- `--help`: Show help message and exit

## Output Format

The utility outputs files in this format:

```
--- File: path/to/file.ext ---

[file content here]

--- End File: path/to/file.ext ---

```

## Use with LLMs

This utility is designed to help create context files for Large Language Models.

## License

MIT
