from setuptools import setup, find_packages

setup(
    author='Utilified Holdings Pty Ltd',
    description='',
    name='nem12-reader',
    version='0.1.0',
    packages=find_packages(include=[
        'nem12_reader',
        'nem12_reader.*'
    ]),
    python_requires='>=3.8',
    install_requires=[
        'PyMySQL>=1.0.2',
        'wrapt>=1.11.1'
    ]
)
