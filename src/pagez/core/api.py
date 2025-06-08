"""
外部API模块
提供便捷的API函数供外部调用
"""
import os
from typing import Optional, List, Dict, Union

from .logger_config import get_logger
from .codepage_info import CodePageInfo
from .smart_detector import SmartCodePage
from .utils import safe_subprocess_run

logger = get_logger()


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


def smart_extract(archive_path: str, 
                 target_dir: Optional[str] = None, 
                 seven_z_path: str = "7z", 
                 password: Optional[str] = None,
                 codepage: Optional[Union[int, str, CodePageInfo]] = None,
                 overwrite: bool = True) -> bool:
    """智能解压函数
    
    使用智能代码页检测来解压文件
    
    Args:
        archive_path: 压缩包路径
        target_dir: 目标目录，如果为None则解压到当前目录下的同名文件夹
        seven_z_path: 7z可执行文件的路径
        password: 解压密码，如果为None则尝试无密码解压
        codepage: 指定代码页，可以是代码页ID、代码页参数字符串或CodePageInfo对象，
                 如果为None则自动检测
        overwrite: 是否覆盖已存在的文件
        
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
    cmd = [seven_z_path, "x", archive_path, f"-o{target_dir}"]
    
    # 添加覆盖选项
    if overwrite:
        cmd.append("-aoa")  # 覆盖所有文件
    else:
        cmd.append("-aos")  # 跳过已存在的文件
    
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
        result = safe_subprocess_run(cmd, timeout=300)  # 增加超时时间
        
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


def batch_extract(archive_paths: List[str], 
                 output_folder: str,
                 seven_z_path: str = "7z",
                 password: Optional[str] = None,
                 parallel: bool = True,
                 max_workers: Optional[int] = None) -> Dict[str, bool]:
    """批量解压压缩包
    
    Args:
        archive_paths: 压缩包路径列表
        output_folder: 输出文件夹
        seven_z_path: 7z可执行文件的路径
        password: 解压密码
        parallel: 是否并行处理
        max_workers: 最大工作线程数
        
    Returns:
        文件路径到解压结果的映射字典
    """
    from .utils import parallel_process_files
    
    # 确保输出文件夹存在
    os.makedirs(output_folder, exist_ok=True)
    
    def extract_single(archive_path: str) -> bool:
        """解压单个文件"""
        archive_name = os.path.basename(archive_path)
        target_dir = os.path.join(output_folder, os.path.splitext(archive_name)[0])
        return smart_extract(archive_path, target_dir, seven_z_path, password)
    
    if parallel and len(archive_paths) > 1:
        # 并行处理
        return parallel_process_files(archive_paths, extract_single, max_workers)
    else:
        # 串行处理
        results = {}
        for archive_path in archive_paths:
            results[archive_path] = extract_single(archive_path)
        return results


def detect_archive_codepage(archive_path: str, seven_z_path: str = "7z") -> CodePageInfo:
    """检测单个压缩包的代码页
    
    Args:
        archive_path: 压缩包路径
        seven_z_path: 7z可执行文件的路径
        
    Returns:
        代码页信息对象
    """
    selector = SmartCodePage(seven_z_path)
    return selector.detect_codepage(archive_path)


def get_archive_info(archive_path: str, seven_z_path: str = "7z") -> Optional[Dict]:
    """获取压缩包信息
    
    Args:
        archive_path: 压缩包路径
        seven_z_path: 7z可执行文件的路径
        
    Returns:
        压缩包信息字典或None
    """
    selector = SmartCodePage(seven_z_path)
    return selector.extract_archive_info(archive_path)


def test_extract_folder(test_folder: str = r"E:\2EHV\test", 
                       output_folder: Optional[str] = None,
                       seven_z_path: str = "7z",
                       parallel: bool = True,
                       max_workers: Optional[int] = None):
    """测试解压指定文件夹中的所有压缩包
    
    Args:
        test_folder: 测试文件夹路径
        output_folder: 输出文件夹路径，如果为None则在测试文件夹中创建output子文件夹
        seven_z_path: 7z可执行文件的路径
        parallel: 是否并行处理
        max_workers: 最大工作线程数
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
    
    # 批量解压
    results = batch_extract(archive_files, output_folder, seven_z_path, 
                          parallel=parallel, max_workers=max_workers)
    
    # 打印汇总结果
    logger.info("\n解压测试结果汇总:")
    logger.info("=" * 70)
    success_count = sum(1 for success in results.values() if success)
    logger.info(f"总共测试: {len(results)} 个文件")
    logger.info(f"成功解压: {success_count} 个文件")
    logger.info(f"失败: {len(results) - success_count} 个文件")
    logger.info("=" * 70)
    
    # 打印每个文件的结果
    for file_path, success in results.items():
        archive_name = os.path.basename(file_path)
        status = "成功" if success else "失败"
        # 获取代码页信息
        cp_info = detect_archive_codepage(file_path, seven_z_path)
        logger.info(f"{archive_name} - 代码页: {cp_info} - {status}")


def clear_all_caches():
    """清除所有缓存"""
    from .utils import detect_language_from_text
    
    # 清除函数级缓存
    detect_language_from_text.cache_clear()
    
    # 创建临时选择器并清除其缓存
    selector = SmartCodePage()
    selector.clear_cache()
    
    logger.info("所有缓存已清除")
