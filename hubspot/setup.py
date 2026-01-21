from setuptools import setup, find_packages

setup(
    name="hubspot_tools",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "hubspot-api-client>=8.1.0",
        "kubiya_workflow_sdk[tools]",
        "pydantic>=2.0.0"
    ],
    author="Kubiya",
    description="HubSpot integration tools for Kubiya",
    python_requires=">=3.8",
) 