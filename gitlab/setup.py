from setuptools import setup, find_packages

setup(
    name="gitlab_tools",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "kubiya_workflow_sdk[tools]>=0.1.0",
        "python-gitlab>=3.15.0",
        "requests>=2.31.0",
    ],
    author="Kubiya",
    description="GitLab management tools for Kubiya",
    python_requires=">=3.8",
) 