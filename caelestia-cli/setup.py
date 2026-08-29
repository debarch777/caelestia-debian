import os
from setuptools import setup, find_packages

def find_package_data():
    data_files = []
    base_dir = os.path.join("src", "caelestia", "data")
    for root, _, files in os.walk(base_dir):
        for f in files:
            rel_path = os.path.relpath(os.path.join(root, f), os.path.join("src", "caelestia"))
            data_files.append(rel_path)
    return data_files

setup(
    name="caelestia",
    version="1.1.3",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    package_data={
        "caelestia": find_package_data(),
    },
    include_package_data=True,
    install_requires=[
        "pillow",
        "materialyoucolor",
    ],
    entry_points={
        "console_scripts": [
            "caelestia=caelestia:main",
        ],
    },
)
