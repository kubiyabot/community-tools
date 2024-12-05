from setuptools import setup, find_packages

setup(
    name="k8s_tools",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "kubernetes>=12.0.0",
        "PyYAML>=5.1",
        "requests>=2.25.0",
    ],
    package_data={
        'k8s_tools': [
            'config/*.yaml',
            'templates/*.sh',
            'templates/insights/*.sh'
        ],
    },
    python_requires='>=3.7',
)
