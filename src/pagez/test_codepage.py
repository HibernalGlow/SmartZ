#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试智能代码页检测功能
"""
import os
import sys
import argparse
from pagez.main import test_extract_folder, SmartCodePage

def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='测试智能代码页检测功能')
    parser.add_argument('--folder', '-f', type=str, default=r"E:\2EHV\test",
                        help='要测试的文件夹路径，默认为E:\\2EHV\\test')
    parser.add_argument('--output', '-o', type=str, default=None,
                        help='输出文件夹路径，默认在测试文件夹中创建output子文件夹')
    parser.add_argument('--7z', '-z', dest='seven_z_path', type=str, default="7z",
                        help='7z可执行文件的路径，默认为"7z"')
    parser.add_argument('--list-only', '-l', action='store_true',
                        help='仅列出检测到的代码页，不执行解压')
    
    args = parser.parse_args()
    
    # 检查测试文件夹是否存在
    if not os.path.exists(args.folder):
        print(f"测试文件夹不存在: {args.folder}")
        return 1
    
    # 如果只是列出检测结果
    if args.list_only:
        list_detected_codepages(args.folder, args.seven_z_path)
    else:
        # 执行完整测试
        test_extract_folder(args.folder, args.output, args.seven_z_path)
    
    return 0

def list_detected_codepages(test_folder, seven_z_path="7z"):
    """仅列出检测到的代码页，不执行解压"""
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
        
        # 1. 从文件名检测
        filename_cp_id, _ = selector.auto_detect_codepage_from_filename(archive_name)
        print(f"从文件名检测的代码页: {filename_cp_id}")
        
        # 2. 从内容检测
        content_cp_id, _ = selector.detect_codepage_from_archive_content(archive_path)
        print(f"从内容检测的代码页: {content_cp_id}")
        
        # 3. 智能检测
        smart_cp_id, _ = selector.smart_detect_codepage(archive_path)
        print(f"智能检测的代码页: {smart_cp_id}")
        
        # 记录结果
        results.append({
            "file": archive_name,
            "filename_cp": filename_cp_id,
            "content_cp": content_cp_id,
            "smart_cp": smart_cp_id
        })
    
    # 打印汇总结果
    print("\n代码页检测结果汇总:")
    print("=" * 70)
    print(f"{'文件名':<30} | {'文件名检测':<10} | {'内容检测':<10} | {'智能检测':<10}")
    print("-" * 70)
    
    for result in results:
        print(f"{result['file']:<30} | {result['filename_cp']:<10} | {result['content_cp']:<10} | {result['smart_cp']:<10}")

if __name__ == "__main__":
    sys.exit(main()) 