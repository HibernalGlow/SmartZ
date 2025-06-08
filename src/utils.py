"""
实用工具模块
提供各种辅助功能
"""
import os
import re
import shutil
import tempfile
from pathlib import Path
from typing import List, Dict, Optional, Tuple


def format_password(password: str) -> str:
    """格式化密码，移除首尾空格和换行符
    
    Args:
        password: 原始密码
        
    Returns:
        格式化后的密码
    """
    if len(password) < 100:
        return re.sub(r'(\r\n|\r|\n)', '', password.strip())
    return ""


def is_archive_by_extension(file_path: str, extensions: List[str]) -> bool:
    """根据扩展名判断是否为压缩包
    
    Args:
        file_path: 文件路径
        extensions: 压缩包扩展名列表
        
    Returns:
        是否为压缩包
    """
    ext = Path(file_path).suffix.lower().lstrip('.')
    return ext in extensions


def is_archive_by_pattern(file_path: str, patterns: List[str]) -> bool:
    """根据正则表达式判断是否为压缩包
    
    Args:
        file_path: 文件路径  
        patterns: 正则表达式模式列表
        
    Returns:
        是否为压缩包
    """
    ext = Path(file_path).suffix.lower().lstrip('.')
    for pattern in patterns:
        try:
            if re.match(pattern, ext):
                return True
        except re.error:
            continue
    return False


def is_part_archive(file_path: str) -> bool:
    """检查是否为分卷压缩包
    
    Args:
        file_path: 文件路径
        
    Returns:
        是否为分卷压缩包
    """
    name = Path(file_path).name.lower()
    
    # RAR分卷: .part1.rar, .part2.rar, .r01, .r02等
    if re.search(r'\.(part\d+|r\d+)\.rar$', name):
        return True
    
    # 7z分卷: .7z.001, .7z.002等
    if re.search(r'\.7z\.\d+$', name):
        return True
    
    # ZIP分卷: .z01, .z02等
    if re.search(r'\.z\d+$', name):
        return True
    
    return False


def get_unique_path(base_path: str) -> str:
    """获取唯一的文件/目录路径
    
    Args:
        base_path: 基础路径
        
    Returns:
        唯一路径
    """
    path = Path(base_path)
    if not path.exists():
        return str(path)
    
    counter = 1
    stem = path.stem
    suffix = path.suffix
    parent = path.parent
    
    while True:
        if suffix:
            # 文件
            new_name = f"{stem}_{counter}{suffix}"
        else:
            # 目录
            new_name = f"{stem}_{counter}"
        
        new_path = parent / new_name
        if not new_path.exists():
            return str(new_path)
        
        counter += 1


def get_temp_dir(prefix: str = "smartzip_") -> str:
    """获取临时目录
    
    Args:
        prefix: 目录前缀
        
    Returns:
        临时目录路径
    """
    return tempfile.mkdtemp(prefix=prefix)


def safe_remove(path: str) -> bool:
    """安全删除文件或目录
    
    Args:
        path: 文件或目录路径
        
    Returns:
        是否删除成功
    """
    try:
        path_obj = Path(path)
        if path_obj.is_file():
            path_obj.unlink()
        elif path_obj.is_dir():
            shutil.rmtree(str(path_obj))
        return True
    except Exception:
        return False


def get_file_size_mb(file_path: str) -> float:
    """获取文件大小(MB)
    
    Args:
        file_path: 文件路径
        
    Returns:
        文件大小(MB)
    """
    try:
        size_bytes = os.path.getsize(file_path)
        return size_bytes / (1024 * 1024)
    except:
        return 0.0


def parse_rename_rule(rule: str) -> Tuple[str, str]:
    """解析重命名规则
    
    Args:
        rule: 规则字符串，格式为 "old<--->new"
        
    Returns:
        (旧值, 新值) 元组
    """
    if '<--->' in rule:
        parts = rule.split('<--->', 1)
        return parts[0], parts[1] if len(parts) > 1 else ''
    return rule, ''


def apply_rename_rules(file_path: str, ext_rules: Dict[str, str], 
                      name_rules: Dict[str, str], regex_rules: Dict[str, str]) -> Optional[str]:
    """应用重命名规则
    
    Args:
        file_path: 文件路径
        ext_rules: 扩展名重命名规则
        name_rules: 文件名重命名规则  
        regex_rules: 正则表达式重命名规则
        
    Returns:
        新文件名，如果没有匹配则返回None
    """
    path_obj = Path(file_path)
    name = path_obj.name
    stem = path_obj.stem
    suffix = path_obj.suffix.lower().lstrip('.')
    
    # 应用扩展名规则
    if suffix in ext_rules:
        new_suffix = ext_rules[suffix]
        name = f"{stem}.{new_suffix}" if new_suffix else stem
    
    # 应用文件名包含规则
    for old_part, new_part in name_rules.items():
        if old_part in name:
            name = name.replace(old_part, new_part)
    
    # 应用正则表达式规则
    for pattern, replacement in regex_rules.items():
        try:
            name = re.sub(pattern, replacement, name)
        except re.error:
            continue
    
    return name if name != path_obj.name else None


def should_delete_file(file_path: str, ext_rules: List[str], 
                      name_rules: List[str], regex_rules: List[str]) -> bool:
    """检查文件是否应该被删除
    
    Args:
        file_path: 文件路径
        ext_rules: 扩展名删除规则
        name_rules: 文件名删除规则
        regex_rules: 正则表达式删除规则
        
    Returns:
        是否应该删除
    """
    path_obj = Path(file_path)
    name = path_obj.name
    suffix = path_obj.suffix.lower().lstrip('.')
    
    # 检查扩展名规则
    if suffix in ext_rules:
        return True
    
    # 检查文件名包含规则
    for pattern in name_rules:
        if pattern in name:
            return True
    
    # 检查正则表达式规则
    for pattern in regex_rules:
        try:
            if re.search(pattern, name):
                return True
        except re.error:
            continue
    
    return False


def extract_archive_info(archive_path: str, seven_z_path: str) -> Optional[Dict]:
    """提取压缩包信息
    
    Args:
        archive_path: 压缩包路径
        seven_z_path: 7z.exe路径
        
    Returns:
        压缩包信息字典或None
    """
    import subprocess
    
    try:
        cmd = [seven_z_path, 'l', '-slt', archive_path]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            return None
        
        # 解析输出
        info = {
            'files': [],
            'folders': [],
            'encrypted': False,
            'total_size': 0,
            'file_count': 0
        }
        
        lines = result.stdout.split('\n')
        current_item = {}
        
        for line in lines:
            line = line.strip()
            
            if line.startswith('Path = '):
                if current_item:
                    if current_item.get('Attributes', '').startswith('D'):
                        info['folders'].append(current_item)
                    else:
                        info['files'].append(current_item)
                current_item = {'Path': line[7:]}
            
            elif ' = ' in line and current_item:
                key, value = line.split(' = ', 1)
                current_item[key] = value
                
                if key == 'Size' and value.isdigit():
                    info['total_size'] += int(value)
                elif key == 'Encrypted' and value == '+':
                    info['encrypted'] = True
        
        # 处理最后一个项目
        if current_item:
            if current_item.get('Attributes', '').startswith('D'):
                info['folders'].append(current_item)
            else:
                info['files'].append(current_item)
        
        info['file_count'] = len(info['files'])
        
        return info
        
    except Exception:
        return None


def is_single_root_archive(archive_info: Dict) -> bool:
    """检查压缩包是否只有一个根目录/文件
    
    Args:
        archive_info: 压缩包信息
        
    Returns:
        是否只有单个根
    """
    if not archive_info:
        return False
    
    all_items = archive_info['files'] + archive_info['folders']
    
    if not all_items:
        return False
    
    # 获取所有根路径
    root_paths = set()
    for item in all_items:
        path = item.get('Path', '')
        if path:
            root = path.split('/')[0].split('\\')[0]
            root_paths.add(root)
    
    return len(root_paths) == 1


def get_clipboard_text() -> str:
    """获取剪贴板文本
    
    Returns:
        剪贴板文本
    """
    try:
        import pyperclip
        return pyperclip.paste()
    except:
        return ""


def set_clipboard_text(text: str) -> bool:
    """设置剪贴板文本
    
    Args:
        text: 要设置的文本
        
    Returns:
        是否设置成功
    """
    try:
        import pyperclip
        pyperclip.copy(text)
        return True
    except:
        return False


def validate_7zip_installation(zip_dir: str) -> bool:
    """验证7-zip安装
    
    Args:
        zip_dir: 7-zip安装目录
        
    Returns:
        是否安装正确
    """
    if not os.path.exists(zip_dir):
        return False
    
    required_files = ['7z.exe', '7zG.exe', '7zFM.exe']
    
    for file_name in required_files:
        file_path = os.path.join(zip_dir, file_name)
        if not os.path.exists(file_path):
            return False
    
    return True


def find_7zip_installation() -> Optional[str]:
    """查找7-zip安装目录
    
    Returns:
        7-zip安装目录或None
    """
    possible_paths = [
        r"C:\Program Files\7-Zip",
        r"C:\Program Files (x86)\7-Zip",
        os.path.join(os.environ.get('ProgramFiles', ''), '7-Zip'),
        os.path.join(os.environ.get('ProgramFiles(x86)', ''), '7-Zip')
    ]
    
    for path in possible_paths:
        if validate_7zip_installation(path):
            return path
    
    return None


class PasswordManager:
    """密码管理器"""
    
    def __init__(self):
        self.passwords = []
        self.usage_count = {}
        self.dynamic_sort = False
    
    def add_password(self, password: str) -> bool:
        """添加密码
        
        Args:
            password: 密码
            
        Returns:
            是否添加成功
        """
        if not password or password in self.passwords:
            return False
        
        self.passwords.append(password)
        self.usage_count[password] = 0
        return True
    
    def remove_password(self, password: str) -> bool:
        """移除密码
        
        Args:
            password: 密码
            
        Returns:
            是否移除成功
        """
        if password in self.passwords:
            self.passwords.remove(password)
            self.usage_count.pop(password, None)
            return True
        return False
    
    def use_password(self, password: str):
        """记录密码使用
        
        Args:
            password: 使用的密码
        """
        if password in self.usage_count:
            self.usage_count[password] += 1
            
            if self.dynamic_sort:
                self._sort_by_usage()
    
    def _sort_by_usage(self):
        """按使用频率排序密码"""
        self.passwords.sort(key=lambda p: self.usage_count.get(p, 0), reverse=True)
    
    def get_passwords(self) -> List[str]:
        """获取密码列表
        
        Returns:
            密码列表
        """
        return self.passwords.copy()
    
    def auto_remove_passwords(self, max_count: int):
        """自动移除多余密码
        
        Args:
            max_count: 最大密码数量
        """
        if max_count > 0 and len(self.passwords) > max_count:
            # 按使用频率排序，移除使用频率最低的密码
            sorted_passwords = sorted(self.passwords, 
                                    key=lambda p: self.usage_count.get(p, 0), 
                                    reverse=True)
            
            self.passwords = sorted_passwords[:max_count]
            
            # 清理usage_count
            self.usage_count = {p: self.usage_count.get(p, 0) 
                              for p in self.passwords}
