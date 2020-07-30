import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="voice-control-framework-Valgrindo",
    version="0.0b1",
    author="Sergey Goldobin",
    author_email="sergejgoldobin081096@gmail.com",
    description="Customizable voice control integration framework.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Valgrindo/Capstone",
    packages=setuptools.find_packages(),
    install_requires=[
        'bs4',                  # Used for all XML parsing.
        'requests',
        'keyboard',             # Until module support
        'google-cloud-speech',  # Used in speech recognition
        'soundfile',            # """
        'sounddevice'           # """
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Information Technology"
    ],
    python_requires='>=3.6',
    include_package_data=True   # Include test data and configuration files.
)
