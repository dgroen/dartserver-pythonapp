"""Setup script for dartserver-pythonapp."""

from setuptools import find_packages, setup

setup(
    name="dartserver-pythonapp",
    version="1.0.0",
    packages=find_packages(exclude=["tests", "tests.*", "examples", "examples.*"]),
    include_package_data=True,
)
