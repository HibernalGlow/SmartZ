# 测试优化后的语言检测
from pagez.core.utils import detect_language_from_text

# 清除缓存
detect_language_from_text.cache_clear()

print('优化后的语言检测:')
test_cases = [
    ("测试文件.zip", "中文"),
    ("テストファイル.rar", "日文"), 
    ("한국어파일.zip", "韩文"),
    ("test_file.7z", "英文")
]

for text, expected in test_cases:
    result = detect_language_from_text(text)
    print(f'{text} -> {result} (预期: {expected})')
