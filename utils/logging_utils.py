from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional


def setup_logger(name: str = "misinfo", log_file: Optional[Path] = None, level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)
    if not logger.handlers:
        fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
        sh = logging.StreamHandler()
        sh.setFormatter(fmt)
        logger.addHandler(sh)
        if log_file is not None:
            fh = logging.FileHandler(str(log_file))
            fh.setFormatter(fmt)
            logger.addHandler(fh)
    return logger
