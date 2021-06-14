"""Make it an editable package"""

from setuptools import setup

setup(
    name="prepavol",
    version="3.1",
    author="Yannick Teresiak",
    author_email="yannick.teresiak@gmail.com",
    url="https://gitlab.com/yannick.teresiak/flaskapp",
    license="GPLv3",
    license_file="COPYING",
    description="Web app for light aviation flight preparation",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    install_requires=[
        "flask",
        "flask_session",
        "flask_wtf",
        "jsonpickle",
        "lxml",
        "pandas",
        "numpy",
        "pytest-timeout",
        "pyyaml",
        "bs4",
        "requests",
        "matplotlib",
        "shapely",
        "sklearn",
    ],
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    include_package_data=True,
    packages=["prepavol", "tests"],
    zip_safe=False,
    python_requires=">=3.7",
)
