import click
import os
import glob
import fnmatch

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
def concat(
  bypass_gitignore,
  ignore_patterns,
  paths,
):
  if not paths:
    paths = [os.getcwd()]

  gitignore_patterns = []
  if not bypass_gitignore:
    gitignore_patterns = get_gitignore_patterns()

  all_files = []

  for path in paths:
    if os.path.isdir(path):
      for root, dirs, files in os.walk(path, topdown=True):
        if gitignore_patterns and not bypass_gitignore:
          i = 0
          while i < len(dirs):
            dir_path = os.path.join(root, dirs[i])
            if is_path_ignored(dir_path, ignore_patterns, gitignore_patterns):
              dirs.pop(i)
            else:
              i += 1

        for file in files:
          file_path = os.path.join(root, file)
          if not is_path_ignored(file_path, ignore_patterns, gitignore_patterns):
            all_files.append(file_path)
    else:
      if '*' in path or '?' in path:
        matched_files = glob.glob(path, recursive=True)
        for file_path in matched_files:
          if not is_path_ignored(file_path, ignore_patterns, gitignore_patterns):
            all_files.append(file_path)
      else:
        if not is_path_ignored(path, ignore_patterns, gitignore_patterns):
          all_files.append(path)

  all_files.sort()

  for file_path in all_files:
    try:
      with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        click.echo(f"--- File: {file_path} ---\n")
        click.echo(content)
        click.echo(f"--- End File: {file_path} ---\n")
    except Exception as e:
      click.echo(f"Skipping {file_path}: {str(e)}", err=True)

def get_gitignore_patterns():
    gitignore_path = os.path.join(os.getcwd(), '.gitignore')
    patterns = []

    if os.path.exists(gitignore_path):
        try:
            with open(gitignore_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        patterns.append(line)
        except Exception as e:
            click.echo(f"Error reading .gitignore: {str(e)}", err=True)

    return patterns

def is_path_ignored(path, ignore_patterns=None, gitignore_patterns=None):
    ignore_patterns = ignore_patterns or []
    gitignore_patterns = gitignore_patterns or []

    try:
        rel_path = os.path.relpath(path, os.getcwd())
    except ValueError:
        rel_path = path

    rel_path = rel_path.replace(os.sep, '/')

    # Handle explicit ignore patterns
    for pattern in ignore_patterns:
        pattern = pattern.replace(os.sep, '/')
        if is_pattern_match(pattern, rel_path):
            return True

    # Handle gitignore patterns
    for pattern in gitignore_patterns:
        if not pattern or pattern.startswith('#'):
            continue

        pattern = pattern.replace(os.sep, '/')
        if is_pattern_match(pattern, rel_path):
            return True

    return False

def is_pattern_match(pattern, path):
    """Check if a path matches a pattern according to gitignore rules."""
    # Exact match
    if fnmatch.fnmatch(path, pattern):
        return True

    # Directory pattern (ends with '/')
    if pattern.endswith('/'):
        base_pattern = pattern[:-1]
        # Match the exact directory
        if fnmatch.fnmatch(path, base_pattern):
            return True
        # Match if path is inside this directory
        if path.startswith(f"{base_pattern}/"):
            return True

    # Pattern without slash matches anywhere in path
    if '/' not in pattern:
        basename = os.path.basename(path)
        if fnmatch.fnmatch(basename, pattern):
            return True

        # Check each path component
        path_parts = path.split('/')
        for part in path_parts:
            if fnmatch.fnmatch(part, pattern):
                return True

    # Handle patterns like '[Oo]bj/' that should match any path component
    if pattern.endswith('/'):
        base_pattern = pattern[:-1]
        path_parts = path.split('/')

        # Check if any directory component matches the pattern
        for i in range(len(path_parts)):
            if fnmatch.fnmatch(path_parts[i], base_pattern):
                # If this is the last component and it's a file, don't match
                if i == len(path_parts) - 1 and not os.path.isdir(path):
                    continue
                return True

    return False
