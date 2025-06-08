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
from typing import Optional, List, Tuple, Dict, Set
from pathlib import Path


class SmartCodePage:
    """智能代码页选择器"""
    
    # 常用代码页和对应的标识符
    COMMON_CODEPAGES = [
        ("简体中文（GBK）", 936),
        ("繁体中文（大五码）", 950),
        ("日文（Shift_JIS）", 932),
        ("韩文（EUC-KR）", 949),
        ("UTF-8 Unicode", 65001)
    ]
    
    # 字符集范围
    CHARSET_RANGES = {
        "chinese_simplified": r'[\u4e00-\u9fff]',
        "chinese_traditional": r'[\u4e00-\u9fff\u3400-\u4dbf]',  # 包含繁体字特有字符
        "japanese": r'[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff]',
        "korean": r'[\uac00-\ud7a3\u1100-\u11ff]'
    }
    
    def __init__(self, seven_z_path: str = "7z"):
        """初始化代码页选择器
        
        Args:
            seven_z_path: 7z可执行文件的路径
        """
        self.selected_codepage = None
        self.mcp_param = None
        self.seven_z_path = seven_z_path
    
    def auto_detect_codepage_from_filename(self, filename: str) -> Tuple[int, str]:
        """根据文件名自动检测代码页
        
        Args:
            filename: 压缩包文件名
            
        Returns:
            (代码页ID, 7-zip格式的代码页参数)
        """
        # 检查文件名中是否包含中文字符
        if re.search(self.CHARSET_RANGES["chinese_simplified"], filename):
            # 检测到中文，使用GBK
            return self.COMMON_CODEPAGES[0][1], f" -mcp={self.COMMON_CODEPAGES[0][1]}"
        
        # 检查文件名中是否包含日文字符
        if re.search(self.CHARSET_RANGES["japanese"], filename):
            # 检测到日文，使用Shift_JIS
            return self.COMMON_CODEPAGES[2][1], f" -mcp={self.COMMON_CODEPAGES[2][1]}"
        
        # 检查文件名中是否包含韩文字符
        if re.search(self.CHARSET_RANGES["korean"], filename):
            # 检测到韩文，使用EUC-KR
            return self.COMMON_CODEPAGES[3][1], f" -mcp={self.COMMON_CODEPAGES[3][1]}"
        
        # 默认使用UTF-8
        return self.COMMON_CODEPAGES[4][1], f" -mcp={self.COMMON_CODEPAGES[4][1]}"
    
    def extract_archive_info(self, archive_path: str) -> Optional[Dict]:
        """提取压缩包信息
        
        Args:
            archive_path: 压缩包路径
            
        Returns:
            压缩包信息字典或None
        """
        try:
            cmd = [self.seven_z_path, 'l', '-slt', archive_path]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                print(f"无法读取压缩包信息: {archive_path}")
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
            print(f"提取压缩包信息出错: {e}")
            return None
    
    def detect_codepage_from_archive_content(self, archive_path: str) -> Tuple[int, str]:
        """根据压缩包内容检测代码页
        
        Args:
            archive_path: 压缩包路径
            
        Returns:
            (代码页ID, 7-zip格式的代码页参数)
        """
        # 首先获取压缩包信息
        info = self.extract_archive_info(archive_path)
        if not info:
            # 如果无法获取压缩包信息，则根据文件名判断
            return self.auto_detect_codepage_from_filename(os.path.basename(archive_path))
        
        # 统计各语言字符的出现次数
        char_counts = {
            "chinese_simplified": 0,
            "chinese_traditional": 0,
            "japanese": 0,
            "korean": 0
        }
        
        # 分析压缩包中的文件名
        for file_item in info['files']:
            filename = file_item.get('Path', '')
            
            # 检测各种语言字符
            for lang, pattern in self.CHARSET_RANGES.items():
                if re.search(pattern, filename):
                    char_counts[lang] += 1
        
        # 根据统计结果选择代码页
        if char_counts["chinese_simplified"] > 0:
            # 检测到简体中文，使用GBK
            return self.COMMON_CODEPAGES[0][1], f" -mcp={self.COMMON_CODEPAGES[0][1]}"
        elif char_counts["chinese_traditional"] > 0:
            # 检测到繁体中文，使用Big5
            return self.COMMON_CODEPAGES[1][1], f" -mcp={self.COMMON_CODEPAGES[1][1]}"
        elif char_counts["japanese"] > 0:
            # 检测到日文，使用Shift_JIS
            return self.COMMON_CODEPAGES[2][1], f" -mcp={self.COMMON_CODEPAGES[2][1]}"
        elif char_counts["korean"] > 0:
            # 检测到韩文，使用EUC-KR
            return self.COMMON_CODEPAGES[3][1], f" -mcp={self.COMMON_CODEPAGES[3][1]}"
        
        # 默认使用UTF-8
        return self.COMMON_CODEPAGES[4][1], f" -mcp={self.COMMON_CODEPAGES[4][1]}"
    
    def test_extract_with_codepage(self, archive_path: str, codepage_id: int) -> bool:
        """测试使用指定代码页解压文件是否成功
        
        Args:
            archive_path: 压缩包路径
            codepage_id: 代码页ID
            
        Returns:
            解压是否成功
        """
        # 创建临时目录
        temp_dir = tempfile.mkdtemp(prefix="codepage_test_")
        try:
            # 尝试解压几个文件来测试代码页
            cmd = [
                self.seven_z_path, 
                "e", 
                archive_path, 
                f"-o{temp_dir}", 
                "-aou",  # 自动重命名
                f"-mcp={codepage_id}",
                "-y"  # 自动回答是
            ]
            
            # 添加限制提取的文件数量
            cmd.append("-i!*")  # 最多提取10个文件
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            # 检查是否成功解压
            success = result.returncode == 0 and os.listdir(temp_dir)
            
            return success
        except Exception as e:
            print(f"测试代码页时出错: {e}")
            return False
        finally:
            # 清理临时目录
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def smart_detect_codepage(self, archive_path: str) -> Tuple[int, str]:
        """智能检测压缩包的代码页
        
        结合文件名和内容分析，并尝试测试解压来确定最佳代码页
        
        Args:
            archive_path: 压缩包路径
            
        Returns:
            (代码页ID, 7-zip格式的代码页参数)
        """
        # 1. 首先根据压缩包内容检测
        content_cp_id, content_cp_param = self.detect_codepage_from_archive_content(archive_path)
        
        # 2. 再根据文件名检测
        filename_cp_id, filename_cp_param = self.auto_detect_codepage_from_filename(os.path.basename(archive_path))
        
        # 3. 如果两者结果不同，尝试测试解压来验证
        if content_cp_id != filename_cp_id:
            # 测试内容检测的代码页
            if self.test_extract_with_codepage(archive_path, content_cp_id):
                return content_cp_id, content_cp_param
            
            # 测试文件名检测的代码页
            if self.test_extract_with_codepage(archive_path, filename_cp_id):
                return filename_cp_id, filename_cp_param
            
            # 如果都不行，尝试其他常用代码页
            for _, cp_id in self.COMMON_CODEPAGES:
                if cp_id not in (content_cp_id, filename_cp_id):
                    if self.test_extract_with_codepage(archive_path, cp_id):
                        return cp_id, f" -mcp={cp_id}"
        
        # 优先使用内容检测的结果
        return content_cp_id, content_cp_param
    
    def get_codepage_for_files(self, file_paths: List[str]) -> Tuple[int, str]:
        """为多个文件智能选择代码页
        
        Args:
            file_paths: 文件路径列表
            
        Returns:
            (代码页ID, 7-zip格式的代码页参数)
        """
        # 统计各代码页的权重
        codepage_weights = {cp_id: 0 for _, cp_id in self.COMMON_CODEPAGES}
        
        for file_path in file_paths:
            if not os.path.exists(file_path):
                print(f"文件不存在: {file_path}")
                continue
                
            cp_id, _ = self.smart_detect_codepage(file_path)
            codepage_weights[cp_id] += 1
        
        # 选择权重最高的代码页
        if sum(codepage_weights.values()) > 0:
            selected_cp_id = max(codepage_weights, key=codepage_weights.get)
            return selected_cp_id, f" -mcp={selected_cp_id}"
        else:
            # 如果没有有效的文件，返回系统默认代码页
            return self.get_system_default_codepage()
    
    def get_system_default_codepage(self) -> Tuple[int, str]:
        """获取系统默认代码页
        
        Returns:
            (代码页ID, 7-zip格式的代码页参数)
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
                    for _, supported_cp in self.COMMON_CODEPAGES:
                        if cp_id == supported_cp:
                            return cp_id, f" -mcp={cp_id}"
            except Exception as e:
                print(f"获取系统代码页出错: {e}")
            
            # 如果无法获取或不支持，根据环境变量判断
            if os.environ.get('LANG', '').startswith('zh_CN') or \
               os.environ.get('LANGUAGE', '').startswith('zh_CN'):
                return self.COMMON_CODEPAGES[0][1], f" -mcp={self.COMMON_CODEPAGES[0][1]}"
            # 繁体中文Windows
            elif os.environ.get('LANG', '').startswith('zh_TW') or \
                 os.environ.get('LANGUAGE', '').startswith('zh_TW'):
                return self.COMMON_CODEPAGES[1][1], f" -mcp={self.COMMON_CODEPAGES[1][1]}"
            # 日文Windows
            elif os.environ.get('LANG', '').startswith('ja') or \
                 os.environ.get('LANGUAGE', '').startswith('ja'):
                return self.COMMON_CODEPAGES[2][1], f" -mcp={self.COMMON_CODEPAGES[2][1]}"
            # 韩文Windows
            elif os.environ.get('LANG', '').startswith('ko') or \
                 os.environ.get('LANGUAGE', '').startswith('ko'):
                return self.COMMON_CODEPAGES[3][1], f" -mcp={self.COMMON_CODEPAGES[3][1]}"
        
        # 默认使用UTF-8
        return self.COMMON_CODEPAGES[4][1], f" -mcp={self.COMMON_CODEPAGES[4][1]}"


def get_codepage_param(file_paths: List[str], seven_z_path: str = "7z") -> str:
    """便捷函数：获取适合给定文件的代码页参数
    
    Args:
        file_paths: 文件路径列表
        seven_z_path: 7z可执行文件的路径
        
    Returns:
        7-zip格式的代码页参数
    """
    selector = SmartCodePage(seven_z_path)
    _, mcp_param = selector.get_codepage_for_files(file_paths)
    return mcp_param


def smart_extract(archive_path: str, target_dir: Optional[str] = None, 
                 seven_z_path: str = "7z", password: Optional[str] = None) -> bool:
    """智能解压函数
    
    使用智能代码页检测来解压文件
    
    Args:
        archive_path: 压缩包路径
        target_dir: 目标目录，如果为None则解压到当前目录下的同名文件夹
        seven_z_path: 7z可执行文件的路径
        password: 解压密码，如果为None则尝试无密码解压
        
    Returns:
        解压是否成功
    """
    # 检查文件是否存在
    if not os.path.exists(archive_path):
        print(f"文件不存在: {archive_path}")
        return False
    
    # 如果未指定目标目录，创建同名目录
    if target_dir is None:
        target_dir = os.path.splitext(os.path.basename(archive_path))[0]
    
    # 确保目标目录存在
    os.makedirs(target_dir, exist_ok=True)
    
    # 智能检测代码页
    selector = SmartCodePage(seven_z_path)
    cp_id, cp_param = selector.smart_detect_codepage(archive_path)
    print(f"为 {os.path.basename(archive_path)} 选择的代码页: {cp_id}")
    
    # 构建解压命令
    cmd = [seven_z_path, "x", archive_path, f"-o{target_dir}", "-aou"]
    
    # 添加代码页参数
    cmd.append(f"-mcp={cp_id}")
    
    # 添加密码参数
    if password:
        cmd.append(f"-p{password}")
    else:
        cmd.append("-p")  # 空密码
    
    # 自动回答是
    cmd.append("-y")
    
    try:
        # 执行解压命令
        print(f"执行命令: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # 检查是否成功
        if result.returncode == 0:
            print(f"成功解压 {os.path.basename(archive_path)} 到 {target_dir}")
            return True
        else:
            print(f"解压失败，错误码: {result.returncode}")
            print(f"错误信息: {result.stderr}")
            return False
    except Exception as e:
        print(f"解压过程中发生错误: {e}")
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
        print(f"测试文件夹不存在: {test_folder}")
        return
    
    # 设置输出文件夹
    if output_folder is None:
        output_folder = os.path.join(test_folder, "output")
    
    # 确保输出文件夹存在
    os.makedirs(output_folder, exist_ok=True)
    
    # 获取所有压缩包文件
    archive_extensions = ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2']
    archive_files = []
    
    for root, _, files in os.walk(test_folder):
        for file in files:
            if any(file.lower().endswith(ext) for ext in archive_extensions):
                archive_files.append(os.path.join(root, file))
    
    if not archive_files:
        print(f"在 {test_folder} 中未找到压缩包文件")
        return
    
    print(f"找到 {len(archive_files)} 个压缩包文件")
    
    # 创建智能代码页选择器
    selector = SmartCodePage(seven_z_path)
    
    # 测试每个压缩包
    results = []
    for archive_path in archive_files:
        archive_name = os.path.basename(archive_path)
        print(f"\n正在处理: {archive_name}")
        
        # 智能检测代码页
        cp_id, cp_param = selector.smart_detect_codepage(archive_path)
        print(f"检测到的代码页: {cp_id}")
        
        # 创建解压目标文件夹
        target_dir = os.path.join(output_folder, os.path.splitext(archive_name)[0])
        
        # 执行解压
        success = smart_extract(archive_path, target_dir, seven_z_path)
        
        # 记录结果
        results.append({
            "file": archive_name,
            "codepage": cp_id,
            "success": success
        })
    
    # 打印汇总结果
    print("\n解压测试结果汇总:")
    print("=" * 50)
    success_count = sum(1 for r in results if r["success"])
    print(f"总共测试: {len(results)} 个文件")
    print(f"成功解压: {success_count} 个文件")
    print(f"失败: {len(results) - success_count} 个文件")
    print("=" * 50)
    
    # 打印每个文件的结果
    for result in results:
        status = "成功" if result["success"] else "失败"
        print(f"{result['file']} - 代码页: {result['codepage']} - {status}")


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
    print(f"开始测试解压 {test_folder} 中的压缩包...")
    test_extract_folder(test_folder, seven_z_path=seven_z_path)