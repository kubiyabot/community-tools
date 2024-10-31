from setuptools import setup, find_packages

setup(
    name="databricks-workspace-iac",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "kubiya_sdk>=0.1.0",
        "slack_sdk>=3.19.0",
    ],
    python_requires=">=3.8",
)