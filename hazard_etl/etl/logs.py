import sys
import logging


def init_logger() -> None:
    """Initializes the logger"""
    log_level = logging.INFO
    logging.basicConfig(level=log_level, format='%(message)s')
    logger = logging.getLogger("gps-logger")
    logger.handlers.clear()
    c_handler = logging.StreamHandler()
    c_handler.setLevel(log_level)
    c_format = logging.Formatter("%(message)s")
    c_handler.setFormatter(c_format)
    logger.addHandler(c_handler)
    logger.propagate = False


def _get_logger():
    return logging.getLogger("gps-logger")


def section(title: str) -> None:
    """Prints a section header
    
    Args:
        title (str): section title
    """
    logger = _get_logger()
    logger.info("\n" + "=" * 60)
    logger.info(title.upper())
    logger.info("=" * 60 + "\n")


def die(msg: str) -> None:
    """Prints error message and stops the process
    
    Args:
        msg (str): the error message
    """
    logger = _get_logger()
    logger.error(f"[!!] ERROR: {msg}")
    sys.exit(1)


def info(msg: str) -> None:
    """Prints info message
    
    Args:
        msg (str): the message to print
    """
    logger = _get_logger()
    logger.info(f"[>>] {msg}")


def progress_bar(current: int, total: int, prefix: str = '', width: int = 40) -> None:
    """Displays a progress bar
    
    Args:
        current (int): current progress
        total (int): total items
        prefix (str): text before the bar
        width (int): width of the bar in characters
    """
    if total == 0:
        return
    
    percent = current / total
    filled = int(width * percent)
    bar = '#' * filled + '-' * (width - filled)
    
    # Build message with padding to clear previous line
    msg = f"[>>] {prefix} [{bar}] {current}/{total} ({percent*100:.0f}%)"
    # Add spaces to clear any leftover characters from previous line
    msg = msg.ljust(100)
    
    if current == total:
        # Final line - print with newline and clear
        print(f"\r{msg}")
    else:
        # In progress - overwrite same line
        print(f"\r{msg}", end='', flush=True)
