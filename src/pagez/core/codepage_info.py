"""
代码页信息模块
定义代码页相关的类和常量
"""
from typing import Dict


class CodePageInfo:
    """代码页信息类"""
    
    def __init__(self, name: str, id: int, description: str = ""):
        """初始化代码页信息
        
        Args:
            name: 代码页名称
            id: 代码页ID
            description: 代码页描述
        """
        self.name = name
        self.id = id
        self.description = description
    
    def __str__(self) -> str:
        return f"{self.name} (ID: {self.id})"
    
    def __repr__(self) -> str:
        return f"CodePageInfo(name='{self.name}', id={self.id})"
    
    def __eq__(self, other) -> bool:
        if isinstance(other, CodePageInfo):
            return self.id == other.id
        return False
    
    def __hash__(self) -> int:
        return hash(self.id)
    
    @property
    def param(self) -> str:
        """返回7z格式的代码页参数"""
        return f"-mcp={self.id}"


# 常用代码页定义
CP_GBK = CodePageInfo("简体中文（GBK）", 936, "中文Windows系统默认编码")
CP_BIG5 = CodePageInfo("繁体中文（大五码）", 950, "台湾/香港Windows系统默认编码")
CP_SHIFT_JIS = CodePageInfo("日文（Shift_JIS）", 932, "日文Windows系统默认编码")
CP_EUC_KR = CodePageInfo("韩文（EUC-KR）", 949, "韩文Windows系统默认编码")
CP_UTF8 = CodePageInfo("UTF-8 Unicode", 65001, "Unicode通用编码")

# 常用代码页列表
COMMON_CODEPAGES = [CP_GBK, CP_BIG5, CP_SHIFT_JIS, CP_EUC_KR, CP_UTF8]

# 语言到代码页的映射
LANG_TO_CODEPAGE: Dict[str, CodePageInfo] = {
    "zh-cn": CP_GBK,
    "zh-tw": CP_BIG5,
    "ja": CP_SHIFT_JIS,
    "ko": CP_EUC_KR,
    "en": CP_UTF8,
    "other": CP_UTF8
}

# 字符集正则表达式范围（备用检测方法）
CHARSET_RANGES = {
    "japanese": r'[\u3040-\u30ff]',  # 日文平假名和片假名
    "korean": r'[\uac00-\ud7a3\u1100-\u11ff]',  # 韩文字符
    "chinese": r'[\u4e00-\u9fff]',  # 中文字符
}
