from setuptools import setup, find_packages

setup(
    name="datadog_tools",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "kubiya-sdk>=0.1.0",
        "requests>=2.31.0",
        "datadog>=0.44.0",
        "pyyaml>=6.0.1",
    ],
    author="Kubiya",
    description="Datadog monitoring tools for Kubiya",
    python_requires=">=3.8",
) 