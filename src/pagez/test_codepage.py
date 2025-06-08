#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试智能代码页检测功能
"""
import os
import sys
import argparse
import logging
from pagez.main import test_extract_folder, SmartCodePage, smart_extract, CodePageInfo

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_codepage")

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
    parser.add_argument('--debug', '-d', action='store_true',
                        help='启用调试模式')
    
    args = parser.parse_args()
    
    # 设置日志级别
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # 检查测试文件夹是否存在
    if not os.path.exists(args.folder):
        logger.error(f"测试文件夹不存在: {args.folder}")
        return 1
    
    # 如果只是列出检测结果
    if args.list_only:
        list_detected_codepages(args.folder, args.seven_z_path, args.debug)
    else:
        # 执行完整测试
        test_extract_folder(args.folder, args.output, args.seven_z_path)
    
    return 0

def list_detected_codepages(test_folder, seven_z_path="7z", debug=False):
    """仅列出检测到的代码页，不执行解压"""
    # 获取所有压缩包文件
    archive_extensions = ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2']
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
    selector = SmartCodePage(seven_z_path, debug=debug)
    
    # 测试每个压缩包
    results = []
    for archive_path in archive_files:
        archive_name = os.path.basename(archive_path)
        logger.info(f"\n正在处理: {archive_name}")
        
        # 1. 从文件名检测
        filename_cp = selector.detect_codepage_from_filename(archive_name)
        logger.info(f"从文件名检测的代码页: {filename_cp}")
        
        # 2. 从内容检测
        content_cp = selector.detect_codepage_from_archive_content(archive_path)
        logger.info(f"从内容检测的代码页: {content_cp}")
        
        # 3. 智能检测
        smart_cp = selector.detect_codepage(archive_path)
        logger.info(f"智能检测的代码页: {smart_cp}")
        
        # 记录结果
        results.append({
            "file": archive_name,
            "filename_cp": filename_cp,
            "content_cp": content_cp,
            "smart_cp": smart_cp
        })
    
    # 打印汇总结果
    logger.info("\n代码页检测结果汇总:")
    logger.info("=" * 70)
    logger.info(f"{'文件名':<30} | {'文件名检测':<20} | {'内容检测':<20} | {'智能检测':<20}")
    logger.info("-" * 70)
    
    for result in results:
        logger.info(f"{result['file']:<30} | {result['filename_cp']:<20} | {result['content_cp']:<20} | {result['smart_cp']:<20}")

if __name__ == "__main__":
    sys.exit(main())