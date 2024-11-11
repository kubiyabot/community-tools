from setuptools import setup, find_packages

setup(
    name="kubiya-kubernetes-tools",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "kubiya-sdk>=0.1.0",
        "slack-sdk>=3.19.0",
        "websocket-client>=1.6.1",
        "pyyaml>=6.0",
    ],
    python_requires=">=3.8",
)
