from setuptools import setup, find_packages

setup(
    name="kubiya-atlassian-jira-tools",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "kubiya-sdk",
        "atlassian-jira",
    ],
)