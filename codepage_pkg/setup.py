from setuptools import setup, find_packages

setup(
    name="codepage_pkg",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "tkinter",  # 通常是Python标准库的一部分
    ],
    
    # 元数据
    author="SmartZ",
    author_email="smartz@example.com",
    description="代码页选择器 - 用于7-zip操作",
    long_description="""
    代码页选择器包，用于在使用7-zip进行解压缩操作时选择合适的代码页。
    移植自SmartZip的AHK代码页选择功能。
    """,
    keywords="codepage, 7zip, smartzip",
    python_requires=">=3.6",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
) 