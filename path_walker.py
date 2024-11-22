import os
from datetime import datetime
import fnmatch
from pathlib import Path

def load_gitignore(path):
    """Load .gitignore patterns and convert them to proper glob patterns"""
    gitignore_patterns = set()
    gitignore_path = os.path.join(path, '.gitignore')
    
    if os.path.exists(gitignore_path):
        with open(gitignore_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    # Convert .gitignore pattern to glob pattern
                    pattern = line.replace('\\', '/')
                    
                    # Handle directory patterns
                    if pattern.endswith('/'):
                        pattern = f"**/{pattern}**"
                    else:
                        pattern = f"**/{pattern}"
                        
                    # Add both with and without leading slash
                    gitignore_patterns.add(pattern)
                    if pattern.startswith('**/'):
                        gitignore_patterns.add(pattern[3:])
    
    return gitignore_patterns

def should_ignore(path, base_path, patterns):
    """Check if a path should be ignored using glob patterns"""
    # Get relative path from base_path
    try:
        rel_path = os.path.relpath(path, base_path).replace('\\', '/')
    except ValueError:
        return False
        
    # Always ignore .git directory
    if '.git' in Path(rel_path).parts:
        return True
        
    # Check each pattern
    for pattern in patterns:
        # Direct match
        if fnmatch.fnmatch(rel_path, pattern):
            return True
            
        # Check if any parent directory matches
        path_parts = Path(rel_path).parts
        for i in range(len(path_parts)):
            partial_path = '/'.join(path_parts[:i+1])
            if fnmatch.fnmatch(partial_path, pattern):
                return True
            
            # Also check with trailing slash for directories
            if fnmatch.fnmatch(f"{partial_path}/", pattern):
                return True
    
    return False

def print_directory_structure(startpath, output_file, allowed_types = ('.ts', '.tsx', '.py')):
    # Convert to absolute path and normalize
    startpath = os.path.abspath(startpath)
    
    # Get current date and time
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Load gitignore patterns
    gitignore_patterns = load_gitignore(startpath)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        # Write header with metadata
        f.write(f"Scan Report\n")
        f.write(f"===========\n")
        f.write(f"Date: {timestamp}\n")
        f.write(f"Source Directory: {startpath}\n")
        f.write(f"Output File: {os.path.abspath(output_file)}\n\n")
        
        # Write gitignore patterns if any were found
        if gitignore_patterns:
            f.write("Ignored Patterns (from .gitignore):\n")
            f.write("=================================\n")
            for pattern in sorted(gitignore_patterns):
                f.write(f"- {pattern}\n")
            f.write("\n")
        
        # Print directory structure
        f.write("Directory Structure:\n")
        f.write("===================\n\n")
        
        for root, dirs, files in os.walk(startpath):
            # Check if current directory should be ignored
            if should_ignore(root, startpath, gitignore_patterns):
                dirs[:] = []  # Skip all subdirectories
                continue
            
            # Calculate directory level for indentation
            try:
                level = len(Path(root).relative_to(Path(startpath)).parts)
            except ValueError:
                level = 0
                
            indent = '  ' * level
            f.write(f'{indent}{os.path.basename(root)}/\n')
            
            # Filter and sort files
            visible_files = []
            for file in sorted(files):
                full_path = os.path.join(root, file)
                if (file.endswith(allowed_types) and 
                    not should_ignore(full_path, startpath, gitignore_patterns)):
                    visible_files.append(file)
            
            # Print files
            subindent = '  ' * (level + 1)
            for file in visible_files:
                f.write(f'{subindent}{file}\n')
            
            # Filter directories based on gitignore
            i = 0
            while i < len(dirs):
                dir_path = os.path.join(root, dirs[i])
                if should_ignore(dir_path, startpath, gitignore_patterns):
                    dirs.pop(i)
                else:
                    i += 1
        
        # Print file contents
        f.write("\n\nFile Contents:\n")
        f.write("=============\n\n")
        
        for root, dirs, files in os.walk(startpath):
            if should_ignore(root, startpath, gitignore_patterns):
                continue
            
            for file in sorted(files):
                if not file.endswith(allowed_types):
                    continue
                
                full_path = os.path.join(root, file)
                if should_ignore(full_path, startpath, gitignore_patterns):
                    continue
                
                rel_path = os.path.relpath(full_path, startpath)
                f.write(f"\n--- {rel_path} ---\n")
                try:
                    with open(full_path, 'r', encoding='utf-8') as file_content:
                        f.write(file_content.read())
                except Exception as e:
                    f.write(f"\nError reading file: {str(e)}\n")
                f.write("\n")

# Usage example - make sure to run this from the parent directory containing both projects
now = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
os.makedirs('docs/history', exist_ok=True)
print_directory_structure('.', f'docs/history/structure-{now}.txt', ('.py', '.md'))
