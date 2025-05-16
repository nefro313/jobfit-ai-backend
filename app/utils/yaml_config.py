from pathlib import Path
from typing import Any

import yaml

from app.api.error_handlers import CustomExceptionError
from app.core.logging import get_logger

logger = get_logger(__name__)

def load_yaml_configs(config_file_path) -> dict[str, Any]:
    """
    Load and parse YAML configuration files for agents and tasks.
    
    Returns:
        Dict[str, Any]: Dictionary containing loaded configurations
        
    Raises:
        CustomExceptionError: If configuration files cannot be loaded or parsed
    """
    logger.debug("Loading ATS checker configurations")
    configs = {}
    
    try:
        for config_type, file_path in config_file_path.items():
            path = Path(file_path)
            if not path.exists():
                logger.error(f"Configuration file not found: {file_path}")
                raise FileNotFoundError(f"Missing configuration file: {file_path}")
                
            with open(path, encoding="utf-8") as file:
                configs[config_type] = yaml.safe_load(file)
                logger.debug(f"Successfully loaded {config_type} configuration")
                
        return configs
    except (yaml.YAMLError, FileNotFoundError) as e:
        logger.error(f"Failed to load configurations: {str(e)}", exc_info=True)
        raise CustomExceptionError("Failed to load configurationse") from e