from setuptools import find_packages, setup

setup(
    name="incc_shared",
    version="0.1.0",
    description="Shared code for incc-app",
    packages=find_packages(),
    install_requires=["pydantic"],
    python_requires=">=3.8",
)
