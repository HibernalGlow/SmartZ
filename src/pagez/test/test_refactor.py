"""
测试重构后的智能代码页检测器
"""

def test_language_detection():
    """测试语言检测功能"""
    from pagez.core.utils import detect_language_from_text
    
    print("=== 测试语言检测功能 ===")
    test_cases = [
        ("测试文件.zip", "中文"),
        ("テストファイル.rar", "日文"),
        ("test_file.7z", "英文"),
        ("한국어파일.zip", "韩文"),
        ("123.zip", "其他")
    ]
    
    for filename, expected_lang in test_cases:
        detected = detect_language_from_text(filename)
        print(f"{filename} -> {detected} (预期: {expected_lang})")
    
    print(f"缓存统计: {detect_language_from_text.cache_info()}")
    print()


def test_codepage_detection():
    """测试代码页检测功能"""
    from src.pagez import SmartCodePage
    
    print("=== 测试代码页检测功能 ===")
    detector = SmartCodePage()
    
    test_files = [
        "中文测试.zip",
        "日本語テスト.rar", 
        "english_test.7z",
        "한국어테스트.zip"
    ]
    
    for filename in test_files:
        codepage = detector.detect_codepage_from_filename(filename)
        print(f"{filename} -> {codepage}")
    
    print(f"文件名检测缓存: {detector.detect_codepage_from_filename.cache_info()}")
    print()


def test_api_functions():
    """测试API函数"""
    from src.pagez import get_codepage_param, CP_GBK, CP_UTF8
    
    print("=== 测试API函数 ===")
    
    # 测试代码页参数生成
    print(f"GBK参数: {CP_GBK.param}")
    print(f"UTF8参数: {CP_UTF8.param}")
    
    # 注意：这里我们只能测试不存在的文件，因为实际文件可能不存在
    try:
        param = get_codepage_param("测试文件.zip")
        print(f"测试文件代码页参数: {param}")
    except Exception as e:
        print(f"测试文件不存在（预期）: {e}")
    
    print()


def test_thread_safety():
    """测试线程安全功能"""
    import threading
    from pagez.core.utils import detect_language_from_text
    
    print("=== 测试线程安全功能 ===")
    
    results = []
    
    def worker(text, result_list):
        lang = detect_language_from_text(text)
        result_list.append((text, lang))
    
    threads = []
    test_texts = ["测试1.zip", "テスト2.rar", "test3.7z"] * 3
    
    for text in test_texts:
        thread = threading.Thread(target=worker, args=(text, results))
        threads.append(thread)
        thread.start()
    
    for thread in threads:
        thread.join()
    
    print("并发检测结果:")
    for text, lang in results:
        print(f"  {text} -> {lang}")
    
    print(f"最终缓存统计: {detect_language_from_text.cache_info()}")
    print()


def test_performance():
    """测试性能优化"""
    import time
    from pagez.core.utils import detect_language_from_text
    
    print("=== 测试性能优化 ===")
    
    # 清除缓存
    detect_language_from_text.cache_clear()
    
    test_text = "中文测试文件名.zip"
    
    # 第一次调用（无缓存）
    start = time.time()
    result1 = detect_language_from_text(test_text)
    time1 = time.time() - start
    
    # 第二次调用（有缓存）
    start = time.time()
    result2 = detect_language_from_text(test_text)
    time2 = time.time() - start
    
    print(f"第一次调用: {result1}, 耗时: {time1:.6f}秒")
    print(f"第二次调用: {result2}, 耗时: {time2:.6f}秒")
    print(f"性能提升: {time1/time2:.1f}倍")
    print()


if __name__ == "__main__":
    print("智能代码页检测器重构测试")
    print("=" * 50)
    
    test_language_detection()
    test_codepage_detection()
    test_api_functions()
    test_thread_safety()
    test_performance()
    
    print("所有测试完成！")
