import os
import logging
from datetime import datetime
from typing import Optional


class GameMacroLogger:
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = log_dir
        self._ensure_log_directory()
        self._setup_logger()
    
    def _ensure_log_directory(self):
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
    
    def _setup_logger(self):
        log_filename = os.path.join(
            self.log_dir, 
            f"gamemacro_{datetime.now().strftime('%Y%m%d')}.log"
        )
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_filename, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger('GameMacroAssistant')
    
    def log_error(self, error_code: str, message: str):
        error_message = f"[{error_code}] {message}"
        self.logger.error(error_message)
    
    def log_info(self, message: str):
        self.logger.info(message)
    
    def log_warning(self, message: str):
        self.logger.warning(message)


# Global logger instance
_logger_instance: Optional[GameMacroLogger] = None


def get_logger() -> GameMacroLogger:
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = GameMacroLogger()
    return _logger_instance


def log_error(error_code: str, message: str):
    logger = get_logger()
    logger.log_error(error_code, message)


def log_info(message: str):
    logger = get_logger()
    logger.log_info(message)


def log_warning(message: str):
    logger = get_logger()
    logger.log_warning(message)