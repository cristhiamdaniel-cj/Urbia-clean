"""
Configuración centralizada - Singleton Pattern
"""
import yaml
from pathlib import Path
from typing import Any, Dict


class Settings:
    """Configuración singleton"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance
    
    def _load_config(self) -> None:
        """Cargar configuración desde YAML"""
        config_path = Path(__file__).parent / "settings.yaml"
        
        if config_path.exists():
            with open(config_path, 'r') as f:
                self._config = yaml.safe_load(f)
        else:
            self._config = self._default_config()
    
    def _default_config(self) -> Dict[str, Any]:
        """Configuración por defecto"""
        return {
            'dashboard': {
                'port': 5000,
                'debug': True
            },
            'sensors': {
                'interval': {
                    'critical': 5,
                    'normal': 30,
                    'low': 120
                }
            },
            'gateways': {
                'norte': {'port': 5001},
                'sur': {'port': 5002}
            }
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """Obtener valor de configuración"""
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        
        return value if value is not None else default
