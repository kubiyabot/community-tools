from setuptools import setup, find_packages

setup(
    name="kubiya-jenkins-ops",
    version="0.1.0",
    packages=find_packages(),
    package_data={
        'jenkins_ops': [
            'scripts/configs/*.json',
            'scripts/housekeeping/*.py',
        ],
    },
    include_package_data=True,
    install_requires=[
        "kubiya_sdk>=0.1.0",
        "requests>=2.25.0",
        "pyyaml>=5.4.1"
    ],
    entry_points={
        'kubiya.tools': [
            'jenkins_ops=jenkins_ops:discover'
        ]
    },
    python_requires=">=3.8",
) 