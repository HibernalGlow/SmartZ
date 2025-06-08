"""
代码页选择模块
提供选择7-zip使用的代码页功能
"""
import os
import re
import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser
from typing import Optional, List, Tuple, Dict, Callable, Any
import configparser


class CodePageConfig:
    """代码页配置管理器"""
    
    def __init__(self, config_path: Optional[str] = None):
        """初始化配置管理器
        
        Args:
            config_path: 配置文件路径，如果为None则使用默认路径
        """
        if config_path is None:
            # 默认配置文件位于用户目录下的.codepage.ini
            self.config_path = os.path.join(os.path.expanduser("~"), ".codepage.ini")
        else:
            self.config_path = config_path
            
        # 禁用插值功能来避免%符号问题
        self.config = configparser.ConfigParser(interpolation=None)
        self.config.optionxform = str  # 保持键名大小写
        
        # 确保配置文件存在
        self._ensure_config_exists()
        self._load_config()
    
    def _ensure_config_exists(self):
        """确保配置文件存在，如果不存在则创建默认配置"""
        if not os.path.exists(self.config_path):
            self._create_default_config()
    
    def _create_default_config(self):
        """创建默认配置文件"""
        # 确保目录存在
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        
        # 添加默认配置
        if not self.config.has_section('codepage'):
            self.config.add_section('codepage')
        
        # 保存配置
        self._save_config()
    
    def _load_config(self):
        """加载配置文件"""
        if os.path.exists(self.config_path):
            self.config.read(self.config_path, encoding='utf-8')
    
    def _save_config(self):
        """保存配置文件"""
        with open(self.config_path, 'w', encoding='utf-8') as f:
            self.config.write(f)
    
    def get_custom_codepages(self) -> List[str]:
        """获取自定义代码页列表
        
        Returns:
            自定义代码页列表
        """
        custom_codepages = []
        if self.config.has_section('codepage'):
            for key, value in self.config.items('codepage'):
                custom_codepages.append(value)
        return custom_codepages
    
    def save_custom_codepages(self, codepages: List[str]):
        """保存自定义代码页列表
        
        Args:
            codepages: 自定义代码页列表
        """
        # 清除现有配置
        if self.config.has_section('codepage'):
            self.config.remove_section('codepage')
        
        # 添加新配置
        self.config.add_section('codepage')
        for i, codepage in enumerate(codepages):
            self.config.set('codepage', str(i+1), codepage)
        
        # 保存配置
        self._save_config()


class CodePageSelector:
    """代码页选择器"""
    
    # 内置代码页和对应的数字标识符
    DEFAULT_CODEPAGES = [
        ("简体中文（GBK）", 936),
        ("繁体中文（大五码）", 950),
        ("日文（Shift_JIS）", 932),
        ("韩文（EUC-KR）", 949),
        ("UTF-8 Unicode", 65001)
    ]
    
    def __init__(self, config_path: Optional[str] = None):
        """初始化代码页选择器
        
        Args:
            config_path: 配置文件路径，如果为None则使用默认路径
        """
        self.config = CodePageConfig(config_path)
        self.result_codepage = None
        self.result_mcp_param = None
    
    def get_all_codepages(self) -> List[Tuple[str, int]]:
        """获取所有代码页列表（包括内置和自定义的）
        
        Returns:
            代码页名称和ID元组的列表
        """
        # 先添加内置代码页
        all_codepages = list(self.DEFAULT_CODEPAGES)
        
        # 添加自定义代码页
        for cp in self.config.get_custom_codepages():
            if cp.isdigit():
                all_codepages.append((cp, int(cp)))
        
        return all_codepages
    
    def show_dialog(self) -> Tuple[Optional[int], Optional[str]]:
        """显示代码页选择对话框
        
        Returns:
            (代码页ID, 7-zip格式的代码页参数)
        """
        self.result_codepage = None
        self.result_mcp_param = None
        
        # 创建对话框
        dialog = CodePageDialog(self)
        dialog.show()
        
        return self.result_codepage, self.result_mcp_param


class CodePageDialog:
    """代码页选择对话框"""
    
    def __init__(self, selector: CodePageSelector):
        """初始化对话框
        
        Args:
            selector: 代码页选择器实例
        """
        self.selector = selector
        self.custom_codepages = selector.config.get_custom_codepages()
        
        # 创建主窗口
        self.root = tk.Tk()
        self.root.title("请选择或输入你需要的代码页")
        self.root.geometry("450x250")
        self.root.resizable(True, False)
        
        # 使用合适的主题
        style = ttk.Style()
        self.root.configure(background=style.lookup('TFrame', 'background'))
        
        # 阻止关闭按钮，必须通过对话框按钮关闭
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # 创建GUI元素
        self._create_widgets()
    
    def _create_widgets(self):
        """创建GUI组件"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # 说明标签
        ttk.Label(main_frame, text="选择或输入代码页:").grid(
            row=0, column=0, columnspan=3, sticky=tk.W, pady=(0, 5))
        
        # 链接标签
        link = ttk.Label(main_frame, text="其他代码页参考", foreground="blue", cursor="hand2")
        link.grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=(0, 10))
        link.bind("<Button-1>", 
                 lambda e: webbrowser.open("https://docs.microsoft.com/zh-cn/windows/win32/intl/code-page-identifiers"))
        
        # 下拉框
        self.codepage_list = self._get_codepage_list()
        self.combo_var = tk.StringVar()
        self.combo = ttk.Combobox(main_frame, textvariable=self.combo_var, width=40)
        self.combo['values'] = self.codepage_list
        self.combo.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 按钮框架
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E))
        
        # 添加按钮
        ttk.Button(btn_frame, text="添加", command=self.add_codepage).grid(
            row=0, column=0, padx=(0, 5))
        
        # 删除按钮
        ttk.Button(btn_frame, text="删除", command=self.delete_codepage).grid(
            row=0, column=1, padx=5)
        
        # 确定按钮
        ttk.Button(btn_frame, text="确定", command=self.on_confirm).grid(
            row=0, column=2, padx=5)
        
        # 取消按钮
        ttk.Button(btn_frame, text="取消", command=self.on_close).grid(
            row=0, column=3, padx=(5, 0))
        
        # 提示文本
        tip_text = "提示: 如需添加自定义代码页，请输入数字标识符后点击添加"
        ttk.Label(main_frame, text=tip_text, foreground="gray").grid(
            row=4, column=0, columnspan=3, sticky=tk.W, pady=(10, 0))
    
    def _get_codepage_list(self) -> List[str]:
        """获取代码页列表（用于显示在下拉框中）
        
        Returns:
            代码页名称列表
        """
        # 添加内置代码页
        codepage_list = [name for name, _ in self.selector.DEFAULT_CODEPAGES]
        
        # 添加自定义代码页
        codepage_list.extend(self.custom_codepages)
        
        return codepage_list
    
    def add_codepage(self):
        """添加自定义代码页"""
        text = self.combo_var.get().strip()
        
        # 验证是否为数字
        if not text.isdigit():
            self._show_error("请输入有效的代码页标识符（数字）")
            return
        
        # 检查是否已存在
        if text in self.custom_codepages or text in [name for name, _ in self.selector.DEFAULT_CODEPAGES]:
            self._show_error("该代码页已存在")
            return
        
        # 添加到列表
        self.custom_codepages.append(text)
        
        # 更新下拉框
        self.combo['values'] = self._get_codepage_list()
        self.combo.set("")
    
    def delete_codepage(self):
        """删除自定义代码页"""
        text = self.combo_var.get().strip()
        
        # 检查是否为自定义代码页
        if text not in self.custom_codepages:
            self._show_error("只能删除自定义代码页")
            return
        
        # 从列表中删除
        self.custom_codepages.remove(text)
        
        # 更新下拉框
        self.combo['values'] = self._get_codepage_list()
        self.combo.set("")
    
    def on_confirm(self):
        """确定按钮点击事件"""
        text = self.combo_var.get().strip()
        
        # 设置结果
        if text.isdigit():
            # 如果输入的是数字，直接使用
            self.selector.result_codepage = int(text)
            self.selector.result_mcp_param = f" -mcp={text}"
        else:
            # 如果是名称，查找对应的代码页ID
            for name, cp_id in self.selector.get_all_codepages():
                if text == name:
                    self.selector.result_codepage = cp_id
                    self.selector.result_mcp_param = f" -mcp={cp_id}"
                    break
        
        # 保存自定义代码页
        self.selector.config.save_custom_codepages(self.custom_codepages)
        
        # 关闭对话框
        self.root.destroy()
    
    def on_close(self):
        """关闭对话框"""
        self.selector.result_codepage = None
        self.selector.result_mcp_param = None
        self.root.destroy()
    
    def _show_error(self, message: str):
        """显示错误消息
        
        Args:
            message: 错误消息
        """
        messagebox.showerror("错误", message)
    
    def show(self):
        """显示对话框并等待结果"""
        # 设置为模态对话框
        self.root.grab_set()
        self.root.focus_set()
        
        # 居中显示
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'+{x}+{y}')
        
        # 显示并等待
        self.root.mainloop()


def show_codepage_dialog(config_path: Optional[str] = None) -> Tuple[Optional[int], Optional[str]]:
    """显示代码页选择对话框（便捷函数）
    
    Args:
        config_path: 可选的配置文件路径
        
    Returns:
        (代码页ID, 7-zip格式的代码页参数)
    """
    selector = CodePageSelector(config_path)
    return selector.show_dialog()


if __name__ == "__main__":
    # 测试代码
    codepage_id, mcp_param = show_codepage_dialog()
    print(f"选择的代码页: {codepage_id}")
    print(f"7-zip参数: {mcp_param}") 