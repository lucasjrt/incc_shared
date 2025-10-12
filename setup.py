from setuptools import find_packages, setup

setup(
    name="incc_shared",
    version="0.0.1",
    description="Shared code for incc-app",
    packages=find_packages(),
    install_requires=[
        # runtime deps here, e.g. "requests>=2.0"
    ],
    python_requires=">=3.8",
)
