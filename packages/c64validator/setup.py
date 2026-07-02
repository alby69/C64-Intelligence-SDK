from setuptools import setup, find_packages

setup(
    name="c64validator",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        # py6502 is local for now or needs to be packaged
    ],
    author="Alberto Abate",
    description="C64 code validation and simulation tools",
)
