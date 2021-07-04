import os
from setuptools import setup


# Parse requirements packages from requirements.txt
def read_requirements():
    path = os.path.join('.', 'requirements.txt')
    with open(path, 'r') as file:
        requirements = [line.rstrip() for line in file]
    return requirements


setup(
    name="Robot controller for Raspberry Pi",
    version="0.0.1",
    description="つくばロボットコンテスト2021 Raspberry Pi用ロボット制御プログラム",
    author="Team 11",
    url="",
    install_requires=read_requirements()
)