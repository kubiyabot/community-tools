from setuptools import setup, find_packages

setup(
    name="slack-tools",
    version="1.0.0",
    description="Kubiya Slack tools with dual token support",
    packages=find_packages(),
    install_requires=[
        "requests>=2.31.0",
        "slack-sdk>=3.21.0",
        "kubiya-sdk",
    ],
    python_requires=">=3.7",
)