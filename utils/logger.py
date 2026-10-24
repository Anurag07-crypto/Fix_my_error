import logging
from pathlib import Path
from typing import Optional

def get_logger(name: str, level: Optional[int] = None) -> logging.Logger:
    logger = logging.getLogger(name)
    
    # it prevent duplicate handlers if called multiple times
    if logger.handlers:
        return logger
    logger.setLevel(level if level is not None else logging.DEBUG)
    
    #  ----- Console Handler -- INFO and above ---
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    
    # ----- File Handler -- DEBUG and above ----
    log_dir = Path(__file__).parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)
    file_handler = logging.FileHandler(log_dir / "app.log")
    file_handler.setLevel(logging.DEBUG)
    
    # ---- Format ---
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    logger.addHandler(console)
    logger.addHandler(file_handler)
    return logger

