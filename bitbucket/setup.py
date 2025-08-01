from setuptools import setup, find_packages

setup(
    name="kubiya-bitbucket-tools",
    version="0.1.0",
    packages=find_packages(exclude=["tests"]),
    install_requires=[
        "kubiya_workflow_sdk[tools]",
    ],
    author="Your Name",
    author_email="your.email@example.com",
    description="A set of Bitbucket tools for use with Kubiya SDK",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/kubiya-bitbucket-tools",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)