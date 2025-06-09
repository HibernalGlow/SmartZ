"""
智能代码页检测器核心模块
实现主要的代码页检测逻辑
"""
import os
import tempfile
import shutil
import threading
from typing import Optional, List, Dict
from functools import lru_cache

from .logger_config import get_logger
from .codepage_info import CodePageInfo, COMMON_CODEPAGES, LANG_TO_CODEPAGE
from .utils import (
    detect_language_from_text, 
    safe_subprocess_run, 
    get_system_default_codepage,
    thread_safe_cache,
    parallel_process_files
)

logger = get_logger()

# 线程锁
_temp_dir_lock = threading.Lock()


class SmartCodePage:
    """智能代码页选择器"""
    
    def __init__(self, seven_z_path: str = "7z"):
        """初始化代码页选择器
        
        Args:
            seven_z_path: 7z可执行文件的路径
        """
        self.seven_z_path = seven_z_path
        self._archive_info_cache = {}
        self._cache_lock = threading.Lock()
    
    def get_codepage_from_language(self, lang: str) -> CodePageInfo:
        """根据语言代码获取代码页信息
        
        Args:
            lang: 语言代码
            
        Returns:
            代码页信息对象
        """
        return LANG_TO_CODEPAGE.get(lang, LANG_TO_CODEPAGE["other"])
    
    @thread_safe_cache(maxsize=256)
    def detect_codepage_from_filename(self, filename: str) -> CodePageInfo:
        """从文件名检测代码页（带缓存）
        
        Args:
            filename: 文件名
            
        Returns:
            代码页信息对象
        """
        # 检测文件名中的语言
        lang = detect_language_from_text(filename)
        logger.debug(f"从文件名 '{filename}' 检测到语言: {lang}")
        
        # 根据语言获取代码页
        codepage = self.get_codepage_from_language(lang)
        logger.debug(f"为文件名 '{filename}' 选择代码页: {codepage}")
        
        return codepage
    
    def extract_archive_info(self, archive_path: str, use_cache: bool = True) -> Optional[Dict]:
        """提取压缩包信息（带缓存）
        
        Args:
            archive_path: 压缩包路径
            use_cache: 是否使用缓存
            
        Returns:
            压缩包信息字典或None
        """
        # 检查缓存
        if use_cache:
            with self._cache_lock:
                if archive_path in self._archive_info_cache:
                    return self._archive_info_cache[archive_path]
        
        try:
            cmd = [self.seven_z_path, 'l', '-slt', archive_path]
            result = safe_subprocess_run(cmd, timeout=30)
            
            if result.returncode != 0:
                logger.warning(f"无法读取压缩包信息: {archive_path}")
                return None
            
            # 解析输出
            info = {
                'files': [],
                'folders': [],
                'encrypted': False,
                'total_size': 0,
                'file_count': 0
            }
            
            lines = result.stdout.split('\n')
            current_item = {}
            
            for line in lines:
                line = line.strip()
                
                if line.startswith('Path = '):
                    if current_item:
                        if current_item.get('Attributes', '').startswith('D'):
                            info['folders'].append(current_item)
                        else:
                            info['files'].append(current_item)
                    current_item = {'Path': line[7:]}
                
                elif ' = ' in line and current_item:
                    key, value = line.split(' = ', 1)
                    current_item[key] = value
                    
                    if key == 'Size' and value.isdigit():
                        info['total_size'] += int(value)
                    elif key == 'Encrypted' and value == '+':
                        info['encrypted'] = True
            
            # 处理最后一个项目
            if current_item:
                if current_item.get('Attributes', '').startswith('D'):
                    info['folders'].append(current_item)
                else:
                    info['files'].append(current_item)
            
            info['file_count'] = len(info['files'])
            
            # 缓存结果
            if use_cache:
                with self._cache_lock:
                    self._archive_info_cache[archive_path] = info
            
            return info
            
        except Exception as e:
            logger.error(f"提取压缩包信息出错: {e}")
            return None
    
    @thread_safe_cache(maxsize=128)
    def detect_codepage_from_archive_content(self, archive_path: str) -> CodePageInfo:
        """从压缩包内容检测代码页（带缓存）
        
        Args:
            archive_path: 压缩包路径
            
        Returns:
            代码页信息对象
        """
        # 首先获取压缩包信息
        info = self.extract_archive_info(archive_path)
        if not info:
            # 如果无法获取压缩包信息，返回默认代码页
            logger.warning(f"无法获取压缩包信息: {archive_path}")
            return LANG_TO_CODEPAGE["other"]
        
        # 收集所有文件名
        filenames = [file_item.get('Path', '') for file_item in info['files']]
        
        # 首先检查压缩包名称中是否包含日文特征
        archive_basename = os.path.basename(archive_path)
        archive_lang = detect_language_from_text(archive_basename)
        
        # 如果压缩包名称是日文，增加日文的权重
        initial_weights = {"zh-cn": 0, "zh-tw": 0, "ja": 0, "ko": 0, "other": 0}
        if archive_lang == "ja":
            initial_weights["ja"] = max(1, len(filenames) // 10)  # 给予一定的初始权重
            logger.debug(f"压缩包名称 '{archive_basename}' 检测为日文，增加日文权重")
        
        # 统计各语言的文件数量
        lang_counts = initial_weights.copy()
        
        # 检查是否有明确的日文文件扩展名
        japanese_extensions = ['.jp', '.jpa', '.jpx', '.jpm', '.j2k']
        for filename in filenames:
            _, ext = os.path.splitext(filename.lower())
            if ext in japanese_extensions:
                lang_counts["ja"] += 1
                continue
                
            # 普通语言检测
            lang = detect_language_from_text(filename)
            lang_counts[lang] += 1
        
        logger.debug(f"压缩包内容语言统计: {lang_counts}")
        
        # 选择出现次数最多的语言
        if sum(lang_counts.values()) > 0:
            # 如果日文和其他语言的差距很小（小于10%），优先选择日文
            if "ja" in lang_counts and lang_counts["ja"] > 0:
                max_lang = max(lang_counts, key=lang_counts.get)
                if max_lang != "ja" and lang_counts["ja"] >= lang_counts[max_lang] * 0.9:
                    logger.debug(f"日文和{max_lang}的差距很小，优先选择日文")
                    dominant_lang = "ja"
                else:
                    dominant_lang = max_lang
            else:
                dominant_lang = max(lang_counts, key=lang_counts.get)
                
            logger.debug(f"压缩包 '{os.path.basename(archive_path)}' 的主要语言: {dominant_lang}")
            return self.get_codepage_from_language(dominant_lang)
        
        # 如果无法确定，返回默认代码页
        return LANG_TO_CODEPAGE["other"]
    
    def test_extract_with_codepage(self, archive_path: str, codepage: CodePageInfo) -> bool:
        """测试使用指定代码页解压文件是否成功
        
        Args:
            archive_path: 压缩包路径
            codepage: 代码页信息对象
            
        Returns:
            解压是否成功
        """
        # 创建临时目录（线程安全）
        with _temp_dir_lock:
            temp_dir = tempfile.mkdtemp(prefix="codepage_test_")
        
        try:
            # 尝试解压几个文件来测试代码页
            cmd = [
                self.seven_z_path, 
                "e", 
                archive_path, 
                f"-o{temp_dir}", 
                "-aou",  # 自动重命名
                codepage.param,
                "-y"  # 自动回答是
            ]
            
            # 添加限制提取的文件数量
            cmd.append("-i!*")  # 最多提取所有文件（测试时会很快失败）
            
            logger.debug(f"测试代码页 {codepage.name} 的命令: {' '.join(cmd)}")
            result = safe_subprocess_run(cmd, timeout=30)
            
            # 检查是否成功解压
            success = result.returncode == 0 and os.listdir(temp_dir)
            logger.debug(f"测试代码页 {codepage.name} 结果: {'成功' if success else '失败'}")
            
            return success
        except Exception as e:
            logger.error(f"测试代码页时出错: {e}")
            return False
        finally:
            # 清理临时目录
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception:
                pass  # 忽略清理错误
    
    def detect_codepage(self, archive_path: str) -> CodePageInfo:
        """智能检测压缩包的代码页
        
        专注于压缩包内容分析，不考虑文件名和编码冲突
        
        Args:
            archive_path: 压缩包路径
            
        Returns:
            代码页信息对象
        """
        if not os.path.exists(archive_path):
            logger.warning(f"文件不存在: {archive_path}")
            return LANG_TO_CODEPAGE["other"]
        
        # 直接使用压缩包内容检测
        content_cp = self.detect_codepage_from_archive_content(archive_path)
        logger.debug(f"内容检测的代码页: {content_cp}")
        
        # 不再进行编码冲突检测和测试解压
        return content_cp
    
    def get_codepage_for_files(self, file_paths: List[str], parallel: bool = True) -> CodePageInfo:
        """为多个文件智能选择代码页
        
        专注于压缩包内容分析，不考虑文件名和编码冲突
        
        Args:
            file_paths: 文件路径列表
            parallel: 是否使用并行处理
            
        Returns:
            代码页信息对象
        """
        # 过滤存在的文件
        valid_files = [fp for fp in file_paths if os.path.exists(fp)]
        
        if not valid_files:
            logger.warning("没有有效的文件")
            return get_system_default_codepage()
        
        # 统计各代码页的权重
        codepage_weights = {cp.id: 0 for cp in COMMON_CODEPAGES}
        
        if parallel and len(valid_files) > 1:
            # 并行处理
            results = parallel_process_files(valid_files, self.detect_codepage)
            for file_path, cp in results.items():
                if cp:
                    codepage_weights[cp.id] += 1
        else:
            # 串行处理
            for file_path in valid_files:
                cp = self.detect_codepage(file_path)
                codepage_weights[cp.id] += 1
        
        # 选择权重最高的代码页
        if sum(codepage_weights.values()) > 0:
            selected_cp_id = max(codepage_weights, key=codepage_weights.get)
            for cp in COMMON_CODEPAGES:
                if cp.id == selected_cp_id:
                    return cp
        
        # 如果没有有效的文件，返回系统默认代码页
        return get_system_default_codepage()
    
    def clear_cache(self):
        """清除缓存"""
        with self._cache_lock:
            self._archive_info_cache.clear()
        
        # 清除函数级缓存
        self.detect_codepage_from_filename.cache_clear()
        self.detect_codepage_from_archive_content.cache_clear()
        detect_language_from_text.cache_clear()
        
        logger.debug("缓存已清除")
