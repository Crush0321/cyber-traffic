from setuptools import setup, find_packages

setup(
    name="cyber-traffic",
    version="0.1.0",
    packages=find_packages(),
    install_requires=["rumps>=0.4.0"],
    entry_points={
        "console_scripts": [
            "cyber-traffic=cyber_traffic.app:main",
        ],
    },
    python_requires=">=3.9",
)
