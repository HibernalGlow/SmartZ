"""
代码页选择器模块的测试
"""
import os
import pytest
import tempfile
from unittest.mock import patch, MagicMock
import configparser

from codepage_pkg.codepage import CodePageConfig, CodePageSelector


class TestCodePageConfig:
    """测试代码页配置管理器"""
    
    def setup_method(self):
        """测试前准备"""
        # 创建临时配置文件
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, "test_codepage.ini")
        self.config = CodePageConfig(self.config_path)
    
    def teardown_method(self):
        """测试后清理"""
        # 清理临时文件
        if os.path.exists(self.config_path):
            os.remove(self.config_path)
        os.rmdir(self.temp_dir)
    
    def test_init(self):
        """测试初始化"""
        # 验证配置文件已创建
        assert os.path.exists(self.config_path)
        
        # 验证配置对象
        assert isinstance(self.config.config, configparser.ConfigParser)
        
        # 验证空的codepage节已创建
        config_parser = configparser.ConfigParser()
        config_parser.read(self.config_path)
        assert 'codepage' in config_parser.sections()
    
    def test_get_custom_codepages_empty(self):
        """测试获取空的自定义代码页列表"""
        codepages = self.config.get_custom_codepages()
        assert isinstance(codepages, list)
        assert len(codepages) == 0
    
    def test_save_and_get_custom_codepages(self):
        """测试保存和获取自定义代码页列表"""
        # 保存自定义代码页
        test_codepages = ["1234", "5678", "9012"]
        self.config.save_custom_codepages(test_codepages)
        
        # 重新加载配置
        self.config = CodePageConfig(self.config_path)
        
        # 获取自定义代码页
        codepages = self.config.get_custom_codepages()
        
        # 验证结果
        assert len(codepages) == len(test_codepages)
        for cp in test_codepages:
            assert cp in codepages


class TestCodePageSelector:
    """测试代码页选择器"""
    
    def setup_method(self):
        """测试前准备"""
        # 创建临时配置文件
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, "test_codepage.ini")
        self.selector = CodePageSelector(self.config_path)
    
    def teardown_method(self):
        """测试后清理"""
        # 清理临时文件
        if os.path.exists(self.config_path):
            os.remove(self.config_path)
        os.rmdir(self.temp_dir)
    
    def test_init(self):
        """测试初始化"""
        # 验证选择器已初始化
        assert self.selector.result_codepage is None
        assert self.selector.result_mcp_param is None
        assert isinstance(self.selector.config, CodePageConfig)
    
    def test_get_all_codepages(self):
        """测试获取所有代码页列表"""
        # 获取所有代码页
        codepages = self.selector.get_all_codepages()
        
        # 验证内置代码页
        assert len(codepages) == len(self.selector.DEFAULT_CODEPAGES)
        for i, (name, cp_id) in enumerate(self.selector.DEFAULT_CODEPAGES):
            assert codepages[i] == (name, cp_id)
        
        # 添加自定义代码页
        custom_codepages = ["1234", "5678"]
        self.selector.config.save_custom_codepages(custom_codepages)
        
        # 重新获取所有代码页
        codepages = self.selector.get_all_codepages()
        
        # 验证自定义代码页已添加
        assert len(codepages) == len(self.selector.DEFAULT_CODEPAGES) + len(custom_codepages)
        for i, cp in enumerate(custom_codepages):
            idx = len(self.selector.DEFAULT_CODEPAGES) + i
            assert codepages[idx] == (cp, int(cp))
    
    @patch('codepage_pkg.codepage.CodePageDialog')
    def test_show_dialog(self, mock_dialog):
        """测试显示对话框"""
        # 设置模拟对话框
        mock_dialog_instance = MagicMock()
        mock_dialog.return_value = mock_dialog_instance
        
        # 设置结果
        self.selector.result_codepage = 936
        self.selector.result_mcp_param = " -mcp=936"
        
        # 调用show_dialog
        codepage_id, mcp_param = self.selector.show_dialog()
        
        # 验证对话框被创建并显示
        mock_dialog.assert_called_once_with(self.selector)
        mock_dialog_instance.show.assert_called_once()
        
        # 验证结果
        assert codepage_id == 936
        assert mcp_param == " -mcp=936"


if __name__ == "__main__":
    pytest.main(["-xvs", __file__]) 