#!/usr/bin/env python
"""
SmartZip集成示例
展示如何将代码页选择器集成到SmartZip的Python版本中
"""
import os
import sys
import re
from pathlib import Path
import subprocess
from typing import List, Optional, Tuple

# 添加当前包到路径中（仅用于示例）
sys.path.insert(0, str(Path(__file__).parent))

# 导入代码页选择器
from codepage_pkg import show_codepage_dialog


class SmartZipIntegration:
    """SmartZip集成示例类"""
    
    def __init__(self, seven_zip_path: Optional[str] = None):
        """初始化
        
        Args:
            seven_zip_path: 7-zip可执行文件路径，如果为None则尝试查找
        """
        # 设置7-zip路径
        self.seven_z = self._find_7zip(seven_zip_path)
        if not self.seven_z:
            raise FileNotFoundError("未找到7-zip可执行文件，请安装7-zip或提供正确的路径")
        
        print(f"使用7-zip路径: {self.seven_z}")
        
        # 初始化代码页
        self.code_page = ""
    
    def _find_7zip(self, path: Optional[str] = None) -> Optional[str]:
        """查找7-zip可执行文件
        
        Args:
            path: 指定的7-zip路径
            
        Returns:
            7-zip可执行文件的路径，如果未找到则返回None
        """
        if path and os.path.exists(path):
            return path
        
        # 常见的7-zip安装位置
        common_paths = []
        
        # Windows系统
        if sys.platform == "win32":
            program_files = os.environ.get("ProgramFiles", "C:\\Program Files")
            program_files_x86 = os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)")
            
            common_paths = [
                os.path.join(program_files, "7-Zip", "7z.exe"),
                os.path.join(program_files_x86, "7-Zip", "7z.exe"),
                "C:\\7-Zip\\7z.exe"
            ]
        # Linux系统
        elif sys.platform.startswith("linux"):
            common_paths = [
                "/usr/bin/7z",
                "/usr/local/bin/7z"
            ]
        # macOS系统
        elif sys.platform == "darwin":
            common_paths = [
                "/usr/local/bin/7z",
                "/opt/homebrew/bin/7z"
            ]
            
        # 检查常见路径
        for p in common_paths:
            if os.path.exists(p):
                return p
        
        # 尝试从PATH环境变量中查找
        try:
            result = subprocess.run(["which", "7z"] if sys.platform != "win32" else ["where", "7z.exe"],
                                    capture_output=True, text=True, check=False)
            if result.returncode == 0:
                path = result.stdout.strip()
                if path and os.path.exists(path):
                    return path
        except:
            pass
        
        return None
    
    def select_code_page(self):
        """选择代码页"""
        # 使用代码页选择器
        codepage_id, mcp_param = show_codepage_dialog()
        
        if codepage_id is not None:
            print(f"选择的代码页: {codepage_id}")
            self.code_page = mcp_param
        else:
            print("未选择代码页")
    
    def extract_archive(self, archive_path: str, target_dir: Optional[str] = None):
        """解压缩文件
        
        Args:
            archive_path: 压缩包路径
            target_dir: 目标目录，如果为None则使用当前目录
        """
        if not os.path.exists(archive_path):
            print(f"错误: 文件不存在 {archive_path}")
            return False
        
        # 创建目标目录
        if target_dir is None:
            # 使用压缩包名称作为目标目录
            base_name = os.path.splitext(os.path.basename(archive_path))[0]
            target_dir = os.path.join(os.path.dirname(archive_path), base_name)
        
        os.makedirs(target_dir, exist_ok=True)
        
        # 构建命令
        cmd = [self.seven_z, "x", archive_path, f"-o{target_dir}", "-aou"]
        
        # 添加代码页参数
        if self.code_page:
            cmd.append(self.code_page)
        
        print(f"执行命令: {' '.join(cmd)}")
        
        # 执行命令
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            print("解压成功!")
            return True
        except subprocess.CalledProcessError as e:
            print(f"解压失败: {e}")
            print(f"错误输出: {e.stderr}")
            return False


def main():
    """主函数"""
    print("SmartZip集成示例")
    print("================\n")
    
    try:
        # 创建SmartZip集成实例
        smart_zip = SmartZipIntegration()
        
        # 提示用户选择代码页
        print("\n请选择代码页...")
        smart_zip.select_code_page()
        
        # 在实际应用中，这里可以使用提供的压缩包路径
        # 在此示例中，我们只打印提示信息
        print("\n在实际应用中，您可以使用如下代码解压缩文件:")
        print('smart_zip.extract_archive("example.zip", "output_dir")')
        
    except Exception as e:
        print(f"错误: {e}")


if __name__ == "__main__":
    main() 