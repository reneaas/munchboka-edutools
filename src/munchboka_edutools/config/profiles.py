"""Configuration profiles for book building."""

import yaml
from pathlib import Path
from typing import Dict, Any, List
from dataclasses import dataclass, field


@dataclass
class ProcessorConfig:
    """Configuration for a single processor."""
    name: str
    enabled: bool = True
    priority: int = 50
    settings: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BuildProfile:
    """A named configuration profile for building books."""
    name: str
    description: str = ""
    processors: List[ProcessorConfig] = field(default_factory=list)
    build_options: Dict[str, Any] = field(default_factory=dict)


class ProfileManager:
    """Manage build profiles and configurations."""
    
    DEFAULT_PROFILES = {
        "default": {
            "description": "Default profile with basic enhancements",
            "processors": [
                {"name": "typography", "enabled": True},
                {"name": "page_breaks", "enabled": True},
                {"name": "math_rendering", "enabled": True},
            ],
            "build_options": {
                "builder": "html",
            }
        },
        "print": {
            "description": "Optimized for high-quality print output",
            "processors": [
                {
                    "name": "typography",
                    "enabled": True,
                    "settings": {
                        "smart_quotes": True,
                        "non_breaking_spaces": True,
                        "number_formatting": True,
                    }
                },
                {
                    "name": "page_breaks",
                    "enabled": True,
                    "settings": {
                        "break_before_chapters": True,
                    }
                },
                {
                    "name": "math_rendering",
                    "enabled": True,
                    "settings": {
                        "enhance_equation_numbers": True,
                    }
                },
            ],
            "build_options": {
                "builder": "pdfhtml",
            }
        },
        "web": {
            "description": "Optimized for web viewing",
            "processors": [
                {"name": "typography", "enabled": False},
                {"name": "page_breaks", "enabled": False},
                {"name": "math_rendering", "enabled": True},
            ],
            "build_options": {
                "builder": "html",
            }
        },
    }
    
    def __init__(self, config_file: Path = None):
        """Initialize profile manager.
        
        Args:
            config_file: Optional path to custom profiles YAML file
        """
        self.profiles: Dict[str, BuildProfile] = {}
        self._load_default_profiles()
        
        if config_file and config_file.exists():
            self._load_custom_profiles(config_file)
    
    def _load_default_profiles(self) -> None:
        """Load built-in default profiles."""
        for name, config in self.DEFAULT_PROFILES.items():
            self.profiles[name] = self._dict_to_profile(name, config)
    
    def _load_custom_profiles(self, config_file: Path) -> None:
        """Load custom profiles from YAML file."""
        with open(config_file, 'r') as f:
            custom_profiles = yaml.safe_load(f)
        
        if custom_profiles and 'profiles' in custom_profiles:
            for name, config in custom_profiles['profiles'].items():
                self.profiles[name] = self._dict_to_profile(name, config)
    
    def _dict_to_profile(self, name: str, config: Dict[str, Any]) -> BuildProfile:
        """Convert dictionary config to BuildProfile."""
        processors = []
        for proc_config in config.get('processors', []):
            processors.append(ProcessorConfig(
                name=proc_config['name'],
                enabled=proc_config.get('enabled', True),
                priority=proc_config.get('priority', 50),
                settings=proc_config.get('settings', {})
            ))
        
        return BuildProfile(
            name=name,
            description=config.get('description', ''),
            processors=processors,
            build_options=config.get('build_options', {})
        )
    
    def get_profile(self, name: str) -> BuildProfile:
        """Get a profile by name.
        
        Args:
            name: Profile name
            
        Returns:
            BuildProfile instance
            
        Raises:
            KeyError: If profile doesn't exist
        """
        if name not in self.profiles:
            available = ', '.join(self.profiles.keys())
            raise KeyError(f"Profile '{name}' not found. Available: {available}")
        
        return self.profiles[name]
    
    def list_profiles(self) -> List[str]:
        """List all available profile names."""
        return list(self.profiles.keys())
    
    def save_profile(self, profile: BuildProfile, config_file: Path) -> None:
        """Save a profile to YAML file.
        
        Args:
            profile: Profile to save
            config_file: Path to save to
        """
        # Load existing profiles if file exists
        profiles_dict = {}
        if config_file.exists():
            with open(config_file, 'r') as f:
                data = yaml.safe_load(f) or {}
                profiles_dict = data.get('profiles', {})
        
        # Add/update profile
        profiles_dict[profile.name] = {
            'description': profile.description,
            'processors': [
                {
                    'name': p.name,
                    'enabled': p.enabled,
                    'priority': p.priority,
                    'settings': p.settings,
                }
                for p in profile.processors
            ],
            'build_options': profile.build_options,
        }
        
        # Write back
        with open(config_file, 'w') as f:
            yaml.dump({'profiles': profiles_dict}, f, default_flow_style=False)
