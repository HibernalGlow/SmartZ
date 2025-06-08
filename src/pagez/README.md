# Smart Archive Extractor - 智能压缩包解压工具

## 概述

这是一个智能代码页检测和压缩包解压工具，提供以下主要功能：

1. **智能代码页检测**：自动识别压缩包内文件名的编码，选择最佳代码页
2. **性能优化**：LRU缓存、延迟加载、并行处理
3. **线程安全**：支持多线程和多进程环境
4. **模块化设计**：代码拆分为专门的模块，易于维护和扩展

## 重构改进

### v2.0.0 重要更新

1. **模块化架构**
   - `logger_config.py` - 日志配置管理
   - `codepage_info.py` - 代码页信息和常量
   - `smart_detector.py` - 核心检测逻辑
   - `api.py` - 外部API函数
   - `utils.py` - 工具函数和优化功能
   - `__main__.py` - 简化的入口点

2. **性能优化**
   - LRU缓存机制，避免重复计算
   - 延迟加载外部库（charset_normalizer, langdetect）
   - 并行处理多个文件
   - 线程安全的subprocess调用
   - 优化的正则表达式

3. **线程/进程安全**
   - 全局线程锁保护共享资源
   - 线程本地存储
   - 线程安全的缓存数据结构
   - 进程池支持

## 使用方法

### 基本使用

```python
from pagez import smart_extract, detect_archive_codepage

# 智能解压单个文件
success = smart_extract("example.zip", target_dir="output")

# 检测压缩包代码页
codepage = detect_archive_codepage("example.zip")
print(f"检测到的代码页: {codepage}")
```

### 批量处理

```python
from pagez import batch_extract

# 批量解压多个文件（支持并行处理）
archive_list = ["file1.zip", "file2.rar", "file3.7z"]
results = batch_extract(archive_list, "output_folder", parallel=True)

for archive, success in results.items():
    print(f"{archive}: {'成功' if success else '失败'}")
```

### 高级用法

```python
from pagez import SmartCodePage, CodePageInfo

# 创建检测器实例
detector = SmartCodePage("7z")

# 为多个文件选择最佳代码页
files = ["archive1.zip", "archive2.rar"]
codepage = detector.get_codepage_for_files(files, parallel=True)

# 清除缓存
detector.clear_cache()
```

### 命令行使用

```bash
# 使用默认测试文件夹
python -m pagez

# 指定测试文件夹
python -m pagez /path/to/archives
```

## API 参考

### 主要函数

- `smart_extract(archive_path, target_dir=None, ...)` - 智能解压
- `batch_extract(archive_paths, output_folder, ...)` - 批量解压
- `detect_archive_codepage(archive_path)` - 检测代码页
- `get_codepage_param(file_paths)` - 获取代码页参数
- `test_extract_folder(test_folder, ...)` - 测试文件夹解压

### 主要类

- `SmartCodePage` - 智能代码页检测器
- `CodePageInfo` - 代码页信息类

### 常量

- `CP_GBK`, `CP_BIG5`, `CP_SHIFT_JIS`, `CP_EUC_KR`, `CP_UTF8` - 常用代码页
- `COMMON_CODEPAGES` - 常用代码页列表
- `LANG_TO_CODEPAGE` - 语言到代码页映射

## 性能特性

1. **缓存机制**
   - 文件名语言检测结果缓存
   - 压缩包信息缓存
   - 编码检测结果缓存

2. **并行处理**
   - 多文件并行检测
   - 可配置工作线程数
   - 自动资源清理

3. **延迟加载**
   - 可选库的延迟导入
   - 减少启动时间
   - 优雅降级处理

## 依赖库

### 必需依赖
- `loguru` - 日志处理

### 可选依赖（用于提高检测精度）
- `charset_normalizer` - 字符编码检测
- `langdetect` - 语言检测

## 线程安全特性

1. **全局锁**
   - subprocess调用锁
   - 外部库导入锁
   - 缓存操作锁

2. **线程本地存储**
   - 线程私有的执行器
   - 避免资源竞争

3. **安全的缓存**
   - 线程安全的LRU缓存
   - 原子操作保护

## 错误处理

- 优雅的降级机制
- 详细的错误日志
- 超时保护
- 资源自动清理

## 配置选项

所有函数都支持以下通用参数：
- `seven_z_path` - 7z可执行文件路径
- `parallel` - 是否启用并行处理
- `max_workers` - 最大工作线程数
- `timeout` - 操作超时时间

## 注意事项

1. 确保系统已安装7-zip
2. 大量文件处理时建议启用并行模式
3. 定期清理缓存以释放内存
4. 在多进程环境中使用时注意资源管理
