from setuptools import setup, find_packages

setup(
    author='UTILIFIED HOLDINGS PTY LTD',
    description='nem12-reader is a package that supports the reading, processing and extraction of NEM-12, NEM-13 and other AEMO-market formats.',
    name='nem12-reader',
    version='1.0.0',
    packages=find_packages(include=[
        'nem12_reader',
        'nem12_reader.*'
    ]),
    python_requires='>=3.8',
    install_requires=[
        'PyMySQL>=1.0.2',
        'wrapt>=1.11.1',
        'numpy>=1.24.2',
        'pandas>=1.5.3',
        'python-dateutil>=2.8.2',
        'pytz>=2022.7.1'
    ]
)
