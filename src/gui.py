"""
GUI设置界面模块
使用tkinter创建设置界面
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
from pathlib import Path
from typing import Dict, List

from config import ConfigManager


class SettingsGUI:
    """设置界面GUI"""
    
    def __init__(self, config_manager: ConfigManager):
        """初始化设置界面
        
        Args:
            config_manager: 配置管理器
        """
        self.config = config_manager
        self.root = tk.Tk()
        self.root.title("SmartZip 设置")
        self.root.geometry("600x700")
        self.root.resizable(True, True)
        
        # 设置界面样式
        style = ttk.Style()
        style.theme_use('vista' if 'vista' in style.theme_names() else 'default')
        
        self._create_widgets()
        self._load_settings()
    
    def _create_widgets(self):
        """创建界面组件"""
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        
        # 创建标签页
        notebook = ttk.Notebook(main_frame)
        notebook.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        main_frame.rowconfigure(0, weight=1)
        
        # 基本设置标签页
        self._create_basic_tab(notebook)
        
        # 密码设置标签页
        self._create_password_tab(notebook)
        
        # 右键菜单标签页
        self._create_menu_tab(notebook)
        
        # 高级设置标签页
        self._create_advanced_tab(notebook)
        
        # 按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # 按钮
        ttk.Button(button_frame, text="保存设置", command=self._save_settings).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="重置默认", command=self._reset_defaults).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="关闭", command=self.root.destroy).pack(side=tk.RIGHT)
    
    def _create_basic_tab(self, notebook):
        """创建基本设置标签页"""
        frame = ttk.Frame(notebook, padding="10")
        notebook.add(frame, text="基本设置")
        
        row = 0
        
        # 7-zip路径设置
        ttk.Label(frame, text="7-zip安装路径:").grid(row=row, column=0, sticky=tk.W, pady=(0, 5))
        path_frame = ttk.Frame(frame)
        path_frame.grid(row=row+1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        frame.columnconfigure(0, weight=1)
        path_frame.columnconfigure(0, weight=1)
        
        self.zip_dir_var = tk.StringVar()
        ttk.Entry(path_frame, textvariable=self.zip_dir_var).grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        ttk.Button(path_frame, text="浏览", command=self._browse_zip_dir).grid(row=0, column=1)
        
        row += 2
        
        # 目标目录设置
        ttk.Label(frame, text="解压目标目录 (留空为源文件目录):").grid(row=row, column=0, sticky=tk.W, pady=(0, 5))
        target_frame = ttk.Frame(frame)
        target_frame.grid(row=row+1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        target_frame.columnconfigure(0, weight=1)
        
        self.target_dir_var = tk.StringVar()
        ttk.Entry(target_frame, textvariable=self.target_dir_var).grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        ttk.Button(target_frame, text="浏览", command=self._browse_target_dir).grid(row=0, column=1)
        
        row += 2
        
        # 复选框选项
        checkboxes = [
            ("del_source", "解压成功后删除源文件"),
            ("del_when_has_pass", "有密码的压缩包解压成功后删除源文件"),
            ("part_skip", "跳过分卷压缩包的非第一卷"),
            ("nesting", "启用嵌套解压"),
            ("auto_add_pass", "自动添加使用过的密码"),
            ("dynamic_pass_sort", "密码动态排序(使用频繁的排在前面)"),
            ("test", "启用测试功能"),
            ("cmd_log", "启用命令日志")
        ]
        
        self.checkbox_vars = {}
        for var_name, text in checkboxes:
            self.checkbox_vars[var_name] = tk.BooleanVar()
            ttk.Checkbutton(frame, text=text, variable=self.checkbox_vars[var_name]).grid(
                row=row, column=0, sticky=tk.W, pady=2)
            row += 1
        
        row += 1
        
        # 数值设置
        ttk.Label(frame, text="隐藏界面运行的文件大小阈值 (MB):").grid(row=row, column=0, sticky=tk.W, pady=(0, 5))
        self.hide_run_size_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.hide_run_size_var, width=10).grid(row=row+1, column=0, sticky=tk.W, pady=(0, 10))
        
        row += 2
        
        ttk.Label(frame, text="成功判断百分比:").grid(row=row, column=0, sticky=tk.W, pady=(0, 5))
        self.success_percent_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.success_percent_var, width=10).grid(row=row+1, column=0, sticky=tk.W, pady=(0, 10))
        
        row += 2
        
        ttk.Label(frame, text="自动移除密码阈值 (0=禁用):").grid(row=row, column=0, sticky=tk.W, pady=(0, 5))
        self.auto_remove_pass_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.auto_remove_pass_var, width=10).grid(row=row+1, column=0, sticky=tk.W)
    
    def _create_password_tab(self, notebook):
        """创建密码设置标签页"""
        frame = ttk.Frame(notebook, padding="10")
        notebook.add(frame, text="密码设置")
        
        # 说明标签
        ttk.Label(frame, text="密码列表 (按优先级排序，常用密码放在前面):").grid(
            row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        
        # 密码列表框架
        list_frame = ttk.Frame(frame)
        list_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        # 密码列表
        self.password_listbox = tk.Listbox(list_frame, height=15)
        self.password_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.password_listbox.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.password_listbox.configure(yscrollcommand=scrollbar.set)
        
        # 按钮框架
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # 输入框架
        input_frame = ttk.Frame(button_frame)
        input_frame.pack(fill=tk.X, pady=(0, 5))
        input_frame.columnconfigure(0, weight=1)
        
        self.password_entry = ttk.Entry(input_frame)
        self.password_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        self.password_entry.bind('<Return>', lambda e: self._add_password())
        
        ttk.Button(input_frame, text="添加", command=self._add_password).grid(row=0, column=1)
        
        # 操作按钮
        btn_frame = ttk.Frame(button_frame)
        btn_frame.pack(fill=tk.X)
        
        ttk.Button(btn_frame, text="删除选中", command=self._remove_password).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="上移", command=self._move_password_up).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="下移", command=self._move_password_down).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="清空所有", command=self._clear_passwords).pack(side=tk.RIGHT)
    
    def _create_menu_tab(self, notebook):
        """创建右键菜单标签页"""
        frame = ttk.Frame(notebook, padding="10")
        notebook.add(frame, text="右键菜单")
        
        row = 0
        
        # 菜单启用选项
        ttk.Label(frame, text="右键菜单选项:").grid(row=row, column=0, sticky=tk.W, pady=(0, 10))
        row += 1
        
        menu_options = [
            ("context_menu", "启用右键菜单"),
            ("send_to", "启用发送到菜单")
        ]
        
        self.menu_vars = {}
        for var_name, text in menu_options:
            self.menu_vars[var_name] = tk.BooleanVar()
            ttk.Checkbutton(frame, text=text, variable=self.menu_vars[var_name]).grid(
                row=row, column=0, sticky=tk.W, pady=2)
            row += 1
        
        row += 1
        
        # 菜单名称设置
        ttk.Label(frame, text="菜单名称设置:").grid(row=row, column=0, sticky=tk.W, pady=(10, 5))
        row += 1
        
        menu_names = [
            ("open_zip_name", "打开压缩包菜单名称:"),
            ("unzip_name", "智能解压菜单名称:"),
            ("add_zip_name", "压缩菜单名称:")
        ]
        
        self.menu_name_vars = {}
        for var_name, label_text in menu_names:
            ttk.Label(frame, text=label_text).grid(row=row, column=0, sticky=tk.W, pady=(0, 5))
            self.menu_name_vars[var_name] = tk.StringVar()
            ttk.Entry(frame, textvariable=self.menu_name_vars[var_name], width=30).grid(
                row=row+1, column=0, sticky=tk.W, pady=(0, 10))
            row += 2
        
        # 注册按钮
        ttk.Button(frame, text="注册右键菜单", command=self._register_context_menu).grid(
            row=row, column=0, sticky=tk.W, pady=(10, 5))
        ttk.Button(frame, text="卸载右键菜单", command=self._unregister_context_menu).grid(
            row=row+1, column=0, sticky=tk.W)
    
    def _create_advanced_tab(self, notebook):
        """创建高级设置标签页"""
        frame = ttk.Frame(notebook, padding="10")
        notebook.add(frame, text="高级设置")
        
        row = 0
        
        # 压缩参数设置
        ttk.Label(frame, text="压缩参数设置:").grid(row=row, column=0, sticky=tk.W, pady=(0, 10))
        row += 1
        
        ttk.Label(frame, text="普通压缩参数:").grid(row=row, column=0, sticky=tk.W, pady=(0, 5))
        self.add_args_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.add_args_var, width=50).grid(row=row+1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        frame.columnconfigure(0, weight=1)
        row += 2
        
        ttk.Label(frame, text="打开时压缩参数:").grid(row=row, column=0, sticky=tk.W, pady=(0, 5))
        self.open_add_args_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.open_add_args_var, width=50).grid(row=row+1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        row += 2
        
        # 图标设置
        ttk.Label(frame, text="图标文件路径:").grid(row=row, column=0, sticky=tk.W, pady=(0, 5))
        icon_frame = ttk.Frame(frame)
        icon_frame.grid(row=row+1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        icon_frame.columnconfigure(0, weight=1)
        
        self.icon_var = tk.StringVar()
        ttk.Entry(icon_frame, textvariable=self.icon_var).grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        ttk.Button(icon_frame, text="浏览", command=self._browse_icon).grid(row=0, column=1)
        
        row += 2
        
        # 日志级别设置
        ttk.Label(frame, text="日志级别 (0-5):").grid(row=row, column=0, sticky=tk.W, pady=(0, 5))
        self.log_level_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.log_level_var, width=10).grid(row=row+1, column=0, sticky=tk.W)
    
    def _browse_zip_dir(self):
        """浏览7-zip目录"""
        directory = filedialog.askdirectory(title="选择7-zip安装目录")
        if directory:
            self.zip_dir_var.set(directory)
    
    def _browse_target_dir(self):
        """浏览目标目录"""
        directory = filedialog.askdirectory(title="选择解压目标目录")
        if directory:
            self.target_dir_var.set(directory)
    
    def _browse_icon(self):
        """浏览图标文件"""
        file_path = filedialog.askopenfilename(
            title="选择图标文件",
            filetypes=[("图标文件", "*.ico *.png *.jpg *.bmp"), ("所有文件", "*.*")]
        )
        if file_path:
            self.icon_var.set(file_path)
    
    def _add_password(self):
        """添加密码"""
        password = self.password_entry.get().strip()
        if password and password not in self.password_listbox.get(0, tk.END):
            self.password_listbox.insert(tk.END, password)
            self.password_entry.delete(0, tk.END)
    
    def _remove_password(self):
        """删除选中的密码"""
        selection = self.password_listbox.curselection()
        if selection:
            self.password_listbox.delete(selection[0])
    
    def _move_password_up(self):
        """上移密码"""
        selection = self.password_listbox.curselection()
        if selection and selection[0] > 0:
            index = selection[0]
            password = self.password_listbox.get(index)
            self.password_listbox.delete(index)
            self.password_listbox.insert(index - 1, password)
            self.password_listbox.selection_set(index - 1)
    
    def _move_password_down(self):
        """下移密码"""
        selection = self.password_listbox.curselection()
        if selection and selection[0] < self.password_listbox.size() - 1:
            index = selection[0]
            password = self.password_listbox.get(index)
            self.password_listbox.delete(index)
            self.password_listbox.insert(index + 1, password)
            self.password_listbox.selection_set(index + 1)
    
    def _clear_passwords(self):
        """清空所有密码"""
        if messagebox.askyesno("确认", "确定要清空所有密码吗？"):
            self.password_listbox.delete(0, tk.END)
    
    def _register_context_menu(self):
        """注册右键菜单"""
        try:
            # 这里应该实现Windows注册表操作
            # 简化版本只显示消息
            messagebox.showinfo("提示", "右键菜单注册功能需要管理员权限\n请以管理员身份运行程序")
        except Exception as e:
            messagebox.showerror("错误", f"注册右键菜单失败: {e}")
    
    def _unregister_context_menu(self):
        """卸载右键菜单"""
        try:
            # 这里应该实现Windows注册表操作
            # 简化版本只显示消息
            messagebox.showinfo("提示", "右键菜单卸载功能需要管理员权限\n请以管理员身份运行程序")
        except Exception as e:
            messagebox.showerror("错误", f"卸载右键菜单失败: {e}")
    
    def _load_settings(self):
        """加载设置到界面"""
        # 基本设置
        self.zip_dir_var.set(self.config.zip_dir)
        self.target_dir_var.set(self.config.target_dir)
        self.hide_run_size_var.set(str(self.config.hide_run_size))
        self.success_percent_var.set(str(self.config.success_percent))
        self.auto_remove_pass_var.set(str(self.config.auto_remove_pass))
        
        # 复选框
        checkbox_mappings = {
            'del_source': self.config.del_source,
            'del_when_has_pass': self.config.del_when_has_pass,
            'part_skip': self.config.part_skip,
            'nesting': self.config.nesting,
            'auto_add_pass': self.config.auto_add_pass,
            'dynamic_pass_sort': self.config.dynamic_pass_sort,
            'test': self.config.test,
            'cmd_log': self.config.cmd_log
        }
        
        for var_name, value in checkbox_mappings.items():
            if var_name in self.checkbox_vars:
                self.checkbox_vars[var_name].set(value)
        
        # 菜单设置
        self.menu_vars['context_menu'].set(self.config.read('contextMenu', '1', 'menu') == '1')
        self.menu_vars['send_to'].set(self.config.read('sendTo', '1', 'menu') == '1')
        
        self.menu_name_vars['open_zip_name'].set(self.config.read('openZipName', '用7-Zip打开', 'menu'))
        self.menu_name_vars['unzip_name'].set(self.config.read('unZipName', '智能解压', 'menu'))
        self.menu_name_vars['add_zip_name'].set(self.config.read('addZipName', '压缩', 'menu'))
        
        # 高级设置
        self.add_args_var.set(self.config.add)
        self.open_add_args_var.set(self.config.open_add)
        self.icon_var.set(self.config.icon)
        self.log_level_var.set(str(self.config.log_level))
        
        # 密码列表
        password_list = []
        self.config.read_loop("password", password_list)
        for password in password_list:
            self.password_listbox.insert(tk.END, password)
    
    def _save_settings(self):
        """保存设置"""
        try:
            # 保存基本设置
            self.config.write(self.zip_dir_var.get(), '7zipDir')
            self.config.write(self.target_dir_var.get(), 'targetDir')
            self.config.write(self.hide_run_size_var.get(), 'hideRunSize')
            self.config.write(self.success_percent_var.get(), 'successPercent')
            self.config.write(self.auto_remove_pass_var.get(), 'autoRemovePass')
            
            # 保存复选框设置
            checkbox_mappings = {
                'del_source': 'delSource',
                'del_when_has_pass': 'delWhenHasPass',
                'part_skip': 'partSkip',
                'nesting': 'muiltNesting',
                'auto_add_pass': 'autoAddPass',
                'dynamic_pass_sort': 'dynamicPassSort',
                'test': 'test',
                'cmd_log': 'cmdLog'
            }
            
            for var_name, config_key in checkbox_mappings.items():
                if var_name in self.checkbox_vars:
                    value = '1' if self.checkbox_vars[var_name].get() else '0'
                    self.config.write(value, config_key)
            
            # 保存菜单设置
            self.config.write('1' if self.menu_vars['context_menu'].get() else '0', 'contextMenu', 'menu')
            self.config.write('1' if self.menu_vars['send_to'].get() else '0', 'sendTo', 'menu')
            
            self.config.write(self.menu_name_vars['open_zip_name'].get(), 'openZipName', 'menu')
            self.config.write(self.menu_name_vars['unzip_name'].get(), 'unZipName', 'menu')
            self.config.write(self.menu_name_vars['add_zip_name'].get(), 'addZipName', 'menu')
            
            # 保存高级设置
            self.config.write(self.add_args_var.get(), 'add', '7z')
            self.config.write(self.open_add_args_var.get(), 'openAdd', '7z')
            self.config.write(self.icon_var.get(), 'icon')
            self.config.write(self.log_level_var.get(), 'logLevel')
            
            # 保存密码列表
            # 先清空现有密码
            for i in range(1, 100):  # 假设最多100个密码
                self.config.delete('password', str(i))
            
            # 保存新密码列表
            passwords = self.password_listbox.get(0, tk.END)
            for i, password in enumerate(passwords, 1):
                self.config.write(password, str(i), 'password')
            
            messagebox.showinfo("成功", "设置已保存")
            
        except Exception as e:
            messagebox.showerror("错误", f"保存设置失败: {e}")
    
    def _reset_defaults(self):
        """重置为默认设置"""
        if messagebox.askyesno("确认", "确定要重置为默认设置吗？所有当前设置将丢失。"):
            # 删除配置文件，重新创建
            if self.config.config_path.exists():
                self.config.config_path.unlink()
            
            # 重新初始化配置
            self.config._ensure_config_exists()
            self.config._load_config()
            
            # 重新加载界面
            self._load_settings()
            
            messagebox.showinfo("完成", "已重置为默认设置")
    
    def show(self):
        """显示设置界面"""
        self.root.mainloop()


def show_settings():
    """显示设置界面的便捷函数"""
    config = ConfigManager()
    gui = SettingsGUI(config)
    gui.show()
