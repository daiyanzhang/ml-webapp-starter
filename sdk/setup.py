from setuptools import setup, find_packages

setup(
    name="webapp-starter-sdk",
    version="0.1.0",
    description="SDK utilities for webapp-starter project",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "ray>=2.0.0",
        "jupyter",
        "ipython",
        "numpy",
        "pandas",
    ],
    include_package_data=True,
)