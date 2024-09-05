from setuptools import setup, find_packages

setup(
    name="kubiya-k8s-tools",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "kubiya-sdk",
    ],
)
