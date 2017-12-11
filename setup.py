# coding: utf-8
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
] + xyz_require
tests_require = [
    'pytest',
    'freezegun',
] + cocos2d_require


setup(
    name='synergine2',
    version='1.0.1',
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
