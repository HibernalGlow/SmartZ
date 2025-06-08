# CodePage Selector

智能代码页选择器，用于7-zip压缩解压操作。

## 项目介绍

此包从SmartZip项目提取了代码页选择功能，使其成为一个独立的Python模块。它允许用户在使用7-zip进行文件解压时，选择适当的字符编码（代码页），以确保正确处理包含非ASCII字符的文件名。

## 主要功能

- 提供直观的图形界面选择代码页
- 支持常见的中文、日文、韩文等东亚语言编码
- 允许用户添加和保存自定义代码页
- 保存用户首选项以供后续使用
- 提供简单的API以便集成到其他应用

## 安装方法

```bash
pip install codepage_pkg
```

## 基本用法

```python
from codepage_pkg import show_codepage_dialog

# 显示代码页选择对话框
codepage_id, mcp_param = show_codepage_dialog()

# 如果用户选择了代码页
if codepage_id is not None:
    print(f"选择的代码页ID: {codepage_id}")
    print(f"7-zip参数: {mcp_param}")
    
    # 在调用7-zip时使用这个参数
    # 例如: subprocess.run(["7z", "x", "archive.zip", mcp_param])
```

## 高级用法

```python
from codepage_pkg import CodePageSelector

# 创建选择器实例，可以指定配置文件路径
selector = CodePageSelector("path/to/config.ini")

# 显示对话框
codepage_id, mcp_param = selector.show_dialog()

# 获取所有支持的代码页
all_codepages = selector.get_all_codepages()
for name, cp_id in all_codepages:
    print(f"{name}: {cp_id}")
```

## 依赖项

- Python 3.6+
- tkinter (通常包含在Python标准库中)

## 许可证

MIT

## 致谢

此项目基于[SmartZip](https://github.com/vvyesuNi/SmartZip)项目的代码页选择功能，该功能原本用AutoHotkey实现。 