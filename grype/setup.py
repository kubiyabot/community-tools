from setuptools import setup, find_packages

setup(
    name="grype_tools",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "kubiya_sdk>=0.1.0",
    ],
    author="Kubiya",
    author_email="info@kubiya.ai",
    description="Grype vulnerability scanning tools for Kubiya",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/kubiya-tools/grype",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
) 