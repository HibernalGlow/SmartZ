"""
工具函数模块
提供常用的辅助功能
"""
import os
import sys
import re
import subprocess
import threading
from typing import Optional, Dict, Any
from functools import lru_cache, wraps
from concurrent.futures import ThreadPoolExecutor, as_completed

from .logger_config import get_logger
from .codepage_info import CodePageInfo, COMMON_CODEPAGES, CHARSET_RANGES

logger = get_logger()

# 全局线程锁
_subprocess_lock = threading.Lock()
_charset_normalizer_lock = threading.Lock()
_langdetect_lock = threading.Lock()

# 线程本地存储
_thread_local = threading.local()

# 延迟导入的模块
_charset_normalizer = None
_langdetect = None


def _get_thread_executor():
    """获取线程本地的执行器"""
    if not hasattr(_thread_local, 'executor'):
        _thread_local.executor = ThreadPoolExecutor(max_workers=4)
    return _thread_local.executor


def lazy_import_charset_normalizer():
    """延迟导入charset_normalizer库"""
    global _charset_normalizer
    if _charset_normalizer is None:
        with _charset_normalizer_lock:
            if _charset_normalizer is None:
                try:
                    import charset_normalizer
                    _charset_normalizer = charset_normalizer
                    logger.debug("charset_normalizer库加载成功")
                except ImportError:
                    logger.warning("charset_normalizer库未安装，将使用备用方法进行字符集检测")
                    _charset_normalizer = False
    return _charset_normalizer


def lazy_import_langdetect():
    """延迟导入langdetect库"""
    global _langdetect
    if _langdetect is None:
        with _langdetect_lock:
            if _langdetect is None:
                try:
                    import langdetect
                    _langdetect = langdetect
                    # 设置种子以确保结果一致性
                    langdetect.DetectorFactory.seed = 0
                    logger.debug("langdetect库加载成功")
                except ImportError:
                    logger.warning("langdetect库未安装，将使用备用方法进行语言检测")
                    _langdetect = False
    return _langdetect


def thread_safe_cache(maxsize=128):
    """线程安全的缓存装饰器"""
    def decorator(func):
        cached_func = lru_cache(maxsize=maxsize)(func)
        lock = threading.Lock()
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            with lock:
                return cached_func(*args, **kwargs)
        
        wrapper.cache_info = cached_func.cache_info
        wrapper.cache_clear = cached_func.cache_clear
        return wrapper
    return decorator


@thread_safe_cache(maxsize=256)
def detect_language_from_text(text: str) -> str:
    """从文本检测语言（带缓存）
    
    Args:
        text: 要检测的文本
        
    Returns:
        语言代码 (zh-cn, zh-tw, ja, ko, en, other)
    """
    if not text:
        return "other"
    
    # 首先检查文件名中是否包含日文的平假名和片假名
    if re.search(CHARSET_RANGES["japanese"], text):
        return "ja"
    
    # 检查韩文字符
    if re.search(CHARSET_RANGES["korean"], text):
        return "ko"
    
    # 检查是否包含可能是日文编码错误导致的特殊字符
    from .codepage_info import POSSIBLE_JAPANESE_GARBLED
    
    # 计算文本中可能是日文乱码的字符比例
    garbled_chars_count = sum(1 for char in text if char in POSSIBLE_JAPANESE_GARBLED)
    if garbled_chars_count > 0:
        # 如果乱码字符占比超过20%，很可能是日文文件
        if garbled_chars_count / len(text) > 0.2:
            # logger.debug(f"检测到可能的日文乱码字符: {garbled_chars_count}/{len(text)}")
            return "ja"
    
    # 检查中文字符
    if re.search(CHARSET_RANGES["chinese"], text):
        # 检查是否含有乱码特征字符范围
        if re.search(CHARSET_RANGES["garbled_chars"], text):
            # 如果同时包含中文和乱码特征，进行进一步分析
            chinese_count = len(re.findall(CHARSET_RANGES["chinese"], text))
            garbled_count = len(re.findall(CHARSET_RANGES["garbled_chars"], text))
            
            # 如果乱码字符比例较高，可能是日文被错误解码
            if garbled_count > chinese_count * 0.5:
                # logger.debug(f"检测到可能的日文乱码: 中文字符={chinese_count}, 乱码字符={garbled_count}")
                return "ja"
        
        # 简单区分简体和繁体（不够准确，但作为备用方法）
        return "zh-cn"
    
    # 如果正则表达式没有匹配，再使用langdetect库检测
    langdetect = lazy_import_langdetect()
    if langdetect:
        try:
            lang = langdetect.detect(text)
            
            # 映射langdetect的结果到我们的语言代码
            if lang == "zh-cn" or lang == "zh":
                return "zh-cn"
            elif lang == "zh-tw":
                return "zh-tw"
            elif lang == "ja":
                return "ja"
            elif lang == "ko":
                return "ko"
            else:
                return "other"
        except Exception as e:
            logger.debug(f"langdetect检测失败: {e}")
    
    return "other"


@thread_safe_cache(maxsize=128)
def detect_encoding_from_bytes(data: bytes) -> str:
    """从字节数据检测编码（带缓存）
    
    Args:
        data: 字节数据
        
    Returns:
        编码名称
    """
    charset_normalizer = lazy_import_charset_normalizer()
    if charset_normalizer:
        try:
            # charset_normalizer.detect() 返回的是一个可迭代对象
            results = list(charset_normalizer.detect(data))
            if results and len(results) > 0:
                best_match = results[0]
                if best_match.encoding and best_match.confidence > 0.7:
                    return best_match.encoding
        except Exception as e:
            logger.debug(f"charset_normalizer检测失败: {e}")
    
    # 如果charset_normalizer不可用或检测失败，返回默认编码
    return "utf-8"


def safe_subprocess_run(cmd: list, timeout: int = 30, **kwargs) -> subprocess.CompletedProcess:
    """线程安全的subprocess执行
    
    Args:
        cmd: 命令列表
        timeout: 超时时间（秒）
        **kwargs: 传递给subprocess.run的其他参数
        
    Returns:
        subprocess.CompletedProcess对象
    """
    with _subprocess_lock:
        try:
            return subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=timeout,
                **kwargs
            )
        except subprocess.TimeoutExpired:
            logger.warning(f"命令执行超时: {' '.join(cmd)}")
            # 返回一个模拟的失败结果
            return subprocess.CompletedProcess(
                cmd, 
                returncode=1, 
                stdout="", 
                stderr="Command timeout"
            )
        except Exception as e:
            logger.error(f"命令执行出错: {e}")
            return subprocess.CompletedProcess(
                cmd, 
                returncode=1, 
                stdout="", 
                stderr=str(e)
            )


def get_system_default_codepage() -> CodePageInfo:
    """获取系统默认代码页
    
    Returns:
        代码页信息对象
    """
    from .codepage_info import CP_GBK, CP_BIG5, CP_SHIFT_JIS, CP_EUC_KR, CP_UTF8
    
    # Windows系统
    if sys.platform == "win32":
        # 获取系统ANSI代码页
        try:
            # 使用PowerShell获取系统ANSI代码页
            cmd = ["powershell", "-Command", "[System.Text.Encoding]::Default.CodePage"]
            result = safe_subprocess_run(cmd)
            if result.returncode == 0 and result.stdout.strip().isdigit():
                cp_id = int(result.stdout.strip())
                # 检查是否是我们支持的代码页
                for cp in COMMON_CODEPAGES:
                    if cp.id == cp_id:
                        return cp
        except Exception as e:
            logger.error(f"获取系统代码页出错: {e}")
        
        # 如果无法获取或不支持，根据环境变量判断
        lang_env = os.environ.get('LANG', '') or os.environ.get('LANGUAGE', '')
        
        if lang_env.startswith('zh_CN'):
            return CP_GBK
        elif lang_env.startswith('zh_TW'):
            return CP_BIG5
        elif lang_env.startswith('ja'):
            return CP_SHIFT_JIS
        elif lang_env.startswith('ko'):
            return CP_EUC_KR
    
    # 默认使用UTF-8
    return CP_UTF8


def parallel_process_files(files: list, process_func, max_workers: int = None) -> dict:
    """并行处理文件列表
    
    Args:
        files: 文件列表
        process_func: 处理函数，接受文件路径参数
        max_workers: 最大工作线程数
        
    Returns:
        文件路径到处理结果的映射字典
    """
    if max_workers is None:
        max_workers = min(len(files), os.cpu_count() or 4)
    
    results = {}
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任务
        future_to_file = {executor.submit(process_func, file): file for file in files}
        
        # 收集结果
        for future in as_completed(future_to_file):
            file = future_to_file[future]
            try:
                result = future.result()
                results[file] = result
            except Exception as e:
                logger.error(f"处理文件 {file} 时出错: {e}")
                results[file] = None
    
    return results


def cleanup_thread_resources():
    """清理线程本地资源"""
    if hasattr(_thread_local, 'executor'):
        _thread_local.executor.shutdown(wait=True)
        delattr(_thread_local, 'executor')
