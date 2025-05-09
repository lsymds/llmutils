import click
import os
import glob
import fnmatch
import pathlib

@click.command()
@click.argument('paths', nargs=-1, type=click.Path(exists=True))
@click.option(
  "--ignore",
  "-i",
  "ignore_patterns",
  multiple=True,
  default=[],
  help="Path patterns to ignore"
)
@click.option(
  "--bypass-gitignore",
  "-b",
  "bypass_gitignore",
  is_flag=True,
  help="Bypass the current directory's .gitignore file"
)
@click.option(
   "--exclude-content",
   "exclude_content",
   is_flag=True,
   help="Prevent the content being concatenated and solely concatenate the file names together"
)
def concat(
  bypass_gitignore,
  ignore_patterns,
  paths,
  exclude_content,
):
  click.echo(
    "bypass_gitignore: %s ignore_patterns: %s paths: %s exclude_content: %s"
    %
    (bypass_gitignore, ignore_patterns, paths, exclude_content)
  )

  # Use current directory if no paths specified
  if not paths:
    paths = [os.getcwd()]

  # Get gitignore patterns if not bypassed
  gitignore_patterns = []
  if not bypass_gitignore:
    gitignore_patterns = get_gitignore_patterns()
    click.echo(f"Loaded gitignore patterns: {gitignore_patterns}")

  all_files = []

  # Collect all files from specified paths, including subdirectories
  for path in paths:
    if os.path.isdir(path):
      # Handle directory - including all subdirectories
      for root, dirs, files in os.walk(path, topdown=True):
        # Filter directories based on gitignore
        if gitignore_patterns and not bypass_gitignore:
          i = 0
          while i < len(dirs):
            dir_path = os.path.join(root, dirs[i])
            if is_path_ignored(dir_path, ignore_patterns, gitignore_patterns):
              click.echo(f"Ignoring directory: {dir_path}")
              dirs.pop(i)
            else:
              i += 1

        # Add non-ignored files
        for file in files:
          file_path = os.path.join(root, file)
          if not is_path_ignored(file_path, ignore_patterns, gitignore_patterns):
            all_files.append(file_path)
    else:
      # Handle glob patterns
      if '*' in path or '?' in path:
        matched_files = glob.glob(path, recursive=True)
        for file_path in matched_files:
          if not is_path_ignored(file_path, ignore_patterns, gitignore_patterns):
            all_files.append(file_path)
      else:
        # Single file
        if not is_path_ignored(path, ignore_patterns, gitignore_patterns):
          all_files.append(path)

  # Sort files for consistent output
  all_files.sort()

  # Concatenate all files
  for file_path in all_files:
    try:
      if exclude_content:
        # Only output the file path if content is excluded
        click.echo(f"--- File: {file_path} ---")
        click.echo(f"--- End File: {file_path} ---")
      else:
        # Output both file path and content
        with open(file_path, 'r', encoding='utf-8') as f:
          content = f.read()
          click.echo(f"--- File: {file_path} ---\n")
          click.echo(content)
          click.echo(f"--- End File: {file_path} ---\n")
    except Exception as e:
      # Skip binary files and handle errors
      click.echo(f"Skipping {file_path}: {str(e)}", err=True)

def get_gitignore_patterns():
    """Parse .gitignore file from current directory and return patterns"""
    gitignore_path = os.path.join(os.getcwd(), '.gitignore')
    patterns = []

    if os.path.exists(gitignore_path):
        try:
            with open(gitignore_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    # Skip empty lines and comments
                    if line and not line.startswith('#'):
                        patterns.append(line)
        except Exception as e:
            click.echo(f"Error reading .gitignore: {str(e)}", err=True)

    return patterns

def is_path_ignored(path, ignore_patterns=None, gitignore_patterns=None):
    """Check if a path should be ignored based on ignore patterns and gitignore"""
    ignore_patterns = ignore_patterns or []
    gitignore_patterns = gitignore_patterns or []

    # Get normalized relative path
    try:
        rel_path = os.path.relpath(path, os.getcwd())
    except ValueError:
        rel_path = path

    # Normalize path separators
    rel_path = rel_path.replace(os.sep, '/')

    # Handle explicit ignore patterns
    for pattern in ignore_patterns:
        pattern = pattern.replace(os.sep, '/')
        if fnmatch.fnmatch(rel_path, pattern):
            return True

    # Handle gitignore patterns
    for pattern in gitignore_patterns:
        # Skip comments and empty lines
        if not pattern or pattern.startswith('#'):
            continue

        # Normalize pattern
        pattern = pattern.replace(os.sep, '/')

        # Handle directory patterns (ending with /)
        if pattern.endswith('/'):
            base_pattern = pattern[:-1]

            # Direct match for the directory itself
            if fnmatch.fnmatch(rel_path, base_pattern):
                return True

            # Check if it's a subdirectory or file within the matched directory
            if any(fnmatch.fnmatch(parent, base_pattern) for parent in get_parent_paths(rel_path)):
                return True

        # Handle normal file patterns
        elif fnmatch.fnmatch(rel_path, pattern):
            return True

        # Handle patterns without slashes (match anywhere in path)
        elif '/' not in pattern:
            path_parts = rel_path.split('/')
            # Check each path component against the pattern
            for part in path_parts:
                if fnmatch.fnmatch(part, pattern):
                    return True

    return False

def get_parent_paths(path):
    """
    For a path like 'a/b/c/d', returns ['a', 'a/b', 'a/b/c']
    Used to check if a file is within an ignored directory
    """
    parts = path.split('/')
    parents = []

    for i in range(1, len(parts)):
        parents.append('/'.join(parts[:i]))

    return parents
