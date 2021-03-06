# coding: utf-8
import sys
from setuptools import setup
from setuptools import find_packages

install_requires = [
    'PyYAML',
    'redis',
    'psutil',
]
xyz_require = [
    'dijkstar',
    'tmx',
    'numpy',
]
cocos2d_require = [
    'cocos2d',
    'Pillow',
] + xyz_require
tests_require = [
    'pytest',
    'freezegun',
    'pytest-mock',
] + cocos2d_require


if sys.version_info.major == 3 and sys.version_info.minor == 4:
    install_requires.append('typing')

setup(
    name='synergine2',
    version='1.0.4',
    description='Subject focus simulation framework',
    author='Bastien Sevajol',
    author_email='sevajol.bastien@gmail.com',
    url='https://github.com/buxx/synergine2',
    packages=find_packages(exclude=[
        'contrib',
        'docs',
        'tests',
    ]),
    classifiers=[
        "Programming Language :: Python",
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: 3.5",
    ],
    install_requires=install_requires,
    extras_require={
        'tests': tests_require,
        'cocos2d': tests_require,
        'xyz': tests_require,
    },
)
