from setuptools import setup, find_packages

setup(
    name="jenkins_tools",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "kubiya-sdk>=0.1.0",
        "requests>=2.31.0",
        "python-jenkins>=1.8.0",
        "pyyaml>=6.0.1",
    ],
    author="Kubiya",
    description="Jenkins management tools for Kubiya",
    python_requires=">=3.8",
) 