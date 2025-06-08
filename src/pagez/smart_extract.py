#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
智能解压工具
使用智能代码页检测功能来解压文件
"""
import os
import sys
import argparse
from pagez.main import smart_extract, SmartCodePage

def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='智能解压工具')
    parser.add_argument('archive', type=str, nargs='+',
                        help='要解压的压缩包路径，支持多个文件')
    parser.add_argument('--output', '-o', type=str, default=None,
                        help='输出文件夹路径，默认为压缩包同名文件夹')
    parser.add_argument('--7z', '-z', dest='seven_z_path', type=str, default="7z",
                        help='7z可执行文件的路径，默认为"7z"')
    parser.add_argument('--password', '-p', type=str, default=None,
                        help='解压密码，如果有的话')
    parser.add_argument('--detect-only', '-d', action='store_true',
                        help='仅检测代码页，不执行解压')
    
    args = parser.parse_args()
    
    # 检查文件是否存在
    archive_files = []
    for path in args.archive:
        if os.path.exists(path):
            archive_files.append(path)
        else:
            print(f"文件不存在: {path}")
    
    if not archive_files:
        print("没有找到有效的压缩包文件")
        return 1
    
    # 创建智能代码页选择器
    selector = SmartCodePage(args.seven_z_path)
    
    # 如果只是检测代码页
    if args.detect_only:
        for archive_path in archive_files:
            archive_name = os.path.basename(archive_path)
            print(f"\n正在处理: {archive_name}")
            
            # 智能检测代码页
            cp_id, cp_param = selector.smart_detect_codepage(archive_path)
            print(f"检测到的代码页: {cp_id}")
            
            # 显示详细信息
            print("代码页详细信息:")
            for name, id in selector.COMMON_CODEPAGES:
                if id == cp_id:
                    print(f"  名称: {name}")
                    print(f"  ID: {id}")
                    print(f"  7z参数: {cp_param}")
                    break
    else:
        # 执行解压
        success_count = 0
        for archive_path in archive_files:
            # 如果指定了输出目录，则使用它；否则为每个压缩包创建单独的目录
            if args.output:
                if len(archive_files) == 1:
                    # 单个文件，直接使用指定的输出目录
                    target_dir = args.output
                else:
                    # 多个文件，在指定的输出目录下创建以压缩包命名的子目录
                    basename = os.path.splitext(os.path.basename(archive_path))[0]
                    target_dir = os.path.join(args.output, basename)
            else:
                # 未指定输出目录，使用压缩包同名目录
                target_dir = None
            
            # 执行智能解压
            if smart_extract(archive_path, target_dir, args.seven_z_path, args.password):
                success_count += 1
        
        # 打印汇总结果
        print(f"\n解压完成: {success_count}/{len(archive_files)} 个文件成功")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 