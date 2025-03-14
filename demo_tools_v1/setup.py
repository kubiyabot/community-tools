from setuptools import setup, find_packages

setup(
    name="demo_tools",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "kubiya-sdk>=0.1.0",
        "requests>=2.31.0",
    ],
    author="Kubiya",
    description="Demo tools for generating test data",
    python_requires=">=3.8",
) 