from setuptools import setup, find_packages

setup(
    name="terraform_module_tools",
    version="0.1.0",
    packages=find_packages(),
    package_data={
        'terraform_module_tools.scripts': [
            'terraformer.sh',
            'terraformer_commands.py',
            'wrapper.sh',
            'former2.sh',
            'conversion_runtime.py'
        ]
    },
    install_requires=[
        "kubiya-sdk",
        "boto3",
    ],
) 