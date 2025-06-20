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
    "garbled_chars": r'[\u5080-\u50ff\u6800-\u69ff\u7000-\u79ff\u8000-\u89ff\u9000-\u97ff]',  # 常见乱码特殊字符范围
}

# 可能是日文编码错误导致的特殊字符集
POSSIBLE_JAPANESE_GARBLED = set([
    '丂', '丄', '丅', '丌', '丒', '丟', '丣', '丨', '丫', '丮', '丯', '丰', '丵', '丷', '丼',
    '乀', '乁', '乂', '乄', '乆', '乊', '乑', '乕', '乗', '乚', '乛', '乢', '乣', '乤', '乥', '乧', '乨', '乪', '乫', '乬', '乭', '乮', '乯', '乲', '乴', '乵', '乶', '乷', '乸', '乹', '乺', '乻', '乼', '乽', '乿',
    '亀', '亁', '亂', '亃', '亄', '亅', '亇', '亊', '亐', '亖', '亗', '亙', '亝', '亞', '亣', '亪', '亯', '亰', '亱', '亴', '亶', '亷', '亸', '亹', '亼', '亽', '亾', '仈', '仌', '仏', '仐', '仒', '仚', '仛', '仜', '仠', '仢', '仦', '仧', '仩', '仭', '仮', '仯', '仱', '仴', '仸',
    '傑', '傔', '傘', '傛', '傜', '傝', '傞', '傟', '傠', '傡', '傢', '傤', '傦', '傪', '傫', '傭', '傮', '傰', '傱', '傳', '傴', '傶', '傷', '傸', '傹', '傼', '傽', '傾', '傿',
    '僂', '僃', '僄', '僅', '僇', '僈', '僉', '僊', '僋', '僌', '僎', '僐', '僑', '僓', '僔', '僗', '僘', '僙', '僛', '僜', '僝', '僟', '僠', '僡', '僢', '僣', '僤', '僨', '僩', '僪', '僫', '僯', '僰', '僱', '僲', '僴', '僶', '僷', '僸', '僺', '僼', '僽', '僾',
    '儈', '儉', '儊', '儌', '儍', '儎', '儏', '儐', '儑', '儓', '儔', '儕', '儗', '儘', '儙', '儚', '儛', '儜', '儝', '儞', '儠', '儢', '儣', '儤', '儥', '儦', '儧', '儨', '儩', '優', '儫', '儬', '儭', '儮', '儯', '儰', '儱', '儲', '儳', '儴', '儵', '儶', '儷', '儸', '儹', '儺', '儻', '儼', '儽', '儾',
    '兗', '兘', '兟', '兤', '兦', '兾', '冃', '冄', '冋', '冎', '冘', '冝', '冡', '冣', '冭', '冮', '冹',
    '凃', '凈', '凊', '凍', '凎', '凐', '凒', '凓', '凕', '凖', '凘', '凙', '凚', '凜', '凞', '凟', '凢',
    '刕', '刜', '刞', '刟', '刡', '刢', '刣', '別', '刦', '刧', '刪', '刬', '刯', '刱', '刲', '刴', '刵', '刼', '刾', '剄', '剅', '剆', '則', '剈', '剉', '剋', '剎', '剏', '剒', '剓', '剕', '剗', '剘', '剙', '剚', '剛', '剝', '剟', '剠', '剢', '剣', '剤', '剦', '剨', '剫', '剬', '剭', '剮', '剰', '剱', '剳', '剴', '剶', '剷', '剸', '剹', '剺', '剻', '剼', '剾',
    '勀', '勁', '勂', '勄', '勅', '勆', '勈', '勊', '勌', '勍', '勎', '勏', '勑', '勓', '勔', '勖', '勛', '勜', '勝', '勞', '勠', '勡', '勣', '勥', '勦', '勧', '勨', '勩', '勪', '勫', '勬', '勭', '勮', '勯', '勱', '勲', '勳', '勴', '勵', '勶', '勷', '勸', '勻',
    '匁', '匂', '匃', '匄', '匇', '匉', '匊', '匋', '匌', '匎', '匑', '匒', '匓', '匔', '匘', '匛', '匜', '匞', '匟', '匢', '匤', '匥', '匧', '匨', '匩', '匫', '匬', '匭', '匯', '匰', '匱', '匲', '匳', '匴', '匵', '匶', '匷', '匸', '匼', '匽', '區', '卂', '卄', '卆', '卋', '卌', '卍', '卐', '協', '単', '卙', '卛', '卝', '卥', '卨', '卪', '卬', '卭',
])
