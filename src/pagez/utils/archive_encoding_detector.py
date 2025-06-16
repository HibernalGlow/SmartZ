"""
压缩包编码检测器 - 集成版本
使用7z -l命令检测压缩包内部文件夹是否存在乱码
支持交互输入，使用pagez的内部函数进行智能检测
输出文件路径和可能乱码内容的JSON格式结果
"""
import os
import re
import json
import subprocess
import argparse
import sys
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
import unicodedata

# 导入rich模块用于美化界面
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    from rich.prompt import Prompt, Confirm
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.tree import Tree
    from rich.layout import Layout
    from rich.align import Align
    from rich.columns import Columns
    from rich import box
    HAS_RICH = True
except ImportError:
    HAS_RICH = False
    print("Warning: rich模块未找到，将使用基础文本界面")

# 导入pagez模块
try:
    from pagez.core.smart_detector import SmartCodePage
    from pagez.core.utils import detect_language_from_text, safe_subprocess_run
    from pagez.core.logger_config import get_logger
    HAS_PAGEZ = True
except ImportError:
    HAS_PAGEZ = False
    print("Warning: pagez模块未找到，将使用基础检测功能")

try:
    import chardet
except ImportError:
    chardet = None


class EncodingDetector:
    """压缩包编码检测器"""
    
    def __init__(self, seven_z_path: Optional[str] = None):
        """初始化检测器
        
        Args:
            seven_z_path: 7z可执行文件路径，如果为None则尝试自动查找
        """
        if seven_z_path is None:
            # 尝试查找7z.exe
            seven_z_path = self._find_7z_executable()
        
        if not seven_z_path or not os.path.exists(seven_z_path):
            raise Exception(f"7z.exe不存在或未找到: {seven_z_path}")
            
        self.seven_z = seven_z_path
        
        # 初始化pagez检测器（如果可用）
        if HAS_PAGEZ:
            try:
                self.smart_detector = SmartCodePage(seven_z_path)
                self.logger = get_logger()
                self.logger.info(f"已初始化pagez智能检测器，使用7z路径: {seven_z_path}")
            except Exception as e:
                self.smart_detector = None
                print(f"Warning: 无法初始化pagez检测器: {e}")
        else:
            self.smart_detector = None
    def _find_7z_executable(self) -> Optional[str]:
        """自动查找7z可执行文件"""
        # 常见的7z安装路径
        common_paths = [
            r"C:\Program Files\7-Zip\7z.exe",
            r"C:\Program Files (x86)\7-Zip\7z.exe",
            "7z.exe",  # 系统PATH中
            "7z",      # Linux/Mac
        ]
        
        for path in common_paths:
            if os.path.exists(path):
                return path
        
        # 尝试在PATH中查找
        try:
            result = subprocess.run(['where', '7z.exe'], capture_output=True, text=True, shell=True)
            if result.returncode == 0:
                return result.stdout.strip().split('\n')[0]
        except:
            pass
        
        try:
            result = subprocess.run(['which', '7z'], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
        
        return None
    
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
        
        # 使用pagez的语言检测功能（如果可用）
        if HAS_PAGEZ and self.smart_detector:
            try:
                # 使用pagez的文件名编码检测
                detected_codepage = self.smart_detector.detect_codepage_from_filename(text)
                if detected_codepage and hasattr(detected_codepage, 'name'):
                    # 如果检测到的编码不是UTF-8且置信度较低，可能是乱码
                    if 'utf' not in detected_codepage.name.lower():
                        issues.append(f"detected_encoding_{detected_codepage.name}")
                
                # 使用pagez的语言检测
                detected_lang = detect_language_from_text(text)
                if detected_lang == "other":
                    issues.append("unrecognized_language")
                    
            except Exception as e:
                if hasattr(self, 'logger'):
                    self.logger.debug(f"pagez检测出错: {e}")
        
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
        
        # 6. 检测日文乱码特征
        japanese_garbled_patterns = [
            r'[ï½ï¾]{2,}',     # 半角片假名乱码
            r'[繧繝繞]{2,}',     # 日文常见乱码
            r'[縺]{2,}',        # 另一种日文乱码
        ]
        
        for pattern in japanese_garbled_patterns:
            if re.search(pattern, text):
                issues.append("japanese_garbled")
                break
        
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
def interactive_mode(detector: EncodingDetector):
    """交互模式 - 支持用户动态输入（使用rich美化界面）"""
    if HAS_RICH:
        console = Console()
        interactive_mode_rich(detector, console)
    else:
        interactive_mode_basic(detector)


def interactive_mode_rich(detector: EncodingDetector, console: Console):
    """使用rich的交互模式"""
    # 显示欢迎界面
    welcome_panel = Panel.fit(
        "[bold blue]压缩包编码检测器[/bold blue]\n"
        "[dim]使用7z -l命令检测压缩包内部文件名乱码[/dim]\n\n"
        "[green]支持的操作:[/green]\n"
        "• 检测单个压缩包文件\n"
        "• 扫描目录中的所有压缩包\n"
        "• 批量检测多个文件\n"
        "• 递归扫描子目录\n\n"
        "[yellow]输入 'help' 查看详细帮助，'quit' 退出程序[/yellow]",
        title="🔍 编码检测器",
        border_style="blue"
    )
    console.print(welcome_panel)
    
    while True:
        try:
            console.print()
            user_input = Prompt.ask(
                "[bold cyan]请输入要检测的路径[/bold cyan]",
                default="",
                show_default=False
            ).strip()
            
            if not user_input:
                continue
            
            # 处理退出命令
            if user_input.lower() in ['quit', 'exit', 'q']:
                console.print("[green]感谢使用，再见！[/green] 👋")
                break
            
            # 处理帮助命令
            if user_input.lower() in ['help', 'h', '?']:
                show_interactive_help_rich(console)
                continue
            
            # 解析输入路径
            paths = parse_input_paths(user_input)
            
            if not paths:
                console.print("[red]错误: 请输入有效的路径[/red]")
                continue
            
            # 处理每个路径
            all_results = []
            for path in paths:
                path = path.strip().strip('"')
                
                if not os.path.exists(path):
                    console.print(f"[yellow]警告: 路径不存在: {path}[/yellow]")
                    continue
                
                if os.path.isfile(path):
                    # 单个文件
                    with Progress(
                        SpinnerColumn(),
                        TextColumn("[progress.description]{task.description}"),
                        console=console,
                        transient=True
                    ) as progress:
                        task = progress.add_task(f"正在检测文件: {os.path.basename(path)}", total=None)
                        result = detector.detect_archive_encoding_issues(path)
                        progress.update(task, completed=True)
                    
                    all_results.append(result)
                    display_single_result_rich(console, result)
                
                elif os.path.isdir(path):
                    # 目录扫描
                    console.print(f"[blue]📁 正在扫描目录: {path}[/blue]")
                    
                    # 询问是否递归扫描
                    is_recursive = Confirm.ask("是否递归扫描子目录?", default=False)
                    
                    with Progress(
                        SpinnerColumn(),
                        TextColumn("[progress.description]{task.description}"),
                        console=console,
                        transient=True
                    ) as progress:
                        task = progress.add_task("正在扫描目录...", total=None)
                        
                        if is_recursive:
                            results = detector.scan_directory(path)
                        else:
                            results = scan_single_directory(detector, path)
                        
                        progress.update(task, completed=True)
                    
                    all_results.extend(results)
                    display_multiple_results_rich(console, results, path)
                else:
                    console.print(f"[yellow]警告: 不支持的路径类型: {path}[/yellow]")
            
            # 显示总结
            if all_results:
                display_summary_rich(console, all_results)
                
                # 询问是否保存结果
                if Confirm.ask("\n💾 是否保存检测结果到文件?", default=False):
                    output_file = Prompt.ask(
                        "请输入保存文件路径",
                        default="encoding_detection_result.json"
                    )
                    save_results_to_file_rich(console, all_results, output_file)
        
        except KeyboardInterrupt:
            console.print("\n[yellow]操作被用户中断，退出程序[/yellow]")
            break
        except EOFError:
            console.print("\n[yellow]输入结束，退出程序[/yellow]")
            break
        except Exception as e:
            console.print(f"[red]错误: {e}[/red]")
            console.print("[dim]请重新输入或输入 'help' 查看帮助[/dim]")


def interactive_mode_basic(detector: EncodingDetector):
    """基础交互模式（无rich支持）"""
    print("=" * 60)
    print("压缩包编码检测器 - 交互模式")
    print("=" * 60)
    print("说明:")
    print("  - 可以输入单个压缩包文件路径")
    print("  - 可以输入目录路径（将扫描其中的压缩包）")
    print("  - 可以输入多个路径，用空格分隔")
    print("  - 输入 'quit' 或 'exit' 退出")
    print("  - 输入 'help' 查看帮助")
    print("=" * 60)
    
    while True:
        try:
            print("\n请输入要检测的路径:")
            user_input = input("> ").strip()
            
            if not user_input:
                continue
            
            # 处理退出命令
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("感谢使用，再见！")
                break
            
            # 处理帮助命令
            if user_input.lower() in ['help', 'h', '?']:
                show_interactive_help()
                continue
            
            # 解析输入路径
            paths = parse_input_paths(user_input)
            
            if not paths:
                print("错误: 请输入有效的路径")
                continue
            
            # 处理每个路径
            all_results = []
            for path in paths:
                path = path.strip().strip('"')
                
                if not os.path.exists(path):
                    print(f"警告: 路径不存在: {path}")
                    continue
                
                if os.path.isfile(path):
                    # 单个文件
                    print(f"\n正在检测文件: {path}")
                    result = detector.detect_archive_encoding_issues(path)
                    all_results.append(result)
                    display_single_result(result)
                
                elif os.path.isdir(path):
                    # 目录扫描
                    print(f"\n正在扫描目录: {path}")
                    
                    # 询问是否递归扫描
                    recursive = input("是否递归扫描子目录? (y/N): ").strip().lower()
                    is_recursive = recursive in ['y', 'yes', '是']
                    
                    if is_recursive:
                        results = detector.scan_directory(path)
                    else:
                        results = scan_single_directory(detector, path)
                    
                    all_results.extend(results)
                    display_multiple_results(results, path)
                else:
                    print(f"警告: 不支持的路径类型: {path}")
            
            # 显示总结
            if all_results:
                display_summary(all_results)
                
                # 询问是否保存结果
                save_choice = input("\n是否保存检测结果到文件? (y/N): ").strip().lower()
                if save_choice in ['y', 'yes', '是']:
                    output_file = input("请输入保存文件路径 (默认: encoding_detection_result.json): ").strip()
                    if not output_file:
                        output_file = "encoding_detection_result.json"
                    
                    save_results_to_file(all_results, output_file)
        
        except KeyboardInterrupt:
            print("\n\n操作被用户中断，退出程序")
            break
        except EOFError:
            print("\n\n输入结束，退出程序")
            break
        except Exception as e:
            print(f"错误: {e}")
            print("请重新输入或输入 'help' 查看帮助")


def parse_input_paths(user_input: str) -> List[str]:
    """解析用户输入的路径"""
    paths = []
    if user_input.startswith('"') and user_input.endswith('"'):
        # 处理带引号的单个路径
        paths = [user_input[1:-1]]
    else:
        # 处理多个路径（空格分隔）
        paths = user_input.split()
    return paths


def show_interactive_help_rich(console: Console):
    """显示rich版本的交互模式帮助信息"""
    help_table = Table(show_header=True, header_style="bold magenta", box=box.ROUNDED)
    help_table.add_column("输入格式", style="cyan", width=30)
    help_table.add_column("说明", style="white")
    help_table.add_column("示例", style="green")
    
    help_table.add_row(
        "单个文件",
        "输入压缩包文件的完整路径",
        "C:\\archives\\test.zip"
    )
    help_table.add_row(
        "带空格的路径",
        "使用双引号包围包含空格的路径",
        '"C:\\path with spaces\\archive.zip"'
    )
    help_table.add_row(
        "多个文件",
        "用空格分隔多个文件路径",
        "file1.zip file2.rar file3.7z"
    )
    help_table.add_row(
        "目录扫描",
        "输入目录路径扫描其中的压缩包",
        "C:\\downloads\\"
    )
    
    commands_table = Table(show_header=True, header_style="bold yellow", box=box.ROUNDED)
    commands_table.add_column("命令", style="cyan")
    commands_table.add_column("说明", style="white")
    
    commands_table.add_row("help, h, ?", "显示此帮助信息")
    commands_table.add_row("quit, exit, q", "退出程序")
    
    formats_text = Text("zip, rar, 7z, tar, gz, bz2, xz, tar.gz, tar.bz2, tar.xz", style="green")
    
    help_panel = Panel(
        Align.center(
            Columns([
                Panel(help_table, title="📁 输入格式", border_style="blue"),
                Panel(commands_table, title="⌨️ 可用命令", border_style="yellow")
            ])
        ),
        title="🔧 交互模式帮助",
        border_style="magenta"
    )
    
    console.print(help_panel)
    console.print(Panel(formats_text, title="📦 支持的压缩包格式", border_style="green"))


def display_single_result_rich(console: Console, result: Dict[str, Any]):
    """使用rich显示单个检测结果"""
    filename = os.path.basename(result['archive_path'])
    
    if result['status'] == 'error':
        error_panel = Panel(
            f"[red]❌ 检测失败[/red]\n[dim]{result['error']}[/dim]",
            title=f"📦 {filename}",
            border_style="red"
        )
        console.print(error_panel)
        return
    
    # 创建结果表格
    result_table = Table(show_header=False, box=box.SIMPLE)
    result_table.add_column("项目", style="cyan", width=12)
    result_table.add_column("数值", style="white")
    
    result_table.add_row("总文件数", str(result['total_files']))
    result_table.add_row("总目录数", str(result['total_directories']))
    result_table.add_row("问题数量", str(result['issues_found']))
    
    # 状态图标和颜色
    if result['issues_found'] > 0:
        status_icon = "⚠️"
        status_text = f"[yellow]发现 {result['issues_found']} 个编码问题[/yellow]"
        border_style = "yellow"
    else:
        status_icon = "✅"
        status_text = "[green]未发现编码问题[/green]"
        border_style = "green"
    
    # 主面板内容
    content = [
        status_text,
        "",
        result_table
    ]
    
    # 显示问题详情
    if result['issues_found'] > 0:
        content.append("")
        
        if result['files_with_issues']:
            content.append("[red]有问题的文件:[/red]")
            for file_info in result['files_with_issues'][:3]:  # 只显示前3个
                issue_types = ', '.join(file_info['issue_types'])
                content.append(f"  • [dim]{file_info['name']}[/dim] ([red]{issue_types}[/red])")
            
            if len(result['files_with_issues']) > 3:
                content.append(f"  [dim]... 还有 {len(result['files_with_issues']) - 3} 个文件[/dim]")
        
        if result['directories_with_issues']:
            content.append("[red]有问题的目录:[/red]")
            for dir_info in result['directories_with_issues'][:3]:  # 只显示前3个
                issue_types = ', '.join(dir_info['issue_types'])
                content.append(f"  • [dim]{dir_info['name']}[/dim] ([red]{issue_types}[/red])")
            
            if len(result['directories_with_issues']) > 3:
                content.append(f"  [dim]... 还有 {len(result['directories_with_issues']) - 3} 个目录[/dim]")
    
    result_panel = Panel(
        "\n".join(str(item) if not hasattr(item, '__rich__') else item for item in content),
        title=f"{status_icon} {filename}",
        border_style=border_style
    )
    console.print(result_panel)


def display_multiple_results_rich(console: Console, results: List[Dict[str, Any]], base_path: str):
    """使用rich显示多个检测结果的摘要"""
    if not results:
        console.print(f"[yellow]在 {base_path} 中未找到压缩包文件[/yellow]")
        return
    
    issues_count = sum(1 for r in results if r['issues_found'] > 0)
    
    # 创建摘要表格
    summary_table = Table(show_header=True, header_style="bold blue", box=box.ROUNDED)
    summary_table.add_column("压缩包", style="cyan")
    summary_table.add_column("状态", justify="center")
    summary_table.add_column("问题数", justify="right", style="yellow")
    
    for result in results[:10]:  # 只显示前10个
        filename = os.path.basename(result['archive_path'])
        
        if result['status'] == 'error':
            status = "[red]❌ 错误[/red]"
            issues = "[red]-[/red]"
        elif result['issues_found'] > 0:
            status = "[yellow]⚠️ 有问题[/yellow]"
            issues = str(result['issues_found'])
        else:
            status = "[green]✅ 正常[/green]"
            issues = "0"
        
        summary_table.add_row(filename, status, issues)
    
    if len(results) > 10:
        summary_table.add_row("[dim]...[/dim]", "[dim]...[/dim]", "[dim]...[/dim]")
    
    # 状态摘要
    status_text = f"共检测 [bold]{len(results)}[/bold] 个压缩包"
    if issues_count > 0:
        status_text += f"，发现 [yellow]{issues_count}[/yellow] 个存在编码问题"
    else:
        status_text += f"，[green]所有压缩包都没有发现编码问题[/green]"
    
    scan_panel = Panel(
        f"{status_text}\n\n{summary_table}",
        title=f"📂 扫描结果: {os.path.basename(base_path)}",
        border_style="blue"
    )
    console.print(scan_panel)


def display_summary_rich(console: Console, results: List[Dict[str, Any]]):
    """使用rich显示检测结果总结"""
    if not results:
        return
    
    total_archives = len(results)
    archives_with_issues = sum(1 for r in results if r['issues_found'] > 0)
    total_issues = sum(r['issues_found'] for r in results)
    total_files = sum(r['total_files'] for r in results)
    total_directories = sum(r['total_directories'] for r in results)
    
    # 创建统计表格
    stats_table = Table(show_header=False, box=box.SIMPLE)
    stats_table.add_column("统计项", style="cyan", width=15)
    stats_table.add_column("数值", style="bold white", justify="right")
    
    stats_table.add_row("总压缩包数", str(total_archives))
    stats_table.add_row("有问题的包", str(archives_with_issues))
    stats_table.add_row("总问题数", str(total_issues))
    stats_table.add_row("总文件数", str(total_files))
    stats_table.add_row("总目录数", str(total_directories))
    
    # 确定面板样式
    if total_issues > 0:
        icon = "📊"
        border_style = "yellow"
    else:
        icon = "📊"
        border_style = "green"
    
    summary_panel = Panel(
        stats_table,
        title=f"{icon} 检测结果总结",
        border_style=border_style
    )
    console.print(summary_panel)


def save_results_to_file_rich(console: Console, results: List[Dict[str, Any]], output_file: str):
    """使用rich显示保存结果到文件"""
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True
        ) as progress:
            task = progress.add_task("正在保存文件...", total=None)
            
            output_data = {
                'scan_summary': {
                    'total_archives': len(results),
                    'archives_with_issues': sum(1 for r in results if r['issues_found'] > 0),
                    'total_issues': sum(r['issues_found'] for r in results),
                    'total_files': sum(r['total_files'] for r in results),
                    'total_directories': sum(r['total_directories'] for r in results)
                },
                'results': results
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            
            progress.update(task, completed=True)
        
        console.print(f"[green]✅ 结果已保存到: {output_file}[/green]")
    except Exception as e:
        console.print(f"[red]❌ 保存文件失败: {e}[/red]")


def show_interactive_help():
    """显示交互模式帮助信息"""
    print("\n" + "=" * 50)
    print("交互模式帮助")
    print("=" * 50)
    print("支持的输入格式:")
    print("  1. 单个文件: C:\\path\\to\\archive.zip")
    print("  2. 带空格的路径: \"C:\\path with spaces\\archive.zip\"")
    print("  3. 多个文件: file1.zip file2.rar file3.7z")
    print("  4. 目录扫描: C:\\archives\\")
    print("\n支持的命令:")
    print("  help, h, ?     - 显示此帮助")
    print("  quit, exit, q  - 退出程序")
    print("\n支持的压缩包格式:")
    print("  zip, rar, 7z, tar, gz, bz2, xz, tar.gz, tar.bz2, tar.xz")
    print("=" * 50)


def scan_single_directory(detector: EncodingDetector, directory: str) -> List[Dict[str, Any]]:
    """扫描单个目录（不递归）"""
    extensions = ['zip', 'rar', '7z', 'tar', 'gz', 'bz2', 'xz']
    archive_files = []
    
    try:
        for file in os.listdir(directory):
            file_path = os.path.join(directory, file)
            if os.path.isfile(file_path):
                file_ext = Path(file).suffix.lower().lstrip('.')
                
                # 检查双扩展名（如.tar.gz）
                if file.lower().endswith('.tar.gz') or file.lower().endswith('.tar.bz2') or file.lower().endswith('.tar.xz'):
                    archive_files.append(file_path)
                elif file_ext in extensions:
                    archive_files.append(file_path)
    except PermissionError:
        print(f"警告: 无权限访问目录: {directory}")
        return []
    
    return detector.detect_multiple_archives(archive_files)


def display_single_result(result: Dict[str, Any]):
    """显示单个检测结果"""
    print(f"文件: {result['archive_path']}")
    print(f"状态: {result['status']}")
    
    if result['status'] == 'error':
        print(f"错误: {result['error']}")
        return
    
    print(f"总文件数: {result['total_files']}")
    print(f"总目录数: {result['total_directories']}")
    print(f"发现问题数: {result['issues_found']}")
    
    if result['issues_found'] > 0:
        if result['files_with_issues']:
            print("有问题的文件:")
            for file_info in result['files_with_issues'][:5]:  # 只显示前5个
                issue_types = ', '.join(file_info['issue_types'])
                print(f"  - {file_info['name']} (问题: {issue_types})")
            
            if len(result['files_with_issues']) > 5:
                print(f"  ... 还有 {len(result['files_with_issues']) - 5} 个文件有问题")
        
        if result['directories_with_issues']:
            print("有问题的目录:")
            for dir_info in result['directories_with_issues'][:5]:  # 只显示前5个
                issue_types = ', '.join(dir_info['issue_types'])
                print(f"  - {dir_info['name']} (问题: {issue_types})")
            
            if len(result['directories_with_issues']) > 5:
                print(f"  ... 还有 {len(result['directories_with_issues']) - 5} 个目录有问题")


def display_multiple_results(results: List[Dict[str, Any]], base_path: str):
    """显示多个检测结果的摘要"""
    if not results:
        print(f"在 {base_path} 中未找到压缩包文件")
        return
    
    print(f"\n扫描完成: {base_path}")
    print(f"共检测 {len(results)} 个压缩包")
    
    issues_count = sum(1 for r in results if r['issues_found'] > 0)
    if issues_count > 0:
        print(f"发现 {issues_count} 个压缩包存在编码问题:")
        
        for result in results:
            if result['issues_found'] > 0:
                filename = os.path.basename(result['archive_path'])
                print(f"  - {filename}: {result['issues_found']} 个问题")
    else:
        print("所有压缩包都没有发现编码问题")


def display_summary(results: List[Dict[str, Any]]):
    """显示检测结果总结"""
    if not results:
        return
    
    total_archives = len(results)
    archives_with_issues = sum(1 for r in results if r['issues_found'] > 0)
    total_issues = sum(r['issues_found'] for r in results)
    total_files = sum(r['total_files'] for r in results)
    total_directories = sum(r['total_directories'] for r in results)
    
    print("\n" + "=" * 40)
    print("检测结果总结")
    print("=" * 40)
    print(f"总压缩包数: {total_archives}")
    print(f"有问题的压缩包: {archives_with_issues}")
    print(f"总问题数: {total_issues}")
    print(f"总文件数: {total_files}")
    print(f"总目录数: {total_directories}")
    print("=" * 40)


def save_results_to_file(results: List[Dict[str, Any]], output_file: str):
    """保存结果到文件"""
    try:
        output_data = {
            'scan_summary': {
                'total_archives': len(results),
                'archives_with_issues': sum(1 for r in results if r['issues_found'] > 0),
                'total_issues': sum(r['issues_found'] for r in results),
                'total_files': sum(r['total_files'] for r in results),
                'total_directories': sum(r['total_directories'] for r in results)
            },
            'results': results
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        print(f"结果已保存到: {output_file}")
    except Exception as e:
        print(f"保存文件失败: {e}")


def main():
    """主函数 - 命令行入口"""
    parser = argparse.ArgumentParser(description="压缩包编码检测器 - 检测压缩包内部文件名乱码")
    parser.add_argument('input', nargs='*', help='要检测的压缩包文件或目录')
    parser.add_argument('-i', '--interactive', action='store_true', help='启动交互模式')
    parser.add_argument('-o', '--output', help='输出JSON文件路径')
    parser.add_argument('-r', '--recursive', action='store_true', help='递归扫描目录')
    parser.add_argument('--extensions', nargs='+', default=['zip', 'rar', '7z', 'tar', 'gz', 'bz2', 'xz'],
                       help='要检测的压缩包扩展名')
    parser.add_argument('--pretty', action='store_true', help='格式化JSON输出')
    parser.add_argument('--7z-path', help='7z.exe的路径（如果不在系统PATH中）')
    
    args = parser.parse_args()
    
    try:
        detector = EncodingDetector(args.__dict__.get('7z_path'))
        
        # 检查是否启动交互模式
        if args.interactive or not args.input:
            interactive_mode(detector)
            return 0
        
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
                'total_issues': sum(r['issues_found'] for r in all_results),
                'total_files': sum(r['total_files'] for r in all_results),
                'total_directories': sum(r['total_directories'] for r in all_results)
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
                'total_issues': 0,
                'total_files': 0,
                'total_directories': 0
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
