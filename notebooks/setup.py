from setuptools import setup, find_packages

setup(
    name="webapp-starter-utils",
    version="0.1.0",
    description="Utility functions for webapp-starter notebooks",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "ray>=2.0.0",
        "jupyter",
        "ipython",
        "numpy",
        "pandas",
    ],
    package_data={
        'utils': ['*.py'],
    },
    include_package_data=True,
)