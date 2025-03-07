from setuptools import setup, find_packages

setup(
    name="aws_jit_tools",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "kubiya-sdk",
        "boto3",
        "requests",
        "jinja2",
        "jsonschema"
    ],
    python_requires='>=3.7',
) 