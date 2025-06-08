#!/usr/bin/env python
"""
代码页选择器示例
展示如何使用codepage_pkg包选择代码页并应用于7-zip操作
"""
import os
import subprocess
import sys
from pathlib import Path

# 添加当前包到路径中（仅用于示例）
sys.path.insert(0, str(Path(__file__).parent))

# 导入包
from codepage_pkg import show_codepage_dialog, CodePageSelector


def demonstrate_basic_usage():
    """展示基本用法"""
    print("=== 基本用法示例 ===")
    
    # 显示代码页选择对话框
    codepage_id, mcp_param = show_codepage_dialog()
    
    # 处理结果
    if codepage_id is None:
        print("用户取消了选择")
    else:
        print(f"选择的代码页ID: {codepage_id}")
        print(f"7-zip参数: {mcp_param}")
        
        # 这里可以添加实际的7-zip调用
        # 例如:
        # archive_path = "example.zip"
        # extract_dir = "extracted"
        # cmd = ["7z", "x", archive_path, f"-o{extract_dir}", mcp_param]
        # subprocess.run(cmd, check=True)


def demonstrate_advanced_usage():
    """展示高级用法"""
    print("\n=== 高级用法示例 ===")
    
    # 创建临时配置文件
    config_path = "temp_config.ini"
    
    # 创建选择器实例
    selector = CodePageSelector(config_path)
    
    # 显示所有内置代码页
    print("支持的代码页:")
    for name, cp_id in selector.DEFAULT_CODEPAGES:
        print(f"  {name}: {cp_id}")
    
    # 显示对话框
    print("\n请在弹出的对话框中选择代码页...")
    codepage_id, mcp_param = selector.show_dialog()
    
    # 处理结果
    if codepage_id is None:
        print("用户取消了选择")
    else:
        print(f"选择的代码页ID: {codepage_id}")
        print(f"7-zip参数: {mcp_param}")
    
    # 清理临时文件
    if os.path.exists(config_path):
        os.remove(config_path)


def main():
    """主函数"""
    print("代码页选择器示例")
    print("================\n")
    
    # 展示基本用法
    demonstrate_basic_usage()
    
    # 展示高级用法
    demonstrate_advanced_usage()


if __name__ == "__main__":
    main() 