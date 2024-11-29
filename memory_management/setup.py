from setuptools import setup, find_packages

setup(
    name="memory_management",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "kubiya_sdk",
        "mem0ai[graph]==1.1.0",
        "langchain-community",
        "rank_bm25",
        "neo4j",
        "openai>=1.0.0"
    ],
) 