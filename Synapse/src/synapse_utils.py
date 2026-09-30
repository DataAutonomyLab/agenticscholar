from pathlib import Path
import datetime
from datetime import UTC

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PLAN_DIR = PROJECT_ROOT / "src" / "defined_plans"
ROUTING_DIR = PROJECT_ROOT / "src" / "routing"
CONFIG_DIR = PROJECT_ROOT / "src"/ "config"

def get_routing_path():
    """Get path to file in defined routing directory"""
    return ROUTING_DIR

def get_plan_path():
    """Get path to file in defined plans directory"""
    return PLAN_DIR

def get_data_path():
    """Get path to file in data directory"""
    return DATA_DIR

def get_config_path():
    """Get path to file in config directory"""
    return CONFIG_DIR

def get_cur_time():
    return datetime.datetime.now(UTC).isoformat()

