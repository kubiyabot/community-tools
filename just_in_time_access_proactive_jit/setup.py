from setuptools import setup, find_packages

setup(
    name="just_in_time_access",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "kubiya_sdk",
        "requests",
    ],
) 