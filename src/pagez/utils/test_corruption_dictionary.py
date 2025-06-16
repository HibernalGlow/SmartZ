#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
乱码字典测试脚本
验证乱码字典的生成和修复功能
"""

import os
import sys
import json
from pathlib import Path

# 添加当前目录到Python路径
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from generate_corruption_dictionary import CorruptionDictionaryGenerator

def test_corruption_chains():
    """测试各种编码转换链"""
    generator = CorruptionDictionaryGenerator()
    
    # 测试用例
    test_cases = [
        ("日本語", "UTF-8文本"),
        ("メカブ", "片假名"),
        ("第3000回", "中文数字组合"),
        ("ファイル.txt", "文件名"),
        ("压缩文件", "中文词汇"),
        ("アニメ", "动画"),
        ("マンガ", "漫画"),
        ("ゲーム", "游戏"),
    ]
    
    print("=== 编码转换链测试 ===")
    
    for original, description in test_cases:
        print(f"\n原始文本: {original} ({description})")
        
        # 测试 UTF-8 -> Latin-1 -> GBK
        try:
            corrupted_gbk = generator.generate_utf8_latin1_gbk_chain(original)
            print(f"UTF-8→Latin-1→GBK: {corrupted_gbk}")
        except Exception as e:
            print(f"UTF-8→Latin-1→GBK: 失败 - {e}")
        
        # 测试 Shift_JIS -> Latin-1
        try:
            corrupted_sjis = generator.generate_shiftjis_latin1_utf8_chain(original)
            print(f"Shift_JIS→Latin-1: {corrupted_sjis}")
        except Exception as e:
            print(f"Shift_JIS→Latin-1: 失败 - {e}")
        
        # 测试 UTF-8 -> Latin-1 -> Shift_JIS
        try:
            corrupted_utf8_sjis = generator.generate_utf8_latin1_shiftjis_chain(original)
            print(f"UTF-8→Latin-1→Shift_JIS: {corrupted_utf8_sjis}")
        except Exception as e:
            print(f"UTF-8→Latin-1→Shift_JIS: 失败 - {e}")
        
        # 测试双重UTF-8
        try:
            corrupted_double = generator.generate_double_utf8_chain(original)
            print(f"双重UTF-8: {corrupted_double}")
        except Exception as e:
            print(f"双重UTF-8: 失败 - {e}")

def test_dictionary_generation():
    """测试字典生成"""
    print("\n=== 字典生成测试 ===")
    
    generator = CorruptionDictionaryGenerator()
    
    # 生成字典
    mappings, stats = generator.run("test_dictionaries")
    
    print(f"生成了 {len(mappings)} 个转换链字典")
    
    # 显示部分映射示例
    for chain_name, chain_data in list(mappings.items())[:3]:  # 只显示前3个
        print(f"\n{chain_name} 映射示例:")
        
        reverse_map = chain_data.get('reverse', {})
        if reverse_map:
            examples = list(reverse_map.items())[:5]  # 显示前5个映射
            for corrupted, original in examples:
                print(f"  {corrupted} → {original}")

def test_dictionary_usage():
    """测试字典使用"""
    print("\n=== 字典使用测试 ===")
    
    # 检查是否已生成字典
    dict_file = "test_dictionaries/corruption_dictionary.py"
    if not os.path.exists(dict_file):
        print("字典文件不存在，先生成字典...")
        test_dictionary_generation()
    
    # 导入生成的字典
    sys.path.insert(0, "test_dictionaries")
    try:
        from corruption_dictionary import fix_corrupted_text, CORRUPTION_DICTIONARIES
        
        # 测试修复功能
        test_corrupted_texts = [
            "ãƒ¡ã‚«ãƒ–.txt",  # メカブ.txt 的乱码版本
            "æ—¥æœ¬èªž",        # 日本語 的可能乱码
            "ãƒ•ã‚¡ã‚¤ãƒ«",     # ファイル 的乱码版本
        ]
        
        print("测试乱码修复:")
        for corrupted in test_corrupted_texts:
            fixed = fix_corrupted_text(corrupted)
            print(f"  {corrupted} → {fixed}")
            
        # 显示可用的转换链
        print(f"\n可用的转换链: {list(CORRUPTION_DICTIONARIES.keys())}")
        
    except ImportError as e:
        print(f"导入字典失败: {e}")

def test_real_world_examples():
    """测试真实世界的乱码例子"""
    print("\n=== 真实乱码案例测试 ===")
    
    # 这些是从实际ZIP文件中遇到的乱码文件名
    real_cases = [
        {
            "corrupted": "ãƒ¡ã‚«ãƒ–.txt",
            "expected": "メカブ.txt",
            "description": "Shift_JIS → UTF-8 误解释"
        },
        {
            "corrupted": "æ—¥æœ¬èªž.txt", 
            "expected": "日本語.txt",
            "description": "UTF-8 → Latin-1 误解释"
        },
        {
            "corrupted": "ãƒ•ã‚¡ã‚¤ãƒ«",
            "expected": "ファイル",
            "description": "UTF-8字节被当作Latin-1"
        }
    ]
    
    generator = CorruptionDictionaryGenerator()
    
    for case in real_cases:
        print(f"\n测试案例: {case['description']}")
        print(f"乱码: {case['corrupted']}")
        print(f"期望: {case['expected']}")
        
        # 尝试逆向修复
        try:
            # 对于 UTF-8 被误解为 Latin-1 的情况
            if "ãƒ" in case['corrupted']:
                # 编码为 Latin-1 再解码为 UTF-8
                fixed = case['corrupted'].encode('latin-1').decode('utf-8')
                print(f"修复结果: {fixed}")
                print(f"修复成功: {'✓' if fixed == case['expected'] else '✗'}")
            else:
                print("需要更复杂的修复逻辑")
        except Exception as e:
            print(f"修复失败: {e}")

def generate_sample_corrupted_files():
    """生成示例乱码文件用于测试"""
    print("\n=== 生成示例乱码文件 ===")
    
    sample_dir = "sample_corrupted_files"
    os.makedirs(sample_dir, exist_ok=True)
    
    generator = CorruptionDictionaryGenerator()
    
    # 原始文件名
    original_names = [
        "日本語ファイル.txt",
        "メカブアニメ.zip", 
        "第3000回同人誌.rar",
        "压缩文件测试.7z",
        "게임파일.exe"
    ]
    
    for original in original_names:
        print(f"\n原始文件名: {original}")
        
        # 生成各种乱码版本
        corruptions = {
            'utf8_latin1_gbk': generator.generate_utf8_latin1_gbk_chain(original),
            'shiftjis_latin1': generator.generate_shiftjis_latin1_utf8_chain(original),
            'double_utf8': generator.generate_double_utf8_chain(original),
        }
        
        for method, corrupted in corruptions.items():
            if corrupted != original:
                # 创建示例文件
                safe_name = corrupted.replace('/', '_').replace('\\', '_').replace('?', '_')
                file_path = os.path.join(sample_dir, f"{method}_{safe_name}")
                
                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(f"原始文件名: {original}\n")
                        f.write(f"乱码方法: {method}\n")
                        f.write(f"乱码结果: {corrupted}\n")
                    
                    print(f"  {method}: {corrupted}")
                    print(f"    → 保存为: {file_path}")
                    
                except Exception as e:
                    print(f"  {method}: 保存失败 - {e}")

def main():
    """主测试函数"""
    print("乱码字典生成器测试")
    print("=" * 50)
    
    try:
        # 运行各项测试
        test_corruption_chains()
        test_dictionary_generation() 
        test_dictionary_usage()
        test_real_world_examples()
        generate_sample_corrupted_files()
        
        print("\n" + "=" * 50)
        print("所有测试完成!")
        
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
