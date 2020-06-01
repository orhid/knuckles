with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="knuckles-orhid", # Replace with your own username
    version="0.1.0",
    author="Filip Przybycień",
    author_email="fprzybycien@gmail.com",
    description="simple library for data sonification",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/orhid/knuckles",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
