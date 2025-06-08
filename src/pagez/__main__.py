"""
智能判断代码页模块
用于解压时自动选择合适的代码页
"""
import os
import re
import sys
import subprocess
import tempfile
import shutil
from typing import Optional, List, Dict, Union
from pathlib import Path

from loguru import logger
from datetime import datetime

def setup_logger(app_name="app", project_root=None, console_output=True):
    """配置 Loguru 日志系统
    
    Args:
        app_name: 应用名称，用于日志目录
        project_root: 项目根目录，默认为当前文件所在目录
        console_output: 是否输出到控制台，默认为True
        
    Returns:
        tuple: (logger, config_info)
            - logger: 配置好的 logger 实例
            - config_info: 包含日志配置信息的字典
    """
    # 获取项目根目录
    if project_root is None:
        project_root = Path(__file__).parent.resolve()
    
    # 清除默认处理器
    logger.remove()
    
    # 有条件地添加控制台处理器（简洁版格式）
    if console_output:
        logger.add(
            sys.stdout,
            level="INFO",
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <blue>{elapsed}</blue> | <level>{level.icon} {level: <8}</level> | <cyan>{name}:{function}:{line}</cyan> - <level>{message}</level>"
        )
    
    # 使用 datetime 构建日志路径
    current_time = datetime.now()
    date_str = current_time.strftime("%Y-%m-%d")
    hour_str = current_time.strftime("%H")
    minute_str = current_time.strftime("%M%S")
    
    # 构建日志目录和文件路径
    log_dir = os.path.join(project_root, "logs", app_name, date_str, hour_str)
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"{minute_str}.log")
    
    # 添加文件处理器
    logger.add(
        log_file,
        level="DEBUG",
        rotation="10 MB",
        retention="30 days",
        compression="zip",
        encoding="utf-8",
        format="{time:YYYY-MM-DD HH:mm:ss} | {elapsed} | {level.icon} {level: <8} | {name}:{function}:{line} - {message}",
    )
    
    # 创建配置信息字典
    config_info = {
        'log_file': log_file,
    }
    
    logger.info(f"日志系统已初始化，应用名称: {app_name}")
    return logger, config_info

logger, config_info = setup_logger(app_name="pagez", console_output=True)


try:
    import charset_normalizer
    CHARSET_NORMALIZER_AVAILABLE = True
except ImportError:
    logger.warning("charset_normalizer库未安装，将使用备用方法进行字符集检测")
    CHARSET_NORMALIZER_AVAILABLE = False

try:
    import langdetect
    LANGDETECT_AVAILABLE = True
except ImportError:
    logger.warning("langdetect库未安装，将使用备用方法进行语言检测")
    LANGDETECT_AVAILABLE = False


class CodePageInfo:
    """代码页信息类"""
    
    def __init__(self, name: str, id: int, description: str = ""):
        """初始化代码页信息
        
        Args:
            name: 代码页名称
            id: 代码页ID
            description: 代码页描述
        """
        self.name = name
        self.id = id
        self.description = description
    
    def __str__(self) -> str:
        return f"{self.name} (ID: {self.id})"
    
    def __repr__(self) -> str:
        return f"CodePageInfo(name='{self.name}', id={self.id})"
    
    @property
    def param(self) -> str:
        """返回7z格式的代码页参数"""
        return f"-mcp={self.id}"


class SmartCodePage:
    """智能代码页选择器"""
    
    # 常用代码页信息
    CP_GBK = CodePageInfo("简体中文（GBK）", 936, "中文Windows系统默认编码")
    CP_BIG5 = CodePageInfo("繁体中文（大五码）", 950, "台湾/香港Windows系统默认编码")
    CP_SHIFT_JIS = CodePageInfo("日文（Shift_JIS）", 932, "日文Windows系统默认编码")
    CP_EUC_KR = CodePageInfo("韩文（EUC-KR）", 949, "韩文Windows系统默认编码")
    CP_UTF8 = CodePageInfo("UTF-8 Unicode", 65001, "Unicode通用编码")
    
    # 常用代码页列表
    COMMON_CODEPAGES = [CP_GBK, CP_BIG5, CP_SHIFT_JIS, CP_EUC_KR, CP_UTF8]
    
    # 语言到代码页的映射
    LANG_TO_CODEPAGE = {
        "zh-cn": CP_GBK,
        "zh-tw": CP_BIG5,
        "ja": CP_SHIFT_JIS,
        "ko": CP_EUC_KR,
        "en": CP_UTF8,
        "other": CP_UTF8
    }
    
    # 备用的字符集范围（当专门库不可用时使用）
    CHARSET_RANGES = {
        "japanese": r'[\u3040-\u30ff]',  # 日文平假名和片假名
        "korean": r'[\uac00-\ud7a3\u1100-\u11ff]',  # 韩文字符
        "chinese": r'[\u4e00-\u9fff]',  # 中文字符
    }
    
    def __init__(self):
        """初始化代码页选择器
        
        Args:
            seven_z_path: 7z可执行文件的路径
            debug: 是否启用调试模式
        """


    def detect_language_from_text(self, text: str) -> str:
        """从文本检测语言
        
        Args:
            text: 要检测的文本
            
        Returns:
            语言代码 (zh-cn, zh-tw, ja, ko, en, other)
        """
        if not text:
            return "other"
        
        # 使用langdetect库检测语言
        if LANGDETECT_AVAILABLE:
            try:
                # 设置种子以确保结果一致性
                langdetect.DetectorFactory.seed = 0
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
        
        # 备用方法：使用正则表达式检测特定字符集
        # 检查日文特有字符（平假名和片假名）
        if re.search(self.CHARSET_RANGES["japanese"], text):
            return "ja"
        
        # 检查韩文字符
        if re.search(self.CHARSET_RANGES["korean"], text):
            return "ko"
        
        # 检查中文字符
        if re.search(self.CHARSET_RANGES["chinese"], text):
            # 简单区分简体和繁体（不够准确，但作为备用方法）
            # 这里可以添加一些繁体中文特有字符的检测
            # 但由于没有专门库，这种方法不够准确
            return "zh-cn"
        
        return "other"
    
    def detect_encoding_from_bytes(self, data: bytes) -> str:
        """从字节数据检测编码
        
        Args:
            data: 字节数据
            
        Returns:
            编码名称
        """
        if CHARSET_NORMALIZER_AVAILABLE:
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
    
    def get_codepage_from_language(self, lang: str) -> CodePageInfo:
        """根据语言代码获取代码页信息
        
        Args:
            lang: 语言代码
            
        Returns:
            代码页信息对象
        """
        return self.LANG_TO_CODEPAGE.get(lang, self.CP_UTF8)
    
    def detect_codepage_from_filename(self, filename: str) -> CodePageInfo:
        """从文件名检测代码页
        
        Args:
            filename: 文件名
            
        Returns:
            代码页信息对象
        """
        # 检测文件名中的语言
        lang = self.detect_language_from_text(filename)
        logger.debug(f"从文件名 '{filename}' 检测到语言: {lang}")
        
        # 根据语言获取代码页
        codepage = self.get_codepage_from_language(lang)
        logger.debug(f"为文件名 '{filename}' 选择代码页: {codepage}")
        
        return codepage
    
    def extract_archive_info(self, archive_path: str) -> Optional[Dict]:
        """提取压缩包信息
        
        Args:
            archive_path: 压缩包路径
            
        Returns:
            压缩包信息字典或None
        """
        try:
            cmd = ["7z", 'l', '-slt', archive_path]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
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
            
            return info
            
        except Exception as e:
            logger.error(f"提取压缩包信息出错: {e}")
            return None
    
    def detect_codepage_from_archive_content(self, archive_path: str) -> CodePageInfo:
        """从压缩包内容检测代码页
        
        Args:
            archive_path: 压缩包路径
            
        Returns:
            代码页信息对象
        """
        # 首先获取压缩包信息
        info = self.extract_archive_info(archive_path)
        if not info:
            # 如果无法获取压缩包信息，则根据文件名判断
            return self.detect_codepage_from_filename(os.path.basename(archive_path))
        
        # 收集所有文件名
        filenames = [file_item.get('Path', '') for file_item in info['files']]
        
        # 统计各语言的文件数量
        lang_counts = {"zh-cn": 0, "zh-tw": 0, "ja": 0, "ko": 0, "other": 0}
        
        for filename in filenames:
            lang = self.detect_language_from_text(filename)
            lang_counts[lang] += 1
        
        logger.debug(f"压缩包内容语言统计: {lang_counts}")
        
        # 选择出现次数最多的语言
        if sum(lang_counts.values()) > 0:
            dominant_lang = max(lang_counts, key=lang_counts.get)
            logger.debug(f"压缩包 '{os.path.basename(archive_path)}' 的主要语言: {dominant_lang}")
            return self.get_codepage_from_language(dominant_lang)
        
        # 如果无法确定，返回默认代码页
        return self.CP_UTF8
    
    def test_extract_with_codepage(self, archive_path: str, codepage: CodePageInfo) -> bool:
        """测试使用指定代码页解压文件是否成功
        
        Args:
            archive_path: 压缩包路径
            codepage: 代码页信息对象
            
        Returns:
            解压是否成功
        """
        # 创建临时目录
        temp_dir = tempfile.mkdtemp(prefix="codepage_test_")
        try:
            # 尝试解压几个文件来测试代码页
            cmd = [
                "7z", 
                "e", 
                archive_path, 
                f"-o{temp_dir}", 
                "-aou",  # 自动重命名
                codepage.param,
                "-y"  # 自动回答是
            ]
            
            # 添加限制提取的文件数量
            cmd.append("-i!*")  # 最多提取10个文件
            
            logger.debug(f"测试代码页 {codepage.name} 的命令: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            # 检查是否成功解压
            success = result.returncode == 0 and os.listdir(temp_dir)
            logger.debug(f"测试代码页 {codepage.name} 结果: {'成功' if success else '失败'}")
            
            return success
        except Exception as e:
            logger.error(f"测试代码页时出错: {e}")
            return False
        finally:
            # 清理临时目录
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def detect_codepage(self, archive_path: str) -> CodePageInfo:
        """智能检测压缩包的代码页
        
        结合文件名和内容分析，并尝试测试解压来确定最佳代码页
        
        Args:
            archive_path: 压缩包路径
            
        Returns:
            代码页信息对象
        """
        if not os.path.exists(archive_path):
            logger.warning(f"文件不存在: {archive_path}")
            return self.CP_UTF8
        
        # 1. 首先根据文件名检测
        filename_cp = self.detect_codepage_from_filename(os.path.basename(archive_path))
        
        # 2. 再根据压缩包内容检测
        content_cp = self.detect_codepage_from_archive_content(archive_path)
        
        logger.debug(f"文件名检测的代码页: {filename_cp}")
        logger.debug(f"内容检测的代码页: {content_cp}")
        
        # 3. 如果两者结果不同，尝试测试解压来验证
        if filename_cp.id != content_cp.id:
            # 优先测试文件名检测的代码页（通常更准确）
            if self.test_extract_with_codepage(archive_path, filename_cp):
                return filename_cp
            
            # 测试内容检测的代码页
            if self.test_extract_with_codepage(archive_path, content_cp):
                return content_cp
            
            # 如果都不行，尝试其他常用代码页
            for cp in self.COMMON_CODEPAGES:
                if cp.id not in (filename_cp.id, content_cp.id):
                    if self.test_extract_with_codepage(archive_path, cp):
                        return cp
        
        # 优先使用文件名检测的结果，因为通常更准确
        return filename_cp
    
    def get_codepage_for_files(self, file_paths: List[str]) -> CodePageInfo:
        """为多个文件智能选择代码页
        
        Args:
            file_paths: 文件路径列表
            
        Returns:
            代码页信息对象
        """
        # 统计各代码页的权重
        codepage_weights = {cp.id: 0 for cp in self.COMMON_CODEPAGES}
        
        for file_path in file_paths:
            if not os.path.exists(file_path):
                logger.warning(f"文件不存在: {file_path}")
                continue
                
            cp = self.detect_codepage(file_path)
            codepage_weights[cp.id] += 1
        
        # 选择权重最高的代码页
        if sum(codepage_weights.values()) > 0:
            selected_cp_id = max(codepage_weights, key=codepage_weights.get)
            for cp in self.COMMON_CODEPAGES:
                if cp.id == selected_cp_id:
                    return cp
        
        # 如果没有有效的文件，返回系统默认代码页
        return self.get_system_default_codepage()
    
    def get_system_default_codepage(self) -> CodePageInfo:
        """获取系统默认代码页
        
        Returns:
            代码页信息对象
        """
        # Windows系统
        if sys.platform == "win32":
            # 获取系统ANSI代码页
            try:
                # 使用PowerShell获取系统ANSI代码页
                cmd = ["powershell", "-Command", "[System.Text.Encoding]::Default.CodePage"]
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0 and result.stdout.strip().isdigit():
                    cp_id = int(result.stdout.strip())
                    # 检查是否是我们支持的代码页
                    for cp in self.COMMON_CODEPAGES:
                        if cp.id == cp_id:
                            return cp
            except Exception as e:
                logger.error(f"获取系统代码页出错: {e}")
            
            # 如果无法获取或不支持，根据环境变量判断
            if os.environ.get('LANG', '').startswith('zh_CN') or \
               os.environ.get('LANGUAGE', '').startswith('zh_CN'):
                return self.CP_GBK
            # 繁体中文Windows
            elif os.environ.get('LANG', '').startswith('zh_TW') or \
                 os.environ.get('LANGUAGE', '').startswith('zh_TW'):
                return self.CP_BIG5
            # 日文Windows
            elif os.environ.get('LANG', '').startswith('ja') or \
                 os.environ.get('LANGUAGE', '').startswith('ja'):
                return self.CP_SHIFT_JIS
            # 韩文Windows
            elif os.environ.get('LANG', '').startswith('ko') or \
                 os.environ.get('LANGUAGE', '').startswith('ko'):
                return self.CP_EUC_KR
        
        # 默认使用UTF-8
        return self.CP_UTF8


# API函数

def get_codepage_param(file_paths: Union[str, List[str]], seven_z_path: str = "7z") -> str:
    """便捷函数：获取适合给定文件的代码页参数
    
    Args:
        file_paths: 文件路径或文件路径列表
        seven_z_path: 7z可执行文件的路径
        
    Returns:
        7-zip格式的代码页参数
    """
    selector = SmartCodePage(seven_z_path)
    
    if isinstance(file_paths, str):
        file_paths = [file_paths]
        
    codepage = selector.get_codepage_for_files(file_paths)
    return codepage.param


def smart_extract(archive_path: str, target_dir: Optional[str] = None, 
                 seven_z_path: str = "7z", password: Optional[str] = None,
                 codepage: Optional[Union[int, str, CodePageInfo]] = None) -> bool:
    """智能解压函数
    
    使用智能代码页检测来解压文件
    
    Args:
        archive_path: 压缩包路径
        target_dir: 目标目录，如果为None则解压到当前目录下的同名文件夹
        seven_z_path: 7z可执行文件的路径
        password: 解压密码，如果为None则尝试无密码解压
        codepage: 指定代码页，可以是代码页ID、代码页参数字符串或CodePageInfo对象，
                 如果为None则自动检测
        
    Returns:
        解压是否成功
    """
    # 检查文件是否存在
    if not os.path.exists(archive_path):
        logger.error(f"文件不存在: {archive_path}")
        return False
    
    # 如果未指定目标目录，创建同名目录
    if target_dir is None:
        target_dir = os.path.splitext(os.path.basename(archive_path))[0]
    
    # 确保目标目录存在
    os.makedirs(target_dir, exist_ok=True)
    
    # 处理代码页参数
    selector = SmartCodePage(seven_z_path)
    cp_param = ""
    
    if codepage is None:
        # 智能检测代码页
        cp_info = selector.detect_codepage(archive_path)
        cp_param = cp_info.param
        logger.info(f"为 {os.path.basename(archive_path)} 自动选择的代码页: {cp_info}")
    else:
        # 使用指定的代码页
        if isinstance(codepage, CodePageInfo):
            cp_param = codepage.param
            logger.info(f"使用指定的代码页: {codepage}")
        elif isinstance(codepage, int):
            cp_param = f"-mcp={codepage}"
            logger.info(f"使用指定的代码页ID: {codepage}")
        elif isinstance(codepage, str):
            if codepage.startswith("-mcp="):
                cp_param = codepage
            else:
                cp_param = f"-mcp={codepage}"
            logger.info(f"使用指定的代码页参数: {cp_param}")
    
    # 构建解压命令
    cmd = [seven_z_path, "x", archive_path, f"-o{target_dir}", "-aou"]
    
    # 添加代码页参数
    if cp_param:
        cmd.append(cp_param)
    
    # 添加密码参数
    if password:
        cmd.append(f"-p{password}")
    else:
        cmd.append("-p")  # 空密码
    
    # 自动回答是
    cmd.append("-y")
    
    try:
        # 执行解压命令
        logger.info(f"执行命令: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # 检查是否成功
        if result.returncode == 0:
            logger.info(f"成功解压 {os.path.basename(archive_path)} 到 {target_dir}")
            return True
        else:
            logger.error(f"解压失败，错误码: {result.returncode}")
            logger.error(f"错误信息: {result.stderr}")
            return False
    except Exception as e:
        logger.error(f"解压过程中发生错误: {e}")
        return False


def test_extract_folder(test_folder: str = r"E:\2EHV\test", 
                       output_folder: Optional[str] = None,
                       seven_z_path: str = "7z"):
    """测试解压指定文件夹中的所有压缩包
    
    Args:
        test_folder: 测试文件夹路径
        output_folder: 输出文件夹路径，如果为None则在测试文件夹中创建output子文件夹
        seven_z_path: 7z可执行文件的路径
    """
    # 检查测试文件夹是否存在
    if not os.path.exists(test_folder):
        logger.error(f"测试文件夹不存在: {test_folder}")
        return
    
    # 设置输出文件夹
    if output_folder is None:
        output_folder = os.path.join(test_folder, "output")
    
    # 确保输出文件夹存在
    os.makedirs(output_folder, exist_ok=True)
    
    # 获取所有压缩包文件
    archive_extensions = ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.cbz', '.cbr']
    archive_files = []
    
    for root, _, files in os.walk(test_folder):
        for file in files:
            if any(file.lower().endswith(ext) for ext in archive_extensions):
                archive_files.append(os.path.join(root, file))
    
    if not archive_files:
        logger.warning(f"在 {test_folder} 中未找到压缩包文件")
        return
    
    logger.info(f"找到 {len(archive_files)} 个压缩包文件")
    
    # 创建智能代码页选择器
    selector = SmartCodePage(seven_z_path)
    
    # 测试每个压缩包
    results = []
    for archive_path in archive_files:
        archive_name = os.path.basename(archive_path)
        logger.info(f"\n正在处理: {archive_name}")
        
        # 智能检测代码页
        cp_info = selector.detect_codepage(archive_path)
        logger.info(f"检测到的代码页: {cp_info}")
        
        # 创建解压目标文件夹
        target_dir = os.path.join(output_folder, os.path.splitext(archive_name)[0])
        
        # 执行解压
        success = smart_extract(archive_path, target_dir, seven_z_path, codepage=cp_info)
        
        # 记录结果
        results.append({
            "file": archive_name,
            "codepage": cp_info,
            "success": success
        })
    
    # 打印汇总结果
    logger.info("\n解压测试结果汇总:")
    logger.info("=" * 70)
    success_count = sum(1 for r in results if r["success"])
    logger.info(f"总共测试: {len(results)} 个文件")
    logger.info(f"成功解压: {success_count} 个文件")
    logger.info(f"失败: {len(results) - success_count} 个文件")
    logger.info("=" * 70)
    
    # 打印每个文件的结果
    for result in results:
        status = "成功" if result["success"] else "失败"
        logger.info(f"{result['file']} - 代码页: {result['codepage']} - {status}")


# 如果直接运行此模块，执行测试
if __name__ == "__main__":
    # 检查命令行参数
    if len(sys.argv) > 1:
        # 如果提供了文件夹路径，测试该文件夹
        test_folder = sys.argv[1]
    else:
        # 默认测试E:\2EHV\test
        test_folder = r"E:\2EHV\test"
    
    # 检查7z路径
    seven_z_path = "7z"  # 默认假设7z在PATH中
    
    # 执行测试
    logger.info(f"开始测试解压 {test_folder} 中的压缩包...")
    test_extract_folder(test_folder, seven_z_path=seven_z_path)