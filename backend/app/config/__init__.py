"""
Configuration Manager
Loads and manages configuration for agents.
"""

import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path


class ConfigManager:
    """Manages configuration for the analysis system"""

    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialize configuration manager
        
        Args:
            config_dir: Directory containing config files
        """
        if config_dir is None:
            # Default to config directory in the same directory as this file
            config_dir = Path(__file__).parent
        
        self.config_dir = Path(config_dir)
        self._agent_config: Optional[Dict[str, Any]] = None
        self._rules: Optional[Dict[str, Any]] = None

    def load_agent_config(self) -> Dict[str, Any]:
        """Load agent configuration"""
        if self._agent_config is None:
            config_path = self.config_dir / "agent_config.yaml"
            self._agent_config = self._load_yaml(config_path)
        return self._agent_config

    def load_rules(self) -> Dict[str, Any]:
        """Load analysis rules"""
        if self._rules is None:
            rules_path = self.config_dir / "rules.yaml"
            self._rules = self._load_yaml(rules_path)
        return self._rules

    def get_agent_config(self, agent_name: str) -> Dict[str, Any]:
        """
        Get configuration for a specific agent
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            Agent configuration dictionary
        """
        config = self.load_agent_config()
        return config.get(agent_name, {})

    def get_global_config(self) -> Dict[str, Any]:
        """Get global configuration"""
        config = self.load_agent_config()
        return config.get("global", {})

    def get_rules_for_agent(self, agent_type: str) -> Dict[str, Any]:
        """
        Get rules for a specific agent type
        
        Args:
            agent_type: Type of agent (e.g., 'security', 'quality')
            
        Returns:
            Rules dictionary
        """
        rules = self.load_rules()
        rule_key = f"{agent_type}_rules"
        return rules.get(rule_key, {})

    def is_agent_enabled(self, agent_name: str) -> bool:
        """
        Check if an agent is enabled
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            True if agent is enabled
        """
        agent_config = self.get_agent_config(agent_name)
        return agent_config.get("enabled", True)

    def _load_yaml(self, file_path: Path) -> Dict[str, Any]:
        """Load YAML file"""
        try:
            with open(file_path, 'r') as f:
                return yaml.safe_load(f) or {}
        except FileNotFoundError:
            print(f"Warning: Config file not found: {file_path}")
            return {}
        except yaml.YAMLError as e:
            print(f"Error parsing YAML file {file_path}: {e}")
            return {}

    def reload(self):
        """Reload all configuration"""
        self._agent_config = None
        self._rules = None


# Global config manager instance
_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """Get the global config manager instance"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager
