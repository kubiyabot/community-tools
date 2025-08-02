from setuptools import setup, find_packages

setup(
    name="kubiya-mysql-tools",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "kubiya_workflow_sdk[tools]",
        "mysql-connector-python",
        "sshtunnel",
    ],
    extras_require={
        "test": ["unittest", "mock"],
    },
)