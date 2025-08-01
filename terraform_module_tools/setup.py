from setuptools import setup, find_packages

setup(
    name="terraform-module-tools",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "kubiya_workflow_sdk[tools]",
        "requests",
        "typing",
        "logging",
    ],
    entry_points={
        'console_scripts': [
            'terraform-module-tools=terraform_module_tools:main',
        ],
    },
    author="Your Name",
    author_email="your.email@example.com",
    description="Terraform module and terraformer tools for Kubiya",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/terraform-module-tools",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
) 