from setuptools import setup, find_packages

setup(
    name="kubiya-okta-tools",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "kubiya-sdk",
        "okta-sdk-python>=2.5.0",
    ],
)