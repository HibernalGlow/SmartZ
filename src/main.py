"""
SmartZip主入口文件
处理命令行参数和程序启动逻辑
"""
import sys
import os
import argparse
from pathlib import Path

# 添加当前目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from config import ConfigManager
from smartzip import SmartZip
from gui import show_settings
from context_menu import register_menu, unregister_menu


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="SmartZip - 7-zip功能扩展工具")
    parser.add_argument('operation', nargs='?', choices=['x', 'xc', 'o', 'a'], 
                       help='操作类型: x=解压, xc=选择编码解压, o=打开, a=压缩')
    parser.add_argument('files', nargs='*', help='要处理的文件或目录')
    parser.add_argument('--settings', action='store_true', help='显示设置界面')
    parser.add_argument('--register-menu', action='store_true', help='注册右键菜单')
    parser.add_argument('--unregister-menu', action='store_true', help='卸载右键菜单')
    parser.add_argument('--version', action='version', version='SmartZip Python 3.4')
    
    args = parser.parse_args()
    
    try:
        # 初始化配置管理器
        config = ConfigManager()
        
        # 处理特殊命令
        if args.settings or (not args.operation and not args.files):
            show_settings()
            return
        
        if args.register_menu:
            register_menu()
            return
            
        if args.unregister_menu:
            unregister_menu()
            return
        
        # 处理文件操作
        if args.operation or args.files:
            # 构建参数列表
            file_args = []
            if args.operation:
                file_args.append(args.operation)
            file_args.extend(args.files)
            
            # 如果没有指定操作但有文件，默认为解压
            if not args.operation and args.files:
                file_args.insert(0, 'x')
            
            # 创建SmartZip实例并执行
            smartzip = SmartZip(config)
            smartzip.init(file_args).exec()
        else:
            # 没有参数，显示设置界面
            show_settings()
            
    except KeyboardInterrupt:
        print("\n操作已取消")
        sys.exit(1)
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
