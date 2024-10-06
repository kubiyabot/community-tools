from setuptools import setup, find_packages

setup(
    name="kubiya-terraform-tools",
    version="0.1.0",
    packages=find_packages(where="terraform"),
    package_dir={"": "terraform"},
    install_requires=[
        "kubiya-sdk",
    ],
)