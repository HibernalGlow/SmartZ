"""
压缩包编码检测器
使用7z -l命令检测压缩包内部文件夹是否存在乱码
输出文件路径和可能乱码内容的JSON格式结果
"""
import os
import re
import json
import subprocess
import argparse
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
import unicodedata
try:
    import chardet
except ImportError:
    chardet = None

from .config import ConfigManager


class EncodingDetector:
    """压缩包编码检测器"""
    
    def __init__(self, config_manager: Optional[ConfigManager] = None):
        """初始化检测器
        
        Args:
            config_manager: 配置管理器实例
        """
        self.config = config_manager or ConfigManager()
        
        # 验证7-zip安装
        zip_dir = self.config.zip_dir
        if not os.path.exists(zip_dir):
            raise Exception(f"7-zip 文件夹不存在: {zip_dir}")
            
        self.seven_z = os.path.join(zip_dir, "7z.exe")
        if not os.path.exists(self.seven_z):
            raise Exception(f"7z.exe不存在: {self.seven_z}")
    
    def _is_likely_garbled(self, text: str) -> Tuple[bool, str]:
        """检测文本是否可能是乱码
        
        Args:
            text: 要检测的文本
            
        Returns:
            (是否可能乱码, 检测到的问题类型)
        """
        if not text:
            return False, ""
        
        issues = []
        
        # 1. 检测乱码特征字符
        garbled_patterns = [
            r'[À-ÿ]{3,}',  # 连续的Latin-1扩展字符
            r'[Ã¡Ã¢Ã£Ã¤Ã¥Ã¦Ã§Ã¨Ã©ÃªÃ«Ã¬Ã­Ã®Ã¯]+',  # 常见UTF-8到Latin-1乱码
            r'[锟斤拷]+',    # 经典乱码字符
            r'[ï¿½]+',      # Unicode替换字符
            r'[\ufffd]+',   # Unicode替换字符
        ]
        
        for pattern in garbled_patterns:
            if re.search(pattern, text):
                issues.append("garbled_chars")
                break
        
        # 2. 检测非打印字符
        if any(ord(c) < 32 and c not in '\t\n\r' for c in text):
            issues.append("control_chars")
        
        # 3. 检测编码混乱（同一字符串中混合不同编码系统）
        has_cjk = bool(re.search(r'[\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff]', text))
        has_latin_ext = bool(re.search(r'[À-ÿ]', text))
        if has_cjk and has_latin_ext:
            issues.append("mixed_encoding")
        
        # 4. 检测字符类别异常
        try:
            categories = [unicodedata.category(c) for c in text if c.isprintable()]
            # 如果有太多未定义或私用字符
            undefined_count = sum(1 for cat in categories if cat.startswith('C'))
            if undefined_count > len(text) * 0.3:  # 超过30%是未定义字符
                issues.append("undefined_chars")
        except:
            pass
          # 5. 使用chardet检测编码置信度（如果可用）
        if chardet:
            try:
                detection = chardet.detect(text.encode('utf-8', errors='ignore'))
                if detection and detection['confidence'] < 0.7:  # 置信度低于70%
                    issues.append("low_confidence")
            except:
                pass
        
        return len(issues) > 0, ",".join(issues)
    
    def _parse_7z_output(self, output: str) -> List[Dict[str, Any]]:
        """解析7z -l命令的输出
        
        Args:
            output: 7z命令的输出
            
        Returns:
            文件信息列表
        """
        files = []
        lines = output.split('\n')
        
        # 查找文件列表开始的位置
        start_parsing = False
        header_found = False
        
        for line in lines:
            line = line.strip()
            
            # 跳过空行
            if not line:
                continue
            
            # 查找文件列表的表头
            if re.match(r'^-+\s+-+\s+-+\s+-+', line):
                header_found = True
                continue
            
            if header_found and not start_parsing:
                start_parsing = True
                continue
            
            # 如果遇到分隔线，停止解析
            if start_parsing and re.match(r'^-+', line):
                break
            
            # 解析文件信息行
            if start_parsing:
                # 7z输出格式通常是: 日期 时间 属性 大小 压缩后大小 文件名
                # 使用正则表达式匹配
                match = re.match(r'^(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2}:\d{2})\s+([D\.]{5})\s+(\d+)\s+(\d*)\s+(.+)$', line)
                if match:
                    date, time, attrs, size, compressed_size, name = match.groups()
                    
                    is_directory = 'D' in attrs
                    
                    files.append({
                        'name': name,
                        'is_directory': is_directory,
                        'size': int(size) if size else 0,
                        'compressed_size': int(compressed_size) if compressed_size else 0,
                        'date': date,
                        'time': time,
                        'attributes': attrs
                    })
        
        return files
    
    def detect_archive_encoding_issues(self, archive_path: str) -> Dict[str, Any]:
        """检测压缩包中的编码问题
        
        Args:
            archive_path: 压缩包路径
            
        Returns:
            检测结果字典
        """
        result = {
            'archive_path': archive_path,
            'status': 'success',
            'error': None,
            'total_files': 0,
            'total_directories': 0,
            'issues_found': 0,
            'files_with_issues': [],
            'directories_with_issues': []
        }
        
        try:
            # 执行7z -l命令
            cmd = [self.seven_z, 'l', archive_path]
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=30
            )
            
            if process.returncode != 0:
                result['status'] = 'error'
                result['error'] = f"7z命令执行失败: {process.stderr}"
                return result
            
            # 解析输出
            files = self._parse_7z_output(process.stdout)
            
            # 统计和检测
            for file_info in files:
                name = file_info['name']
                is_dir = file_info['is_directory']
                
                if is_dir:
                    result['total_directories'] += 1
                else:
                    result['total_files'] += 1
                
                # 检测编码问题
                is_garbled, issue_type = self._is_likely_garbled(name)
                
                if is_garbled:
                    result['issues_found'] += 1
                    
                    issue_info = {
                        'name': name,
                        'issue_types': issue_type.split(','),
                        'path': name,  # 在压缩包中的完整路径
                        'size': file_info.get('size', 0),
                        'date': file_info.get('date', ''),
                        'time': file_info.get('time', '')
                    }
                    
                    if is_dir:
                        result['directories_with_issues'].append(issue_info)
                    else:
                        result['files_with_issues'].append(issue_info)
        
        except subprocess.TimeoutExpired:
            result['status'] = 'error'
            result['error'] = "7z命令执行超时"
        except Exception as e:
            result['status'] = 'error'
            result['error'] = str(e)
        
        return result
    
    def detect_multiple_archives(self, archive_paths: List[str]) -> List[Dict[str, Any]]:
        """检测多个压缩包的编码问题
        
        Args:
            archive_paths: 压缩包路径列表
            
        Returns:
            检测结果列表
        """
        results = []
        
        for archive_path in archive_paths:
            if not os.path.exists(archive_path):
                results.append({
                    'archive_path': archive_path,
                    'status': 'error',
                    'error': '文件不存在',
                    'total_files': 0,
                    'total_directories': 0,
                    'issues_found': 0,
                    'files_with_issues': [],
                    'directories_with_issues': []
                })
                continue
            
            result = self.detect_archive_encoding_issues(archive_path)
            results.append(result)
        
        return results
    
    def scan_directory(self, directory: str, extensions: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """扫描目录中的所有压缩包
        
        Args:
            directory: 要扫描的目录
            extensions: 压缩包扩展名列表，如果为None则使用默认列表
            
        Returns:
            检测结果列表
        """
        if extensions is None:
            extensions = ['zip', 'rar', '7z', 'tar', 'gz', 'bz2', 'xz', 'tar.gz', 'tar.bz2', 'tar.xz']
        
        archive_files = []
        
        # 递归查找压缩包文件
        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                file_ext = Path(file).suffix.lower().lstrip('.')
                
                # 检查双扩展名（如.tar.gz）
                if file.lower().endswith('.tar.gz') or file.lower().endswith('.tar.bz2') or file.lower().endswith('.tar.xz'):
                    archive_files.append(file_path)
                elif file_ext in extensions:
                    archive_files.append(file_path)
        
        return self.detect_multiple_archives(archive_files)


def main():
    """主函数 - 命令行入口"""
    parser = argparse.ArgumentParser(description="压缩包编码检测器")
    parser.add_argument('input', nargs='+', help='要检测的压缩包文件或目录')
    parser.add_argument('-o', '--output', help='输出JSON文件路径')
    parser.add_argument('-r', '--recursive', action='store_true', help='递归扫描目录')
    parser.add_argument('--extensions', nargs='+', default=['zip', 'rar', '7z', 'tar', 'gz', 'bz2', 'xz'],
                       help='要检测的压缩包扩展名')
    parser.add_argument('--pretty', action='store_true', help='格式化JSON输出')
    
    args = parser.parse_args()
    
    try:
        detector = EncodingDetector()
        all_results = []
        
        for input_path in args.input:
            if os.path.isfile(input_path):
                # 单个文件
                result = detector.detect_archive_encoding_issues(input_path)
                all_results.append(result)
            elif os.path.isdir(input_path) and args.recursive:
                # 目录扫描
                results = detector.scan_directory(input_path, args.extensions)
                all_results.extend(results)
            else:
                print(f"警告: 跳过无效路径: {input_path}")
        
        # 生成输出
        output_data = {
            'scan_summary': {
                'total_archives': len(all_results),
                'archives_with_issues': sum(1 for r in all_results if r['issues_found'] > 0),
                'total_issues': sum(r['issues_found'] for r in all_results)
            },
            'results': all_results
        }
        
        # 输出结果
        if args.pretty:
            json_output = json.dumps(output_data, ensure_ascii=False, indent=2)
        else:
            json_output = json.dumps(output_data, ensure_ascii=False, separators=(',', ':'))
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(json_output)
            print(f"结果已保存到: {args.output}")
        else:
            print(json_output)
    
    except Exception as e:
        error_result = {
            'scan_summary': {
                'total_archives': 0,
                'archives_with_issues': 0,
                'total_issues': 0
            },
            'error': str(e),
            'results': []
        }
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(error_result, f, ensure_ascii=False, indent=2)
        else:
            print(json.dumps(error_result, ensure_ascii=False, indent=2))
        
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
