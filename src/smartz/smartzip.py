"""
SmartZip核心模块
处理压缩和解压的主要逻辑
"""
import os
import sys
import shutil
import subprocess
import tempfile
import time
import re
from pathlib import Path
from typing import List, Dict, Optional, Callable, Tuple
import pyperclip

from config import ConfigManager

try:
    import send2trash
except ImportError:
    send2trash = None


class SmartZip:
    """SmartZip主类"""
    
    def __init__(self, config_manager: Optional[ConfigManager] = None):
        """初始化SmartZip
        
        Args:
            config_manager: 配置管理器实例
        """
        self.config = config_manager or ConfigManager()
        self.now = time.time()
        self.exit_code = -1
        self.set_show = False
        self.is_running = False
        self.multi = False
        self.continue_flag = False
        self.gui_show = False
        self.cmd_hide = False
        self.pid = None
        self.log = ""
        self.test_log = ""
        self.temp_dir = ""
        self.current_size = 0
        self.index = 0        
        self.default_dir = ""
        self.error = False
        self.need_pass = 0
        self.try_password = ""
          # 验证7-zip安装
        zip_dir = self.config.zip_dir
        if not os.path.exists(zip_dir):
            raise Exception(f"7-zip 文件夹不存在: {zip_dir}")
            
        self.seven_z = os.path.join(zip_dir, "7z.exe")
        self.seven_z_g = os.path.join(zip_dir, "7zG.exe") 
        self.seven_z_fm = os.path.join(zip_dir, "7zFM.exe")
        
        # 验证7-zip可执行文件
        for exe in [self.seven_z, self.seven_z_g, self.seven_z_fm]:
            if not os.path.exists(exe):
                raise Exception(f"7-zip文件不存在: {exe}")
        
        # 初始化扩展名映射
        self.ext_map = {}
        self.ext_exp = []
        self.config.read_loop("ext", [], True)  # 填充ext_map
        self.config.read_loop("extExp", self.ext_exp)
        
        # 初始化密码列表
        self.passwords = ["", self.config.last_pass, self._format_password(self._get_clipboard())]
        password_list = []
        self.config.read_loop("password", password_list)
        self.passwords.extend(password_list)
        
        # 初始化排除参数
        self.exclude_args = self._build_exclude_args()
    def _get_clipboard(self) -> str:
        """获取剪贴板内容"""
        try:
            return pyperclip.paste()
        except:
            return ""
    
    def _format_password(self, password: str) -> str:
        """格式化密码，移除首尾空格和换行符"""
        if len(password) < 100:
            return re.sub(r'(\r\n|\r|\n)', '', password.strip())
        return ""
    
    def _build_exclude_args(self) -> str:
        """构建排除参数"""
        exclude_ext = []
        exclude_name = []
        self.config.read_loop("excludeExt", exclude_ext)
        self.config.read_loop("excludeName", exclude_name)
        
        args = ""
        for ext in exclude_ext:
            args += f' -x!*.{ext}'
        for name in exclude_name:
            args += f' -x!*{name}*'
        
        if args:
            args += " -r"
        
        return args
    
    def init(self, args: List[str]) -> 'SmartZip':
        """初始化处理参数
        
        Args:
            args: 命令行参数列表
            
        Returns:
            self
        """
        self.code_page = ""
        
        # 检查编码参数
        if args and args[0] == "xc":
            self._set_code_page()
            args = args[1:]
        
        # 确定操作类型
        if args and re.match(r'^[xoa]$', args[0]):
            self.operation = args[0]
            args = args[1:]
        else:
            self.operation = "x"  # 默认解压
        
        # 收集文件路径
        self.file_list = []
        for arg in args:
            if os.path.exists(arg):
                path = Path(arg).resolve()
                if path.is_file() or path.is_dir():
                    self.file_list.append(str(path))
        
        if not self.file_list:
            sys.exit(2)
        
        self.is_running = True
        self.multi = len(self.file_list) > 1
        
        # 设置工作目录
        if self.file_list:
            self.default_dir = str(Path(self.file_list[0]).parent)
            os.chdir(self.default_dir)
        
        return self
    
    def _set_code_page(self):
        """设置代码页（简化版，实际实现需要GUI）"""
        # 这里简化处理，实际应该弹出选择对话框
        self.code_page = " -mcp=936"  # 默认GBK
    
    def exec(self):
        """执行主要操作"""
        try:
            if self.operation == "x":
                self.unzip()
            elif self.operation == "o": 
                self.open_zip()
            elif self.operation == "a":
                self.create_zip()
            else:
                self.unzip()
        finally:
            self.is_running = False
            if self.cmd_hide and not self.gui_show:
                print("处理完成")
                time.sleep(2)
    
    def unzip(self, loop_path: str = ""):
        """智能解压功能
        
        Args:
            loop_path: 循环路径（用于嵌套解压）
        """
        if not loop_path:
            file_list = self.file_list
            # 设置解压相关配置
            self.auto_add_pass = self.config.auto_add_pass
            self.dynamic_pass_sort = self.config.dynamic_pass_sort
            self.test_mode = self.config.test
            self.part_skip = self.config.part_skip
            self.del_source = self.config.del_source
            self.del_when_has_pass = self.config.del_when_has_pass
            self.nesting = self.config.nesting
            self.success_percent = self.config.success_percent
            self.auto_remove_pass = self.config.auto_remove_pass
            
            # 设置目标目录
            target_dir = self.config.target_dir
            if target_dir and os.path.exists(target_dir):
                os.chdir(target_dir)
                self.default_dir = target_dir
        else:
            file_list = [loop_path]
            parent_dir = str(Path(loop_path).parent)
            os.chdir(parent_dir)
        
        for file_path in file_list:
            if not loop_path and os.getcwd() != self.default_dir:
                os.chdir(self.default_dir)
            
            if not loop_path:
                self.index = file_list.index(file_path) + 1
            
            # 创建临时目录
            self.temp_dir = f'__7z{int(time.time())}'
            
            self.current_size = os.path.getsize(file_path)
            hide_bool = self.current_size / (1024 * 1024) < self.config.hide_run_size
            
            # 检查是否为分卷压缩包
            is_part = self._is_part(file_path)
            if self.part_skip and not is_part:
                continue
            
            # 执行解压
            self._extract_archive(file_path, hide_bool, is_part, loop_path)
            
            # 处理解压后的文件
            if os.path.exists(self.temp_dir):
                self._process_extracted_files(self.temp_dir)
                
                # 清理临时目录
                try:
                    shutil.rmtree(self.temp_dir)
                except:
                    pass
    
    def _is_part(self, file_path: str) -> bool:
        """检查是否为分卷压缩包"""
        name = Path(file_path).name.lower()
        # 简化的分卷检测逻辑
        return bool(re.search(r'\.(part\d+|r\d+|z\d+)\.rar$', name) or 
                   re.search(r'\.7z\.\d+$', name))
    
    def _extract_archive(self, file_path: str, hide_bool: bool, is_part: bool, loop_path: str):
        """执行解压操作"""
        # 尝试使用密码解压
        password_found = False
        used_password = ""
        
        for password in self.passwords:
            if password is None:
                password = ""
            
            # 构建7z命令
            cmd_args = [
                self.seven_z, 'x', file_path,
                f'-o{self.temp_dir}',
                '-aou'  # 自动重命名
            ]
            
            if password:
                cmd_args.extend([f'-p{password}'])
            
            if self.exclude_args:
                cmd_args.extend(self.exclude_args.split())
            
            if self.code_page:
                cmd_args.append(self.code_page)
            
            # 执行命令
            try:
                result = subprocess.run(cmd_args, capture_output=True, text=True, timeout=300)
                if result.returncode == 0:
                    password_found = True
                    used_password = password
                    if password and password != self.config.last_pass:
                        self.config.last_pass = password
                    break
            except subprocess.TimeoutExpired:
                print(f"解压超时: {file_path}")
                continue
            except Exception as e:
                print(f"解压出错: {e}")
                continue
        
        # 如果所有密码都失败，尝试手动输入
        if not password_found and not os.path.exists(self.temp_dir):
            print(f"需要密码解压: {file_path}")
            manual_password = input("请输入密码: ")
            if manual_password:
                cmd_args = [
                    self.seven_z, 'x', file_path,
                    f'-o{self.temp_dir}',
                    '-aou',
                    f'-p{manual_password}'
                ]
                
                try:
                    result = subprocess.run(cmd_args, capture_output=True, text=True, timeout=300)
                    if result.returncode == 0:
                        password_found = True
                        used_password = manual_password
                        # 添加到密码列表
                        if self.auto_add_pass:
                            self.passwords.append(manual_password)
                            self.config.write(manual_password, str(len(self.passwords)), 'password')
                except Exception as e:
                    print(f"手动解压出错: {e}")
        
        # 解压成功后处理源文件
        if password_found and os.path.exists(self.temp_dir):
            if loop_path:
                self._recycle_item(file_path, True)
            elif self.del_source or (used_password and self.del_when_has_pass):
                self._recycle_item(file_path)
    
    def _process_extracted_files(self, temp_dir: str):
        """处理解压后的文件"""
        temp_path = Path(temp_dir)
        
        # 获取解压后的文件列表
        extracted_items = list(temp_path.iterdir())
        
        if not extracted_items:
            return
        
        # 如果只有一个文件/目录，直接移动到当前目录
        if len(extracted_items) == 1:
            item = extracted_items[0]
            target_path = Path.cwd() / item.name
            
            # 如果目标已存在，重命名
            counter = 1
            while target_path.exists():
                stem = item.stem
                suffix = item.suffix
                target_path = Path.cwd() / f"{stem}_{counter}{suffix}"
                counter += 1
            
            shutil.move(str(item), str(target_path))
        else:
            # 多个文件，移动到以压缩包命名的目录
            archive_name = Path(self.file_list[self.index - 1] if hasattr(self, 'index') else extracted_items[0]).stem
            target_dir = Path.cwd() / archive_name
            
            # 确保目标目录唯一
            counter = 1
            while target_dir.exists():
                target_dir = Path.cwd() / f"{archive_name}_{counter}"
                counter += 1
            
            target_dir.mkdir()
            
            # 移动所有文件
            for item in extracted_items:
                shutil.move(str(item), str(target_dir / item.name))
        
        # 处理重命名和删除规则
        self._apply_rename_delete_rules(Path.cwd())
        
        # 处理嵌套解压
        if self.nesting:
            self._process_nested_archives(Path.cwd())
    
    def _apply_rename_delete_rules(self, directory: Path):
        """应用重命名和删除规则"""
        # 重命名规则
        rename_ext = {}
        rename_name = {}
        rename_exp = {}
        
        self.config.read_loop("renameExt", [], True)  # 实际实现需要解析<--->格式
        self.config.read_loop("renameName", [], True)
        self.config.read_loop("renameExp", [], True)
        
        # 删除规则
        delete_ext = []
        delete_name = []
        delete_exp = []
        
        self.config.read_loop("deleteExt", delete_ext)
        self.config.read_loop("deleteName", delete_name)
        self.config.read_loop("deleteExp", delete_exp)
        
        # 递归处理所有文件
        for item in directory.rglob("*"):
            if item.is_file():
                # 应用删除规则
                should_delete = False
                
                # 按扩展名删除
                if item.suffix.lower().lstrip('.') in delete_ext:
                    should_delete = True
                
                # 按文件名包含删除
                for pattern in delete_name:
                    if pattern in item.name:
                        should_delete = True
                        break
                
                # 按正则表达式删除
                for pattern in delete_exp:
                    if re.search(pattern, item.name):
                        should_delete = True
                        break
                
                if should_delete:
                    self._recycle_item(str(item))
                    continue
                
                # 应用重命名规则（简化实现）
                new_name = item.name
                
                # 这里需要实现具体的重命名逻辑
                # 实际实现需要解析配置中的<--->分隔符格式
                
                if new_name != item.name:
                    new_path = item.parent / new_name
                    if not new_path.exists():
                        item.rename(new_path)
    
    def _process_nested_archives(self, directory: Path):
        """处理嵌套压缩包"""
        for item in directory.rglob("*"):
            if item.is_file() and self._is_archive(item):
                print(f"发现嵌套压缩包: {item}")
                self.unzip(str(item))
    
    def _is_archive(self, file_path: Path) -> bool:
        """检查文件是否为压缩包"""
        ext = file_path.suffix.lower().lstrip('.')
        
        # 检查已知扩展名
        known_extensions = []
        self.config.read_loop("ext", known_extensions)
        if ext in known_extensions:
            return True
        
        # 检查正则表达式
        for pattern in self.ext_exp:
            if re.match(pattern, ext):
                return True
        
        return False
    
    def _recycle_item(self, file_path: str, force: bool = False):
        """回收站删除文件"""
        try:
            if force or self.del_source:
                send2trash.send2trash(file_path)
                print(f"已删除: {file_path}")
        except Exception as e:
            print(f"删除失败: {file_path}, 错误: {e}")
    
    def open_zip(self):
        """打开压缩包或创建压缩包"""
        if len(self.file_list) == 1:
            file_path = self.file_list[0]
            path_obj = Path(file_path)
            
            if path_obj.is_file() and self._is_archive(path_obj):
                # 是压缩包，用7-zip打开
                subprocess.Popen([self.seven_z_fm, file_path])
                print(f"打开压缩包: {file_path}")
            else:
                # 不是压缩包，显示创建界面
                self._show_create_dialog(file_path)
        else:
            # 多文件，创建压缩包
            self.create_zip()
    
    def _show_create_dialog(self, file_path: str):
        """显示创建压缩包对话框（简化版）"""
        archive_name = Path(file_path).stem + ".zip"
        args = self.config.open_add
        
        cmd_args = [self.seven_z, 'a', archive_name] + args.split() + [file_path]
        
        try:
            result = subprocess.run(cmd_args, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"创建压缩包成功: {archive_name}")
            else:
                print(f"创建压缩包失败: {result.stderr}")
        except Exception as e:
            print(f"创建压缩包出错: {e}")
    
    def create_zip(self):
        """创建压缩包"""
        if not self.file_list:
            return
        
        # 统计目录数量
        dir_count = sum(1 for path in self.file_list if Path(path).is_dir())
        
        args = self.config.add
        ext = re.search(r'\.(\w+)"', args)
        extension = f".{ext.group(1)}" if ext else ".zip"
        
        if dir_count == len(self.file_list):
            # 全是目录，每个目录创建一个压缩包
            for dir_path in self.file_list:
                dir_obj = Path(dir_path)
                archive_name = dir_obj.name + extension
                
                cmd_args = [self.seven_z, 'a', archive_name] + args.split() + [f"{dir_path}\\*"]
                
                try:
                    result = subprocess.run(cmd_args, capture_output=True, text=True)
                    if result.returncode == 0:
                        print(f"创建压缩包成功: {archive_name}")
                    else:
                        print(f"创建压缩包失败: {result.stderr}")
                except Exception as e:
                    print(f"创建压缩包出错: {e}")
        
        elif len(self.file_list) == 1:
            # 单个文件
            file_obj = Path(self.file_list[0])
            archive_name = file_obj.stem + extension
            
            cmd_args = [self.seven_z, 'a', archive_name] + args.split() + [self.file_list[0]]
            
            try:
                result = subprocess.run(cmd_args, capture_output=True, text=True)
                if result.returncode == 0:
                    print(f"创建压缩包成功: {archive_name}")
                else:
                    print(f"创建压缩包失败: {result.stderr}")
            except Exception as e:
                print(f"创建压缩包出错: {e}")
        
        else:
            # 混合文件，创建单个压缩包
            current_dir = Path.cwd()
            archive_name = current_dir.name + extension
            
            cmd_args = [self.seven_z, 'a', archive_name] + args.split() + self.file_list
            
            try:
                result = subprocess.run(cmd_args, capture_output=True, text=True)
                if result.returncode == 0:
                    print(f"创建压缩包成功: {archive_name}")
                else:
                    print(f"创建压缩包失败: {result.stderr}")
            except Exception as e:
                print(f"创建压缩包出错: {e}")
    
    def _auto_unique_output(self, name: str, ext: str) -> str:
        """自动生成唯一的输出文件名"""
        base_name = name
        counter = 1
        
        while Path(f"{name}{ext}").exists():
            name = f"{base_name}_{counter}"
            counter += 1
        
        return name
