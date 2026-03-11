from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="redsignal",
    version="1.0.0",
    author="Security Research Team",
    author_email="research@security.local",
    description="Command and Control Emulation Platform for Security Testing",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/RedSignal",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Information Technology",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Topic :: Security",
    ],
    python_requires=">=3.11",
    install_requires=[
        "fastapi>=0.104.1",
        "uvicorn>=0.24.0",
        "websockets>=12.0",
        "pyyaml>=6.0.1",
        "cryptography>=41.0.7",
        "psutil>=5.9.6",
        "requests>=2.31.0",
        "click>=8.1.7",
        "colorama>=0.4.6",
        "rich>=13.7.0",
        "aiofiles>=23.2.0",
    ],
    entry_points={
        "console_scripts": [
            "redsignal-server=scripts.start_server:main",
            "redsignal-client=scripts.start_client:main",
        ],
    },
)

