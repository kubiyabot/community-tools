from setuptools import setup, find_packages

setup(
    name="serverless_mcp_metatool",
    version="0.1.0",
    packages=find_packages(),
    description="A Kubiya meta-tool to discover and define tools from FastMCP servers.",
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author="Your Name",
    author_email="your.email@example.com",
    install_requires=[
        "kubiya-sdk>=0.1.0", 
    ],
    entry_points={
        'kubiya_tools': [
            'serverless_mcp_discover = serverless_mcp:get_tools',
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8',
) 