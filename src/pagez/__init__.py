"""
Smart Archive Extractor Package
智能压缩包解压工具包

提供以下功能：
1. 智能代码页检测
2. 多线程/多进程安全的解压操作
3. 批量处理压缩包
4. 高性能缓存机制
5. 延迟加载优化

主要API:
- smart_extract: 智能解压单个文件
- batch_extract: 批量解压文件
- detect_archive_codepage: 检测压缩包代码页
- get_codepage_param: 获取代码页参数
"""

from pagez.core.api import (
    smart_extract,
    get_codepage_param,
    batch_extract,
    detect_archive_codepage,
    get_archive_info,
    test_extract_folder,
    clear_all_caches
)

from pagez.core.codepage_info import (
    CodePageInfo,
    CP_GBK,
    CP_BIG5,
    CP_SHIFT_JIS,
    CP_EUC_KR,
    CP_UTF8,
    COMMON_CODEPAGES,
    LANG_TO_CODEPAGE
)

from pagez.core.smart_detector import SmartCodePage
from pagez.core.logger_config import setup_logger, get_logger

# 版本信息
__version__ = "2.0.0"
__author__ = "Smart Archive Extractor Team"
__description__ = "智能代码页检测和压缩包解压工具"

# 主要导出的API
__all__ = [
    # API functions
    'smart_extract',
    'get_codepage_param',
    'batch_extract',
    'detect_archive_codepage',
    'get_archive_info',
    'test_extract_folder',
    'clear_all_caches',
    
    # Classes
    'CodePageInfo',
    'SmartCodePage',
    
    # Constants
    'CP_GBK',
    'CP_BIG5',
    'CP_SHIFT_JIS',
    'CP_EUC_KR',
    'CP_UTF8',
    'COMMON_CODEPAGES',
    'LANG_TO_CODEPAGE',
    
    # Utilities
    'setup_logger',
    'get_logger',
    
    # Version
    '__version__'
]
__author__ = "SmartZip Python Edition"
