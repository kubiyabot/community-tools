from setuptools import setup, find_packages

setup(
    name="instenv_api_tools",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "requests>=2.25.1",
        "kubiya-sdk>=0.1.0",
        "litellm>=1.0.0",
        "pydantic>=2.0.0",
    ],
    author="Your Name",
    author_email="your.email@example.com",
    description="InstEnv API tools for Kubiya",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/instenv_api_tools",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
) 