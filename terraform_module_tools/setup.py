from setuptools import setup, find_packages

setup(
    name="kubiya-terraform-module-tools",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "kubiya_sdk>=0.1.0",
        "pyyaml>=5.4.1",
        "python-hcl2>=4.0.0",
        "gitpython>=3.1.0",
    ],
    python_requires=">=3.8",
) 