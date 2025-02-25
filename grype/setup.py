from setuptools import setup, find_packages

setup(
    name="kubiya-grype-tools",
    version="0.1.0",
    packages=find_packages(exclude=["tests"]),
    install_requires=[
        "kubiya-sdk",
    ],
    entry_points={
        "kubiya.tools": [
            "grype_tools=grype_tools.tools:grype_tools",
        ],
    },
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
    python_requires='>=3.6',
) 