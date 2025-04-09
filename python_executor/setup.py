from setuptools import setup, find_packages

setup(
    name="python_executor",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "kubiya-sdk>=0.1.0",
    ],
    author="Kubiya",
    description="A Kubiya tool for safely executing Python code and Jupyter notebooks",
    python_requires=">=3.8",
) 