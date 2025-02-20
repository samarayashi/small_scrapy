import logging
import sys
import traceback
from pathlib import Path
from datetime import datetime
from rich.logging import RichHandler
from rich.console import Console
from rich.traceback import install
from typing import Optional

# 安裝 rich 的異常追蹤
install(show_locals=True)

class CustomFormatter(logging.Formatter):
    """自定義日誌格式"""
    
    def __init__(self):
        super().__init__(
            fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s\n%(exc_info)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    
    def format(self, record):
        """重寫format方法以自定義異常輸出格式"""
        if record.exc_info:
            # 如果有異常信息，格式化它
            record.exc_text = ''.join(traceback.format_exception(*record.exc_info))
        return super().format(record)

def setup_logger(
    name: str,
    console_level: int = logging.INFO,
    file_level: int = logging.DEBUG,
    log_dir: Optional[Path] = None
) -> logging.Logger:
    """
    設置logger
    
    Args:
        name: logger名稱
        console_level: 控制台日誌級別
        file_level: 文件日誌級別
        log_dir: 日誌目錄路徑
        
    Returns:
        logging.Logger: 配置好的logger實例
    """
    # 創建logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)  # 設置最低級別為DEBUG
    
    # 如果logger已經有處理器，先清除
    if logger.handlers:
        logger.handlers.clear()
        
    # 創建日誌目錄
    log_dir = Path(log_dir) if log_dir else Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # 檔案處理器 - 詳細日誌
    detailed_log = log_dir / f"{name}_{datetime.now():%Y%m%d}.log"
    file_handler = logging.FileHandler(detailed_log, encoding='utf-8')
    file_handler.setLevel(file_level)
    file_handler.setFormatter(CustomFormatter())
    
    # 控制台處理器
    console = Console(force_terminal=True)
    console_handler = RichHandler(
        console=console,
        show_time=False,
        show_path=True,
        rich_tracebacks=True,
        tracebacks_show_locals=True,
        tracebacks_width=None,
        markup=True,
        enable_link_path=True  # 啟用文件路徑連結
    )
    console_handler.setLevel(console_level)
    
    # 為控制台處理器設置特殊的格式
    console_formatter = logging.Formatter(
        fmt="%(message)s\n%(exc_info)s",  # 添加異常信息
        datefmt="[%X]"
    )
    console_handler.setFormatter(console_formatter)
    
    # 添加處理器
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger 