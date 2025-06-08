"""
Windows右键菜单注册模块
处理Windows注册表操作来注册右键菜单
"""
import winreg
import os
import sys
from pathlib import Path
from typing import Optional

from config import ConfigManager


class ContextMenuManager:
    """右键菜单管理器"""
    
    def __init__(self, config_manager: ConfigManager):
        """初始化右键菜单管理器
        
        Args:
            config_manager: 配置管理器
        """
        self.config = config_manager
        self.exe_path = sys.executable if getattr(sys, 'frozen', False) else os.path.abspath(__file__)
        self.script_dir = Path(__file__).parent.absolute()
    
    def register_context_menu(self) -> bool:
        """注册右键菜单
        
        Returns:
            是否注册成功
        """
        try:
            # 检查是否启用右键菜单
            if not (self.config.read('contextMenu', '1', 'menu') == '1'):
                return True
            
            # 获取菜单名称
            unzip_name = self.config.read('unZipName', '智能解压', 'menu')
            open_name = self.config.read('openZipName', '用7-Zip打开', 'menu')
            add_name = self.config.read('addZipName', '压缩', 'menu')
            
            # 获取图标路径
            icon_path = self.config.icon
            if not os.path.exists(icon_path):
                icon_path = ""
            
            # 注册文件右键菜单
            self._register_file_menu(unzip_name, open_name, add_name, icon_path)
            
            # 注册文件夹右键菜单
            self._register_folder_menu(add_name, icon_path)
            
            # 注册发送到菜单
            if self.config.read('sendTo', '1', 'menu') == '1':
                self._register_send_to_menu(unzip_name, open_name, add_name, icon_path)
            
            return True
            
        except Exception as e:
            print(f"注册右键菜单失败: {e}")
            return False
    
    def unregister_context_menu(self) -> bool:
        """卸载右键菜单
        
        Returns:
            是否卸载成功
        """
        try:
            # 删除文件右键菜单
            self._delete_registry_key(winreg.HKEY_CLASSES_ROOT, r"*\\shell\\SmartZipUnzip")
            self._delete_registry_key(winreg.HKEY_CLASSES_ROOT, r"*\\shell\\SmartZipOpen")
            self._delete_registry_key(winreg.HKEY_CLASSES_ROOT, r"*\\shell\\SmartZipAdd")
            
            # 删除文件夹右键菜单
            self._delete_registry_key(winreg.HKEY_CLASSES_ROOT, r"Directory\\shell\\SmartZipAdd")
            
            # 删除发送到菜单
            self._unregister_send_to_menu()
            
            return True
            
        except Exception as e:
            print(f"卸载右键菜单失败: {e}")
            return False
    
    def _register_file_menu(self, unzip_name: str, open_name: str, add_name: str, icon_path: str):
        """注册文件右键菜单"""
        # 智能解压菜单
        key_path = r"*\\shell\\SmartZipUnzip"
        with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, key_path) as key:
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, unzip_name)
            if icon_path:
                winreg.SetValueEx(key, "Icon", 0, winreg.REG_SZ, icon_path)
        
        command_path = key_path + "\\\\command"
        with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, command_path) as key:
            command = f'"{self.exe_path}" x "%1"'
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, command)
        
        # 打开压缩包菜单
        key_path = r"*\\shell\\SmartZipOpen"
        with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, key_path) as key:
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, open_name)
            if icon_path:
                winreg.SetValueEx(key, "Icon", 0, winreg.REG_SZ, icon_path)
        
        command_path = key_path + "\\\\command"
        with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, command_path) as key:
            command = f'"{self.exe_path}" o "%1"'
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, command)
        
        # 压缩菜单
        key_path = r"*\\shell\\SmartZipAdd"
        with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, key_path) as key:
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, add_name)
            if icon_path:
                winreg.SetValueEx(key, "Icon", 0, winreg.REG_SZ, icon_path)
        
        command_path = key_path + "\\\\command"
        with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, command_path) as key:
            command = f'"{self.exe_path}" a "%1"'
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, command)
    
    def _register_folder_menu(self, add_name: str, icon_path: str):
        """注册文件夹右键菜单"""
        # 文件夹压缩菜单
        key_path = r"Directory\\shell\\SmartZipAdd"
        with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, key_path) as key:
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, add_name)
            if icon_path:
                winreg.SetValueEx(key, "Icon", 0, winreg.REG_SZ, icon_path)
        
        command_path = key_path + "\\\\command"
        with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, command_path) as key:
            command = f'"{self.exe_path}" a "%1"'
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, command)
    
    def _register_send_to_menu(self, unzip_name: str, open_name: str, add_name: str, icon_path: str):
        """注册发送到菜单"""
        try:
            # 获取发送到目录
            send_to_dir = Path(os.environ['APPDATA']) / "Microsoft" / "Windows" / "SendTo"
            
            if not send_to_dir.exists():
                return
            
            # 创建智能解压快捷方式
            unzip_link = send_to_dir / f"{unzip_name}.lnk"
            self._create_shortcut(str(unzip_link), self.exe_path, "x", icon_path)
            
            # 创建打开快捷方式
            open_link = send_to_dir / f"{open_name}.lnk"
            self._create_shortcut(str(open_link), self.exe_path, "o", icon_path)
            
            # 创建压缩快捷方式
            add_link = send_to_dir / f"{add_name}.lnk"
            self._create_shortcut(str(add_link), self.exe_path, "a", icon_path)
            
        except Exception as e:
            print(f"注册发送到菜单失败: {e}")
    
    def _unregister_send_to_menu(self):
        """卸载发送到菜单"""
        try:
            send_to_dir = Path(os.environ['APPDATA']) / "Microsoft" / "Windows" / "SendTo"
            
            if not send_to_dir.exists():
                return
            
            # 删除SmartZip相关的快捷方式
            for file in send_to_dir.glob("*.lnk"):
                try:
                    # 这里需要检查快捷方式的目标是否为SmartZip
                    # 简化处理，按名称删除
                    if any(name in file.name for name in ["智能解压", "7-Zip", "压缩", "SmartZip"]):
                        file.unlink()
                except:
                    pass
                    
        except Exception as e:
            print(f"卸载发送到菜单失败: {e}")
    
    def _create_shortcut(self, link_path: str, target: str, args: str, icon_path: str):
        """创建快捷方式"""
        try:
            import win32com.client
            
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(link_path)
            shortcut.TargetPath = target
            shortcut.Arguments = args
            if icon_path and os.path.exists(icon_path):
                shortcut.IconLocation = icon_path
            shortcut.save()
            
        except ImportError:
            # 如果没有win32com，使用替代方法
            print("需要安装pywin32来创建快捷方式: pip install pywin32")
        except Exception as e:
            print(f"创建快捷方式失败: {e}")
    
    def _delete_registry_key(self, root_key, sub_key: str):
        """删除注册表项"""
        try:
            winreg.DeleteKeyEx(root_key, sub_key)
        except FileNotFoundError:
            # 键不存在，忽略
            pass
        except Exception as e:
            print(f"删除注册表项失败 {sub_key}: {e}")
    
    def is_admin(self) -> bool:
        """检查是否具有管理员权限"""
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False
    
    def run_as_admin(self, args: Optional[str] = None):
        """以管理员权限运行"""
        try:
            import ctypes
            
            if args is None:
                args = " ".join(sys.argv)
            
            ctypes.windll.shell32.ShellExecuteW(
                None, 
                "runas", 
                sys.executable, 
                args, 
                None, 
                1
            )
        except Exception as e:
            print(f"以管理员权限运行失败: {e}")


def register_menu():
    """注册右键菜单的便捷函数"""
    config = ConfigManager()
    menu_manager = ContextMenuManager(config)
    
    if not menu_manager.is_admin():
        print("需要管理员权限来注册右键菜单")
        menu_manager.run_as_admin("--register-menu")
        return
    
    success = menu_manager.register_context_menu()
    if success:
        print("右键菜单注册成功")
    else:
        print("右键菜单注册失败")


def unregister_menu():
    """卸载右键菜单的便捷函数"""
    config = ConfigManager()
    menu_manager = ContextMenuManager(config)
    
    if not menu_manager.is_admin():
        print("需要管理员权限来卸载右键菜单")
        menu_manager.run_as_admin("--unregister-menu")
        return
    
    success = menu_manager.unregister_context_menu()
    if success:
        print("右键菜单卸载成功")
    else:
        print("右键菜单卸载失败")
