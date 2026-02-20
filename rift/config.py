"""
Configuration management for Rift Agent.
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class RiftConfig:
    """Configuration class for RiftAgent."""
    
    # GitHub Configuration
    github_token: str = ""
    repo_url: str = ""
    
    # Team Configuration
    team_name: str = ""
    leader_name: str = ""
    
    # OpenAI Configuration
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-3.5-turbo"
    openai_temperature: float = 0.3
    openai_max_tokens: int = 150
    
    # Repository Configuration
    clone_dir: str = "/tmp/repo_clone"
    default_branch: str = "main"
    
    # Test Configuration
    test_command: str = "pytest --tb=short"
    test_timeout: int = 300  # 5 minutes
    
    # Fix Configuration
    max_fixes: int = 5
    
    # Logging
    log_level: str = "INFO"
    
    @classmethod
    def from_env(cls) -> "RiftConfig":
        """Create configuration from environment variables."""
        return cls(
            github_token=os.environ.get("GITHUB_TOKEN", ""),
            repo_url=os.environ.get("REPO_URL", ""),
            team_name=os.environ.get("TEAM_NAME", ""),
            leader_name=os.environ.get("LEADER_NAME", ""),
            openai_api_key=os.environ.get("OPENAI_API_KEY"),
            openai_model=os.environ.get("OPENAI_MODEL", "gpt-3.5-turbo"),
            clone_dir=os.environ.get("CLONE_DIR", "/tmp/repo_clone"),
            default_branch=os.environ.get("DEFAULT_BRANCH", "main"),
            test_command=os.environ.get("TEST_COMMAND", "pytest --tb=short"),
            max_fixes=int(os.environ.get("MAX_FIXES", "5")),
            log_level=os.environ.get("LOG_LEVEL", "INFO"),
        )
    
    def validate(self) -> tuple[bool, str]:
        """
        Validate the configuration.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Token is now optional - gh CLI can be used as alternative
        if not self.repo_url:
            return False, "Repository URL is required"
        
        if not self.team_name:
            return False, "Team name is required"
        
        if not self.leader_name:
            return False, "Leader name is required"
        
        # If no token provided, warn but don't fail (gh CLI can be used)
        if not self.github_token:
            import logging
            logging.warning("No GitHub token provided. PR creation will rely on gh CLI authentication.")
        
        return True, ""


# Default configuration instance
default_config = RiftConfig()

