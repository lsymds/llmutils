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

    for pattern in ignore_patterns:
        pattern = pattern.replace(os.sep, '/')
        if fnmatch.fnmatch(rel_path, pattern):
            return True

    for pattern in gitignore_patterns:
        if not pattern or pattern.startswith('#'):
            continue

        pattern = pattern.replace(os.sep, '/')

        if pattern.endswith('/'):
            base_pattern = pattern[:-1]

            if fnmatch.fnmatch(rel_path, base_pattern):
                return True

            if any(fnmatch.fnmatch(parent, base_pattern) for parent in get_parent_paths(rel_path)):
                return True

        elif fnmatch.fnmatch(rel_path, pattern):
            return True

        elif '/' not in pattern:
            path_parts = rel_path.split('/')
            for part in path_parts:
                if fnmatch.fnmatch(part, pattern):
                    return True

    return False

def get_parent_paths(path):
    parts = path.split('/')
    parents = []

    for i in range(1, len(parts)):
        parents.append('/'.join(parts[:i]))

    return parents
