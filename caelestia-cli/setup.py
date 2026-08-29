from setuptools import setup, find_packages

setup(
    name="caelestia",
    version="1.0.0",
    description="Main control utility and theming engine for Caelestia Desktop",
    author="caelestia-dots",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    package_data={
        "caelestia": [
            "data/*",
            "data/**/*",
            "data/emojis.txt",
            "data/schemes/**/*",
            "data/templates/*",
        ]
    },
    include_package_data=True,
    entry_points={
        "console_scripts": [
            "caelestia=caelestia:main",
        ],
    },
    install_requires=[
        "pillow",
        "materialyoucolor",
    ],
    python_requires=">=3.10",
)
