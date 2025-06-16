#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
乱码字典生成器
自动生成各种编码转换链产生的乱码映射表

支持的转换链：
- UTF-8 -> Latin-1 -> GBK
- Shift_JIS -> Latin-1 -> UTF-8
- UTF-8 -> Latin-1 -> Shift_JIS
- GBK -> Latin-1 -> UTF-8
- CP932 -> Latin-1 -> UTF-8
"""

import json
import os
import sys
from typing import Dict, List, Tuple, Set
import logging
from collections import defaultdict

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class CorruptionDictionaryGenerator:
    """乱码字典生成器"""
    
    def __init__(self):
        self.corruption_maps = {}
        self.reverse_maps = {}
        
    def generate_utf8_latin1_gbk_chain(self, text: str) -> str:
        """UTF-8 -> Latin-1 -> GBK 转换链"""
        try:
            # Step 1: UTF-8 字节被误解为 Latin-1
            utf8_bytes = text.encode('utf-8')
            latin1_str = utf8_bytes.decode('latin-1', errors='replace')
            
            # Step 2: Latin-1 字符串被误解为 GBK
            latin1_bytes = latin1_str.encode('latin-1', errors='replace')
            gbk_str = latin1_bytes.decode('gbk', errors='replace')
            
            return gbk_str
        except Exception as e:
            logger.warning(f"UTF-8->Latin-1->GBK 转换失败: {text} - {e}")
            return text
    
    def generate_shiftjis_latin1_utf8_chain(self, text: str) -> str:
        """Shift_JIS -> Latin-1 -> UTF-8 转换链"""
        try:
            # Step 1: 原始文本按 Shift_JIS 编码
            shiftjis_bytes = text.encode('shift_jis')
            
            # Step 2: Shift_JIS 字节被误解为 Latin-1
            latin1_str = shiftjis_bytes.decode('latin-1', errors='replace')
            
            # Step 3: Latin-1 字符串正常处理（已经是损坏的结果）
            return latin1_str
        except Exception as e:
            logger.warning(f"Shift_JIS->Latin-1 转换失败: {text} - {e}")
            return text
    
    def generate_utf8_latin1_shiftjis_chain(self, text: str) -> str:
        """UTF-8 -> Latin-1 -> Shift_JIS 转换链"""
        try:
            # Step 1: UTF-8 字节被误解为 Latin-1
            utf8_bytes = text.encode('utf-8')
            latin1_str = utf8_bytes.decode('latin-1', errors='replace')
            
            # Step 2: Latin-1 字符串被误解为 Shift_JIS
            latin1_bytes = latin1_str.encode('latin-1', errors='replace')
            shiftjis_str = latin1_bytes.decode('shift_jis', errors='replace')
            
            return shiftjis_str
        except Exception as e:
            logger.warning(f"UTF-8->Latin-1->Shift_JIS 转换失败: {text} - {e}")
            return text
    
    def generate_gbk_latin1_utf8_chain(self, text: str) -> str:
        """GBK -> Latin-1 -> UTF-8 转换链"""
        try:
            # Step 1: 原始文本按 GBK 编码
            gbk_bytes = text.encode('gbk')
            
            # Step 2: GBK 字节被误解为 Latin-1
            latin1_str = gbk_bytes.decode('latin-1', errors='replace')
            
            return latin1_str
        except Exception as e:
            logger.warning(f"GBK->Latin-1 转换失败: {text} - {e}")
            return text
    
    def generate_cp932_latin1_utf8_chain(self, text: str) -> str:
        """CP932 -> Latin-1 -> UTF-8 转换链"""
        try:
            # Step 1: 原始文本按 CP932 编码
            cp932_bytes = text.encode('cp932')
            
            # Step 2: CP932 字节被误解为 Latin-1
            latin1_str = cp932_bytes.decode('latin-1', errors='replace')
            
            return latin1_str
        except Exception as e:
            logger.warning(f"CP932->Latin-1 转换失败: {text} - {e}")
            return text
    
    def generate_double_utf8_chain(self, text: str) -> str:
        """双重 UTF-8 编码"""
        try:
            # Step 1: UTF-8 编码
            utf8_bytes = text.encode('utf-8')
            utf8_str = utf8_bytes.decode('utf-8')
            
            # Step 2: 再次 UTF-8 编码然后被误解为 Latin-1
            double_utf8_bytes = utf8_str.encode('utf-8')
            latin1_str = double_utf8_bytes.decode('latin-1', errors='replace')
            
            return latin1_str
        except Exception as e:
            logger.warning(f"双重UTF-8 转换失败: {text} - {e}")
            return text
    
    def get_common_characters(self) -> Dict[str, List[str]]:
        """获取常见字符集合"""
        return {
            'chinese_simplified': [
                # 常用汉字
                '的', '一', '是', '在', '不', '了', '有', '和', '人', '这',
                '中', '大', '为', '上', '个', '国', '我', '以', '要', '他',
                '时', '来', '用', '们', '生', '到', '作', '地', '于', '出',
                '就', '分', '对', '成', '会', '可', '主', '发', '年', '动',
                '同', '工', '也', '能', '下', '过', '子', '说', '产', '种',
                '面', '而', '方', '后', '多', '定', '行', '学', '法', '所',
                # 文件相关
                '文件', '压缩', '解压', '目录', '文档', '图片', '视频', '音频',
                '下载', '上传', '备份', '恢复', '删除', '复制', '移动', '重命名'
            ],
            'japanese_hiragana': [
                # 平假名
                'あ', 'い', 'う', 'え', 'お', 'か', 'き', 'く', 'け', 'こ',
                'さ', 'し', 'す', 'せ', 'そ', 'た', 'ち', 'つ', 'て', 'と',
                'な', 'に', 'ぬ', 'ね', 'の', 'は', 'ひ', 'ふ', 'へ', 'ほ',
                'ま', 'み', 'む', 'め', 'も', 'や', 'ゆ', 'よ', 'ら', 'り',
                'る', 'れ', 'ろ', 'わ', 'を', 'ん'
            ],
            'japanese_katakana': [
                # 片假名
                'ア', 'イ', 'ウ', 'エ', 'オ', 'カ', 'キ', 'ク', 'ケ', 'コ',
                'サ', 'シ', 'ス', 'セ', 'ソ', 'タ', 'チ', 'ツ', 'テ', 'ト',
                'ナ', 'ニ', 'ヌ', 'ネ', 'ノ', 'ハ', 'ヒ', 'フ', 'ヘ', 'ホ',
                'マ', 'ミ', 'ム', 'メ', 'モ', 'ヤ', 'ユ', 'ヨ', 'ラ', 'リ',
                'ル', 'レ', 'ロ', 'ワ', 'ヲ', 'ン'
            ],
            'japanese_kanji': [
                # 常用汉字
                '日', '本', '語', '人', '時', '年', '月', '日', '国', '会',
                '事', '自', '分', '現', '前', '回', '同', '人', '誌', '作',
                '品', '者', '名', '場', '合', '手', '数', '方', '新', '家',
                '場', '所', '問', '題', '世', '界', '全', '部', '関', '係'
            ],
            'korean': [
                # 韩文
                '한', '국', '어', '안', '녕', '하', '세', '요', '감', '사',
                '합', '니', '다', '죄', '송', '미', '안', '네', '아', '니',
                '예', '맞', '습', '모', '르', '겠', '어', '디', '가', '지'
            ],
            'common_symbols': [
                # 常见符号
                '(', ')', '[', ']', '{', '}', '-', '_', '+', '=',
                '!', '@', '#', '$', '%', '^', '&', '*', '~', '`',
                '|', '\\', '/', '?', '<', '>', ',', '.', ';', ':',
                '"', "'", ' ', '\t', '\n'
            ],
            'file_extensions': [
                '.txt', '.zip', '.rar', '.7z', '.pdf', '.doc', '.docx',
                '.jpg', '.png', '.gif', '.mp4', '.avi', '.mp3', '.wav'
            ]
        }
    
    def generate_corruption_mappings(self) -> Dict[str, Dict[str, str]]:
        """生成所有乱码映射"""
        logger.info("开始生成乱码字典...")
        
        # 获取测试字符
        character_sets = self.get_common_characters()
        all_chars = []
        for chars in character_sets.values():
            all_chars.extend(chars)
        
        # 生成各种转换链的映射
        corruption_chains = {
            'utf8_latin1_gbk': self.generate_utf8_latin1_gbk_chain,
            'shiftjis_latin1_utf8': self.generate_shiftjis_latin1_utf8_chain,
            'utf8_latin1_shiftjis': self.generate_utf8_latin1_shiftjis_chain,
            'gbk_latin1_utf8': self.generate_gbk_latin1_utf8_chain,
            'cp932_latin1_utf8': self.generate_cp932_latin1_utf8_chain,
            'double_utf8': self.generate_double_utf8_chain,
        }
        
        mappings = {}
        
        for chain_name, chain_func in corruption_chains.items():
            logger.info(f"生成 {chain_name} 映射...")
            chain_mapping = {}
            reverse_mapping = {}
            
            for char in all_chars:
                try:
                    corrupted = chain_func(char)
                    if corrupted != char and corrupted not in ['?', '�']:
                        chain_mapping[char] = corrupted
                        reverse_mapping[corrupted] = char
                        
                except Exception as e:
                    logger.warning(f"处理字符 '{char}' 时出错: {e}")
                    continue
            
            mappings[chain_name] = {
                'forward': chain_mapping,
                'reverse': reverse_mapping
            }
            
            logger.info(f"{chain_name}: 生成 {len(chain_mapping)} 个正向映射, {len(reverse_mapping)} 个反向映射")
        
        return mappings
    
    def generate_compound_mappings(self, base_mappings: Dict) -> Dict[str, Dict[str, str]]:
        """生成复合字符串的映射（词汇级别）"""
        logger.info("生成复合字符串映射...")
        
        # 常见的复合词
        compound_words = [
            # 中文
            "第3000回", "日本語", "同人誌", "差分多数", "压缩文件", "解压缩",
            "文件名", "编码错误", "字符集", "乱码修复",
            
            # 日文
            "メカブ", "アニメ", "マンガ", "ゲーム", "ソフトウェア",
            "ファイル", "フォルダ", "ダウンロード", "アップロード",
            
            # 文件名模式
            "hash-99511b59f3e3e422", "[hash-", "].txt", "].zip",
            "(差分多数)", "(修正版)", "(完整版)", "(高清版)"
        ]
        
        compound_mappings = {}
        
        for chain_name, chain_data in base_mappings.items():
            forward_map = chain_data['forward']
            compound_forward = {}
            compound_reverse = {}
            
            for word in compound_words:
                corrupted_word = ""
                can_map = True
                
                for char in word:
                    if char in forward_map:
                        corrupted_word += forward_map[char]
                    else:
                        corrupted_word += char
                
                if corrupted_word != word:
                    compound_forward[word] = corrupted_word
                    compound_reverse[corrupted_word] = word
            
            compound_mappings[f"{chain_name}_compound"] = {
                'forward': compound_forward,
                'reverse': compound_reverse
            }
            
            logger.info(f"{chain_name}_compound: 生成 {len(compound_forward)} 个复合映射")
        
        return compound_mappings
    
    def save_dictionaries(self, mappings: Dict, output_dir: str = "corruption_dictionaries"):
        """保存字典到文件"""
        logger.info(f"保存字典到 {output_dir}...")
        
        os.makedirs(output_dir, exist_ok=True)
        
        # 保存完整字典
        full_dict_path = os.path.join(output_dir, "corruption_dictionary_full.json")
        with open(full_dict_path, 'w', encoding='utf-8') as f:
            json.dump(mappings, f, ensure_ascii=False, indent=2)
        
        # 分别保存每个转换链的字典
        for chain_name, chain_data in mappings.items():
            chain_file = os.path.join(output_dir, f"{chain_name}.json")
            with open(chain_file, 'w', encoding='utf-8') as f:
                json.dump(chain_data, f, ensure_ascii=False, indent=2)
        
        # 生成Python可直接使用的字典文件
        py_dict_path = os.path.join(output_dir, "corruption_dictionary.py")
        with open(py_dict_path, 'w', encoding='utf-8') as f:
            f.write('# -*- coding: utf-8 -*-\n')
            f.write('"""\n自动生成的乱码字典\n"""\n\n')
            f.write('CORRUPTION_DICTIONARIES = ')
            f.write(repr(mappings))
            f.write('\n\n')
            
            # 添加便捷函数
            f.write('''
def get_corruption_map(chain_name: str, direction: str = 'reverse'):
    """
    获取指定转换链的映射字典
    
    Args:
        chain_name: 转换链名称
        direction: 'forward' 或 'reverse'
    """
    return CORRUPTION_DICTIONARIES.get(chain_name, {}).get(direction, {})

def fix_corrupted_text(text: str, chain_name: str = None):
    """
    修复乱码文本
    
    Args:
        text: 乱码文本
        chain_name: 指定转换链，None表示尝试所有链
    """
    if chain_name:
        mapping = get_corruption_map(chain_name, 'reverse')
        return apply_mapping(text, mapping)
    
    # 尝试所有转换链
    for chain in CORRUPTION_DICTIONARIES:
        if 'reverse' in CORRUPTION_DICTIONARIES[chain]:
            mapping = CORRUPTION_DICTIONARIES[chain]['reverse']
            result = apply_mapping(text, mapping)
            if result != text:
                return result
    
    return text

def apply_mapping(text: str, mapping: dict):
    """应用字符映射"""
    result = text
    # 按长度排序，优先处理长字符串
    for corrupted, original in sorted(mapping.items(), key=lambda x: len(x[0]), reverse=True):
        result = result.replace(corrupted, original)
    return result

# 预定义的常用映射
UTF8_LATIN1_GBK_REVERSE = get_corruption_map('utf8_latin1_gbk', 'reverse')
SHIFTJIS_LATIN1_REVERSE = get_corruption_map('shiftjis_latin1_utf8', 'reverse')
UTF8_LATIN1_SHIFTJIS_REVERSE = get_corruption_map('utf8_latin1_shiftjis', 'reverse')
''')
        
        logger.info(f"字典已保存到: {output_dir}")
        logger.info(f"- 完整字典: {full_dict_path}")
        logger.info(f"- Python字典: {py_dict_path}")
    
    def generate_statistics(self, mappings: Dict) -> Dict:
        """生成统计信息"""
        stats = {
            'total_chains': len(mappings),
            'chain_details': {}
        }
        
        for chain_name, chain_data in mappings.items():
            forward_count = len(chain_data.get('forward', {}))
            reverse_count = len(chain_data.get('reverse', {}))
            
            stats['chain_details'][chain_name] = {
                'forward_mappings': forward_count,
                'reverse_mappings': reverse_count,
                'efficiency': reverse_count / max(forward_count, 1) * 100
            }
        
        return stats
    
    def run(self, output_dir: str = "corruption_dictionaries"):
        """运行字典生成流程"""
        logger.info("开始生成乱码字典...")
        
        # 生成基础映射
        base_mappings = self.generate_corruption_mappings()
        
        # 生成复合映射
        compound_mappings = self.generate_compound_mappings(base_mappings)
        
        # 合并所有映射
        all_mappings = {**base_mappings, **compound_mappings}
        
        # 保存字典
        self.save_dictionaries(all_mappings, output_dir)
        
        # 生成统计
        stats = self.generate_statistics(all_mappings)
        
        # 保存统计信息
        stats_path = os.path.join(output_dir, "statistics.json")
        with open(stats_path, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        
        logger.info("乱码字典生成完成!")
        logger.info(f"总计生成 {stats['total_chains']} 个转换链")
        
        return all_mappings, stats

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='生成乱码字典')
    parser.add_argument('--output-dir', '-o', default='corruption_dictionaries',
                       help='输出目录 (默认: corruption_dictionaries)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='显示详细信息')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    generator = CorruptionDictionaryGenerator()
    mappings, stats = generator.run(args.output_dir)
    
    print("\n=== 生成统计 ===")
    for chain_name, details in stats['chain_details'].items():
        print(f"{chain_name}:")
        print(f"  正向映射: {details['forward_mappings']}")
        print(f"  反向映射: {details['reverse_mappings']}")
        print(f"  效率: {details['efficiency']:.1f}%")
    
    print(f"\n字典已保存到: {args.output_dir}")

if __name__ == "__main__":
    main()
