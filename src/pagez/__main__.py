"""
智能判断代码页模块 - 主入口点
用于解压时自动选择合适的代码页

这是一个重构后的模块化版本，提供以下改进：
1. 模块化设计：代码拆分为多个专门的模块
2. 性能优化：LRU缓存、延迟加载、并行处理
3. 线程安全：线程锁、线程本地存储、线程安全的缓存
4. 多进程支持：支持进程池并行处理
"""
import sys
import atexit

# 导入模块化的组件
from pagez.core.logger_config import setup_logger, get_logger
from pagez.core.api import test_extract_folder
from pagez.core.utils import cleanup_thread_resources

# 初始化日志系统
logger, config_info = setup_logger(app_name="pagez", console_output=True)




def main():
    """主入口函数"""
    try:
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
        # logger.info(f"Smart Archive Extractor v{__version__} 启动")
        logger.info(f"开始测试解压 {test_folder} 中的压缩包...")
        
        # 使用并行处理进行测试
        test_extract_folder(
            test_folder, 
            seven_z_path=seven_z_path,
            parallel=True,
            max_workers=4
        )
        
        logger.info("测试完成")
        
    except KeyboardInterrupt:
        logger.info("用户中断操作")
    except Exception as e:
        logger.error(f"运行时出错: {e}")
        sys.exit(1)
    finally:
        # 清理资源
        cleanup_thread_resources()


# 如果直接运行此模块，执行测试
if __name__ == "__main__":
    main()