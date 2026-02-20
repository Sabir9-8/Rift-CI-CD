"""
Utility functions for Rift Agent.
"""

import re
import shutil
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional


def extract_file_from_error(error_line: str) -> Optional[str]:
    """
    Extract file path from an error line.
    
    Args:
        error_line: Line containing error information.
        
    Returns:
        File path if found, None otherwise.
    """
    patterns = [
        r'File\s+"([^"]+)"',
        r'(/[^\s]+\.py)',
        r'([^\s]+\.py)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, error_line)
        if match:
            return match.group(1)
    
    return None


def extract_line_from_error(error_line: str) -> Optional[int]:
    """
    Extract line number from an error line.
    
    Args:
        error_line: Line containing error information.
        
    Returns:
        Line number if found, None otherwise.
    """
    patterns = [
        r'line\s+(\d+)',
        r':(\d+)\s*:',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, error_line)
        if match:
            return int(match.group(1))
    
    return None


def sanitize_branch_name(name: str) -> str:
    """
    Sanitize a string to be a valid Git branch name.
    
    Args:
        name: Original name.
        
    Returns:
        Sanitized branch name.
    """
    # Replace spaces and special chars with underscores
    sanitized = re.sub(r'[^\w\-.]', '_', name)
    # Remove consecutive underscores
    sanitized = re.sub(r'_+', '_', sanitized)
    # Remove leading/trailing underscores
    sanitized = sanitized.strip('_')
    return sanitized


def get_git_root(path: Path) -> Optional[Path]:
    """
    Find the Git root directory from a given path.
    
    Args:
        path: Starting path to search from.
        
    Returns:
        Path to Git root or None if not in a Git repo.
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=path,
            capture_output=True,
            text=True,
            check=True,
        )
        return Path(result.stdout.strip())
    except subprocess.CalledProcessError:
        return None


def parse_pytest_output(output: str) -> List[Dict[str, Any]]:
    """
    Parse pytest output to extract test failures.
    
    Args:
        output: Pytest stdout/stderr output.
        
    Returns:
        List of failure dictionaries.
    """
    failures = []
    
    # Pattern for failed test: test_file.py::test_name FAILED
    failed_pattern = re.compile(r'(.+?)(?:FAILED|ERROR)')
    
    for line in output.split('\n'):
        if 'FAILED' in line or 'ERROR' in line:
            match = failed_pattern.search(line)
            if match:
                failures.append({
                    "test": match.group(1).strip(),
                    "full_line": line.strip(),
                })
    
    return failures


def get_changed_files(repo_path: Path) -> List[str]:
    """
    Get list of changed files in the repository.
    
    Args:
        repo_path: Path to the repository.
        
    Returns:
        List of changed file paths.
    """
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True,
        )
        return [f.strip() for f in result.stdout.split('\n') if f.strip()]
    except subprocess.CalledProcessError:
        return []


def format_error_for_ai(errors: List[Dict[str, Any]]) -> str:
    """
    Format errors into a concise string for AI processing.
    
    Args:
        errors: List of error dictionaries.
        
    Returns:
        Formatted string.
    """
    formatted = []
    for i, error in enumerate(errors, 1):
        formatted.append(
            f"{i}. File: {error.get('file', 'unknown')}, "
            f"Line: {error.get('line', 'unknown')}, "
            f"Message: {error.get('message', 'unknown')}"
        )
    return "\n".join(formatted)


def validate_github_token(token: str) -> bool:
    """
    Validate a GitHub token by making a test API call.
    
    Args:
        token: GitHub token to validate.
        
    Returns:
        True if valid, False otherwise.
    """
    try:
        from github import Github
        g = Github(token)
        # Try to get user info
        g.get_user()
        return True
    except Exception:
        return False


def get_repo_info(repo_url: str) -> Dict[str, str]:
    """
    Extract owner and repository name from URL.
    
    Args:
        repo_url: GitHub repository URL.
        
    Returns:
        Dictionary with 'owner' and 'repo' keys.
    """
    match = re.search(r'github\.com[/:]([^/]+)/([^/.]+)', repo_url)
    if match:
        return {
            "owner": match.group(1),
            "repo": match.group(2).replace('.git', ''),
        }
    return {"owner": "", "repo": ""}


# ============================================
# GitHub CLI (gh) Helper Functions
# ============================================

def check_gh_available() -> bool:
    """
    Check if GitHub CLI (gh) is installed.
    
    Returns:
        True if gh is available, False otherwise.
    """
    return shutil.which("gh") is not None


def check_gh_authenticated() -> bool:
    """
    Check if gh CLI is authenticated with GitHub.
    
    Returns:
        True if authenticated, False otherwise.
    """
    try:
        result = subprocess.run(
            ["gh", "auth", "status"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        # If return code is 0, user is authenticated
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def create_pr_with_gh(
    repo_url: str,
    branch_name: str,
    title: str,
    body: str,
    base_branch: str = "main"
) -> Optional[int]:
    """
    Create a pull request using GitHub CLI (gh).
    
    Args:
        repo_url: GitHub repository URL.
        branch_name: Name of the branch with changes.
        title: PR title.
        body: PR body/description.
        base_branch: Base branch to merge into (default: main).
        
    Returns:
        PR number if successful, None otherwise.
    """
    if not check_gh_available():
        print("gh CLI not available")
        return None
    
    if not check_gh_authenticated():
        print("gh CLI not authenticated")
        return None
    
    try:
        # Parse repo for gh command
        # gh pr create --repo owner/repo --head branch --base base --title "title" --body "body"
        match = re.search(r'github\.com[/:]([^/]+)/([^/.]+)', repo_url)
        if not match:
            print(f"Could not parse repo URL: {repo_url}")
            return None
        
        owner = match.group(1)
        repo = match.group(2).replace('.git', '')
        repo_full = f"{owner}/{repo}"
        
        # Escape quotes in body for shell
        escaped_body = body.replace('"', '\\"')
        escaped_title = title.replace('"', '\\"')
        
        result = subprocess.run(
            [
                "gh", "pr", "create",
                "--repo", repo_full,
                "--head", branch_name,
                "--base", base_branch,
                "--title", escaped_title,
                "--body", escaped_body,
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        
        if result.returncode == 0:
            # Extract PR number from output
            # Output format: https://github.com/owner/repo/pull/123
            pr_match = re.search(r'/pull/(\d+)', result.stdout)
            if pr_match:
                pr_number = int(pr_match.group(1))
                print(f"Successfully created PR #{pr_number}")
                return pr_number
            print(f"PR created but couldn't extract number. Output: {result.stdout}")
            return 1  # Return 1 to indicate success even without number
        else:
            print(f"gh pr create failed: {result.stderr}")
            return None
            
    except subprocess.TimeoutExpired:
        print("gh pr create timed out")
        return None
    except Exception as e:
        print(f"Error creating PR with gh: {e}")
        return None


def fork_repo(repo_url: str, token: str) -> Optional[str]:
    """
    Fork a repository using GitHub API.
    
    Args:
        repo_url: GitHub repository URL to fork.
        token: GitHub token with appropriate permissions.
        
    Returns:
        URL of the forked repository if successful, None otherwise.
    """
    import requests
    
    # Extract owner and repo from URL
    match = re.search(r'github\.com[/:]([^/]+)/([^/.]+)', repo_url)
    if not match:
        print(f"Could not parse repo URL: {repo_url}")
        return None
    
    owner = match.group(1)
    repo_name = match.group(2).replace('.git', '')
    
    # Check if we already have a fork of this repo
    try:
        from github import Github
        g = Github(token)
        user = g.get_user()
        
        # Try to get the user's fork
        try:
            fork = g.get_repo(f"{owner}/{repo_name}")
            # Check if this is already a fork owned by the user
            if fork.fork:
                # It's already forked
                user_fork = g.get_repo(f"{user.login}/{repo_name}")
                print(f"Already forked: {user_fork.clone_url}")
                return user_fork.clone_url
        except Exception:
            pass
        
        # Fork the repo
        print(f"Forking {owner}/{repo_name}...")
        original_repo = g.get_repo(f"{owner}/{repo_name}")
        original_repo.create_fork()
        
        # Wait a bit for fork to be created
        import time
        time.sleep(3)
        
        # Get the forked repo
        user_fork = g.get_repo(f"{user.login}/{repo_name}")
        print(f"Fork created: {user_fork.clone_url}")
        return user_fork.clone_url
        
    except Exception as e:
        print(f"Error forking repo: {e}")
        return None

