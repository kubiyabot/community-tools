from setuptools import setup, find_packages

setup(
    name="report-tool",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "requests>=2.0",
        "boto3>=1.38.0",
        "kubiya-sdk",
    ],
    entry_points={
        'console_scripts': [
            'create_es_watchers=report_tool.tools.report:create_es_watchers',
        ],
    },
)