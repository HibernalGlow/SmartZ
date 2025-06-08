"""
配置管理模块
处理INI配置文件的读写操作
"""
import configparser
import os
from pathlib import Path
from typing import Dict, List, Any, Optional


class ConfigManager:
    """配置管理器"""
    def __init__(self, config_path: Optional[str] = None):
        """初始化配置管理器
        
        Args:
            config_path: 配置文件路径，如果为None则使用默认路径
        """
        if config_path is None:
            self.config_path = Path(__file__).parent / "SmartZip.ini"
        else:
            self.config_path = Path(config_path)
            
        # 禁用插值功能来避免%符号问题
        self.config = configparser.ConfigParser(interpolation=None)
        self.config.optionxform = str  # 保持键名大小写
        
        # 确保配置文件存在
        self._ensure_config_exists()
        self._load_config()
    
    def _ensure_config_exists(self):
        """确保配置文件存在，如果不存在则创建默认配置"""
        if not self.config_path.exists():
            self._create_default_config()
    
    def _create_default_config(self):
        """创建默认配置文件"""
        default_config = {
            'set': {
                '7zipDir': '%SmartZipDir%\\7-zip',
                'muiltNesting': '0',
                'partSkip': '1', 
                'test': '0',
                'autoAddPass': '0',
                'dynamicPassSort': '0',
                'autoRemovePass': '0',
                'targetDir': '',
                'delSource': '0',
                'delWhenHasPass': '0',
                'hideRunSize': '10',
                'successPercent': '10',
                'successMinSize': '10',
                'logLevel': '5',
                'cmdLog': '0',
                'icon': '%SmartZipDir%\\ico.ico',
                'addDir2Pass': '0'
            },
            'password': {
                '1': '123456',
                '2': 'password',
                '3': '000000'
            },
            'menu': {
                'openZipName': '用7-Zip打开',
                'unZipName': '智能解压',
                'addZipName': '压缩',
                'contextMenu': '1',
                'sendTo': '1'
            },
            '7z': {
                'openAdd': '.zip" -tzip -mx=0 -aou -ad',
                'add': '.zip" -tzip -mx=0 -aou -ad'
            },
            'ext': {
                '1': 'zip',
                '2': 'rar',
                '3': '7z',
                '4': 'tar',
                '5': 'gz',
                '6': 'bz2',
                '7': 'xz'
            },
            'extExp': {
                '1': r'^\d+$'
            },
            'extForOpen': {
                '1': 'iso'
            },
            'temp': {
                'version': '18',
                'lastPass': '',
                'guiShow': '',
                'isLoop': ''
            }
        }
        
        for section_name, section_data in default_config.items():
            self.config.add_section(section_name)
            for key, value in section_data.items():
                self.config.set(section_name, key, value)
        
        self._save_config()
    
    def _load_config(self):
        """加载配置文件"""
        self.config.read(self.config_path, encoding='utf-8')
    
    def _save_config(self):
        """保存配置文件"""
        with open(self.config_path, 'w', encoding='utf-8') as f:
            self.config.write(f)
    
    def read(self, key: str, default: Any = None, section: str = 'set') -> str:
        """读取配置值
        
        Args:
            key: 配置键
            default: 默认值
            section: 配置节
            
        Returns:
            配置值
        """
        try:
            return self.config.get(section, key)
        except (configparser.NoSectionError, configparser.NoOptionError):
            return default if default is not None else ''
    
    def write(self, value: str, key: str, section: str = 'set'):
        """写入配置值
        
        Args:
            value: 配置值
            key: 配置键  
            section: 配置节
        """
        if not self.config.has_section(section):
            self.config.add_section(section)
        
        self.config.set(section, key, str(value))
        self._save_config()
    
    def read_loop(self, section: str, target_list: List[str], as_dict: bool = False) -> None:
        """循环读取配置节中的所有值
        
        Args:
            section: 配置节名
            target_list: 目标列表或字典
            as_dict: 是否作为字典返回
        """
        if not self.config.has_section(section):
            return
            
        items = self.config.items(section)
        if as_dict and hasattr(target_list, 'update'):
            # 如果target_list是字典类型
            for key, value in items:
                target_list[value] = key
        else:
            # 如果target_list是列表类型
            target_list.extend([value for key, value in items])
    
    def delete(self, section: str, key: str):
        """删除配置项
        
        Args:
            section: 配置节
            key: 配置键
        """
        if self.config.has_section(section):
            self.config.remove_option(section, key)
            self._save_config()
    
    def get_script_dir(self) -> str:
        """获取脚本目录"""
        return str(Path(__file__).parent.absolute())
    
    def resolve_path(self, path: str) -> str:
        """解析路径，替换%SmartZipDir%占位符
        
        Args:
            path: 原始路径
            
        Returns:
            解析后的路径
        """
        if '%SmartZipDir%' in path:
            script_dir = self.get_script_dir()
            return path.replace('%SmartZipDir%', script_dir)
        return path
    
    # 属性访问器，方便访问常用配置
    @property
    def zip_dir(self) -> str:
        """7-zip目录"""
        return self.resolve_path(self.read('7zipDir'))
    
    @property
    def last_pass(self) -> str:
        """最后使用的密码"""
        return self.read('lastPass', '', 'temp')
    
    @last_pass.setter
    def last_pass(self, value: str):
        """设置最后使用的密码"""
        self.write(value, 'lastPass', 'temp')
    
    @property
    def auto_add_pass(self) -> bool:
        """自动添加密码"""
        return self.read('autoAddPass') == '1'
    
    @property
    def dynamic_pass_sort(self) -> bool:
        """动态密码排序"""
        return self.read('dynamicPassSort') == '1'
    
    @property
    def test(self) -> bool:
        """测试模式"""
        return self.read('test') == '1'
    
    @property
    def part_skip(self) -> bool:
        """跳过分卷压缩包"""
        return self.read('partSkip') == '1'
    
    @property
    def del_source(self) -> bool:
        """删除源文件"""
        return self.read('delSource') == '1'
    
    @property
    def del_when_has_pass(self) -> bool:
        """有密码时删除源文件"""
        return self.read('delWhenHasPass') == '1'
    
    @property
    def nesting(self) -> bool:
        """嵌套解压"""
        return self.read('muiltNesting') == '1'
    
    @property
    def success_percent(self) -> int:
        """成功百分比"""
        return int(self.read('successPercent', '10'))
    
    @property
    def auto_remove_pass(self) -> int:
        """自动移除密码"""
        return int(self.read('autoRemovePass', '0'))
    
    @property
    def target_dir(self) -> str:
        """目标目录"""
        return self.read('targetDir')
    
    @property
    def log_level(self) -> int:
        """日志级别"""
        return int(self.read('logLevel', '5'))
    
    @property
    def cmd_log(self) -> bool:
        """命令日志"""
        return self.read('cmdLog') == '1'
    
    @property
    def hide_run_size(self) -> int:
        """隐藏运行大小(MB)"""
        return int(self.read('hideRunSize', '10'))
    
    @property
    def icon(self) -> str:
        """图标路径"""
        return self.resolve_path(self.read('icon'))
    
    @property
    def open_add(self) -> str:
        """打开添加参数"""
        return self.read('openAdd', '.zip" -tzip -mx=0 -aou -ad', '7z')
    
    @property
    def add(self) -> str:
        """添加参数"""
        return self.read('add', '.zip" -tzip -mx=0 -aou -ad', '7z')
