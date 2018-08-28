from setuptools import setup, find_packages

setup(
    name="sql-mojo",
    version="0.1.0",
    install_requires=[
        "sql-mojo-parser",
        "elasticsearch",
        "click",
        "python-Levenshtein",
        "pygments",
        "prompt_toolkit>=2.0.0",
        "tabulate",
    ],
    author="The sql-mojo team",
    author_email="git@l3vi.de",
    description="SQL _all_ the things!",
    url="https://github.com/L3viathan/sql-mojo",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "Environment :: Console",
        "Intended Audience :: Developers",
    ],
    entry_points={
        "console_scripts": ["sql-mojo=sql_mojo:main"],
    },
)
