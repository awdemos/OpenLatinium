from setuptools import setup, find_packages

setup(
    name="openlatinum",
    version="0.2",
    author="OpenLatinum Contributors",
    author_email="",
    description="OpenLatinum: a Latin-inspired programming language",
    packages=find_packages(),
    install_requires=["ply", "tqdm"],
    entry_points={"console_scripts": ["lat = lat.cli:cli"]},
)
