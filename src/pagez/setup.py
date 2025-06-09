from setuptools import setup, find_packages

setup(
    name="pagez",
    version="2.0.0",
    description="智能代码页检测和压缩包解压工具",
    author="Smart Archive Extractor Team",
    packages=find_packages(),
    install_requires=[
        "loguru>=0.7.3",
        "charset-normalizer>=3.4.2",
        "langdetect>=1.0.9",
    ],
    entry_points={
        "console_scripts": [
            "pagez=pagez.__main__:main",
        ],
    },
    python_requires=">=3.8",
) 