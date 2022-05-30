from setuptools import setup, find_packages  # type: ignore

setup(
    name="vessel",
    version="0.1.0",
    description="Fluent chainable interface for container data types",
    url="https://github.com/griendt/vessel",
    author="Alex van de Griendt",
    author_email="alex@e-cube.nl",
    classifiers=[
        "Development Status :: 1 - Development",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    keywords="collection, fluent, development",
    packages=find_packages(),
    python_requires=">=3.7, <4",
    install_requires=[],
    extras_require={
        "test": ["coverage"],
    },
)
