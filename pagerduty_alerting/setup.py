from setuptools import setup, find_packages

setup(
    name='pagerduty_alerting',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'kubiya_sdk',
    ],
)
