"""
代码页选择对话框的测试
"""
import pytest
from unittest.mock import patch, MagicMock, call
import tkinter as tk

# 导入被测试的类
from codepage_pkg.codepage import CodePageDialog, CodePageSelector


@pytest.fixture
def mock_tk():
    """模拟tkinter组件"""
    with patch('codepage_pkg.codepage.tk.Tk') as mock_tk_class:
        # 模拟tkinter主窗口
        mock_root = MagicMock()
        mock_tk_class.return_value = mock_root
        
        # 模拟样式对象
        with patch('codepage_pkg.codepage.ttk.Style') as mock_style_class:
            mock_style = MagicMock()
            mock_style_class.return_value = mock_style
            mock_style.lookup.return_value = '#f0f0f0'
            
            # 模拟Frame组件
            with patch('codepage_pkg.codepage.ttk.Frame') as mock_frame_class:
                mock_frame = MagicMock()
                mock_frame_class.return_value = mock_frame
                
                # 模拟Label组件
                with patch('codepage_pkg.codepage.ttk.Label') as mock_label_class:
                    mock_label = MagicMock()
                    mock_label_class.return_value = mock_label
                    
                    # 模拟Combobox组件
                    with patch('codepage_pkg.codepage.ttk.Combobox') as mock_combo_class:
                        mock_combo = MagicMock()
                        mock_combo_class.return_value = mock_combo
                        
                        # 模拟Button组件
                        with patch('codepage_pkg.codepage.ttk.Button') as mock_button_class:
                            mock_button = MagicMock()
                            mock_button_class.return_value = mock_button
                            
                            # 模拟StringVar
                            with patch('codepage_pkg.codepage.tk.StringVar') as mock_stringvar_class:
                                mock_stringvar = MagicMock()
                                mock_stringvar_class.return_value = mock_stringvar
                                
                                yield {
                                    'tk': mock_tk_class,
                                    'root': mock_root,
                                    'style': mock_style,
                                    'frame': mock_frame,
                                    'label': mock_label,
                                    'combo': mock_combo,
                                    'button': mock_button,
                                    'stringvar': mock_stringvar
                                }


@pytest.fixture
def mock_selector():
    """模拟代码页选择器"""
    selector = MagicMock(spec=CodePageSelector)
    selector.DEFAULT_CODEPAGES = [
        ("简体中文（GBK）", 936),
        ("繁体中文（大五码）", 950),
        ("日文（Shift_JIS）", 932),
        ("韩文（EUC-KR）", 949),
        ("UTF-8 Unicode", 65001)
    ]
    selector.get_all_codepages.return_value = selector.DEFAULT_CODEPAGES
    
    # 模拟配置对象
    mock_config = MagicMock()
    mock_config.get_custom_codepages.return_value = []
    selector.config = mock_config
    
    return selector


class TestCodePageDialog:
    """测试代码页选择对话框"""
    
    @patch('codepage_pkg.codepage.messagebox')
    def test_init(self, mock_messagebox, mock_tk, mock_selector):
        """测试初始化对话框"""
        # 创建对话框
        dialog = CodePageDialog(mock_selector)
        
        # 验证窗口设置
        mock_tk['root'].title.assert_called_once_with("请选择或输入你需要的代码页")
        mock_tk['root'].geometry.assert_called_once_with("450x250")
        mock_tk['root'].resizable.assert_called_once_with(True, False)
        mock_tk['root'].protocol.assert_called_once_with("WM_DELETE_WINDOW", dialog.on_close)
        
        # 验证组件创建
        assert mock_tk['frame'].grid.called
        assert mock_tk['label'].grid.called
        assert mock_tk['combo'].grid.called
        assert mock_tk['button'].grid.called
    
    @patch('codepage_pkg.codepage.messagebox')
    def test_get_codepage_list(self, mock_messagebox, mock_tk, mock_selector):
        """测试获取代码页列表"""
        dialog = CodePageDialog(mock_selector)
        
        # 调用方法
        result = dialog._get_codepage_list()
        
        # 验证结果
        expected = [name for name, _ in mock_selector.DEFAULT_CODEPAGES]
        assert result == expected
    
    @patch('codepage_pkg.codepage.messagebox')
    def test_add_codepage_valid(self, mock_messagebox, mock_tk, mock_selector):
        """测试添加有效的代码页"""
        dialog = CodePageDialog(mock_selector)
        
        # 设置输入值
        mock_tk['stringvar'].get.return_value = "1251"  # 有效的代码页标识符
        
        # 调用方法
        dialog.add_codepage()
        
        # 验证结果
        assert "1251" in dialog.custom_codepages
        assert mock_tk['combo']['values'] == dialog._get_codepage_list()
    
    @patch('codepage_pkg.codepage.messagebox')
    def test_add_codepage_invalid(self, mock_messagebox, mock_tk, mock_selector):
        """测试添加无效的代码页"""
        dialog = CodePageDialog(mock_selector)
        
        # 设置输入值
        mock_tk['stringvar'].get.return_value = "abc"  # 无效的代码页标识符
        
        # 调用方法
        dialog.add_codepage()
        
        # 验证结果
        assert "abc" not in dialog.custom_codepages
        mock_messagebox.showerror.assert_called_once_with("错误", "请输入有效的代码页标识符（数字）")
    
    @patch('codepage_pkg.codepage.messagebox')
    def test_delete_codepage(self, mock_messagebox, mock_tk, mock_selector):
        """测试删除代码页"""
        dialog = CodePageDialog(mock_selector)
        
        # 添加自定义代码页
        dialog.custom_codepages = ["1251", "1252"]
        
        # 设置输入值
        mock_tk['stringvar'].get.return_value = "1251"
        
        # 调用方法
        dialog.delete_codepage()
        
        # 验证结果
        assert "1251" not in dialog.custom_codepages
        assert dialog.custom_codepages == ["1252"]
    
    @patch('codepage_pkg.codepage.messagebox')
    def test_on_confirm_with_digit(self, mock_messagebox, mock_tk, mock_selector):
        """测试使用数字确认选择"""
        dialog = CodePageDialog(mock_selector)
        
        # 设置输入值
        mock_tk['stringvar'].get.return_value = "1251"
        
        # 调用方法
        dialog.on_confirm()
        
        # 验证结果
        assert mock_selector.result_codepage == 1251
        assert mock_selector.result_mcp_param == " -mcp=1251"
        mock_selector.config.save_custom_codepages.assert_called_once_with(dialog.custom_codepages)
        mock_tk['root'].destroy.assert_called_once()
    
    @patch('codepage_pkg.codepage.messagebox')
    def test_on_confirm_with_name(self, mock_messagebox, mock_tk, mock_selector):
        """测试使用名称确认选择"""
        dialog = CodePageDialog(mock_selector)
        
        # 设置输入值
        mock_tk['stringvar'].get.return_value = "简体中文（GBK）"
        
        # 调用方法
        dialog.on_confirm()
        
        # 验证结果
        assert mock_selector.result_codepage == 936
        assert mock_selector.result_mcp_param == " -mcp=936"
        mock_tk['root'].destroy.assert_called_once()
    
    @patch('codepage_pkg.codepage.messagebox')
    def test_on_close(self, mock_messagebox, mock_tk, mock_selector):
        """测试关闭对话框"""
        dialog = CodePageDialog(mock_selector)
        
        # 调用方法
        dialog.on_close()
        
        # 验证结果
        assert mock_selector.result_codepage is None
        assert mock_selector.result_mcp_param is None
        mock_tk['root'].destroy.assert_called_once()
    
    @patch('codepage_pkg.codepage.messagebox')
    def test_show(self, mock_messagebox, mock_tk, mock_selector):
        """测试显示对话框"""
        dialog = CodePageDialog(mock_selector)
        
        # 调用方法
        dialog.show()
        
        # 验证结果
        mock_tk['root'].grab_set.assert_called_once()
        mock_tk['root'].focus_set.assert_called_once()
        mock_tk['root'].update_idletasks.assert_called_once()
        mock_tk['root'].mainloop.assert_called_once()


if __name__ == "__main__":
    pytest.main(["-xvs", __file__]) 