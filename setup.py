import os
from setuptools import setup, find_packages

def read_requirements():
    indir = lambda fname: os.path.join(os.path.dirname(__file__), fname)
    with open(indir("requirements.txt"), "r") as f:
        return [line.strip() for line in f.readlines() if line.strip and \
                not line.startswith("#")]

setup(
    name="MA2006B-FJ26",
    version="0.1",
    description="Reto of the MA2006B course FJ26",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/A01831983/MA2006B_Reto",
    package_dir={"": "src"},
    install_requires=read_requirements(),
    python_requires=">=3.6"
)
