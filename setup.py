from setuptools import setup, find_packages
import pathlib

here = pathlib.Path(__file__).parent.resolve()
long_description = (here / "README.md").read_text(encoding="utf-8")

setup(
    name="autodw",
    version="0.1.0",
    description="Database schema serialization with LLM integration",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Shaobin Shi",
    author_email="d7inshi@gmail.com",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.8, <4",
    install_requires=[
        "mysql-connector-python>=8.0",
        "psycopg2-binary>=2.9",
        "openai>=0.27",
        "sqlparse>=0.4",
    ],
    extras_require={
        "dev": ["pytest>=7.0", "black>=23.0"],
        "llm": ["langchain>=0.1", "transformers>=4.0"],
    },
    entry_points={
        "console_scripts": [
            "autodw=autodw.cli:main",
        ],
    },
    project_urls={
        "Source": "https://github.com/yourusername/autodw",
    },
)