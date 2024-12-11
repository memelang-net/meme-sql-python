from setuptools import setup, find_packages

setup(
    name="meme",
    version="0.1.0",
    description="A Memelang query processing library.",
    author="Bri <bri@memelang.net>",
    url="https://github.com/memelang-net/meme-sql-python",
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'meme-query=meme.cli:main',
        ],
    },
    install_requires=[],
)
