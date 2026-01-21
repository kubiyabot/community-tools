from setuptools import setup, find_packages

setup(
    name="pagerduty_tools",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "kubiya_workflow_sdk[tools]>=0.1.0",
        "requests>=2.31.0",
        "slack-sdk>=3.26.0",
    ],
    author="Kubiya",
    description="PagerDuty management tools for Kubiya",
    python_requires=">=3.8",
) 