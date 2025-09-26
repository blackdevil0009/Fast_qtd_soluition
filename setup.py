from setuptools import setup, find_packages
setup(
    name='fastqtd',
    version='0.1.0',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'click',
        'cryptography',
        'scikit-learn',
        'joblib',
        'numpy'
    ],
    entry_points={
        'console_scripts': [
            'fastqtd=fastqtd.cli:cli'
        ]
    }
)
