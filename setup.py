import setuptools

from rs2wapy import __version__

setuptools.setup(
    name="rs2wapy",
    version=__version__,
    packages=setuptools.find_packages(),
    url="https://github.com/tuokri/rs2wapy",
    author="tuokri",
    author_email="tuokri@tuta.io",
    description="Rising Storm 2: Vietnam WebAdmin Python Interface",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    install_requires=[
        "beautifulsoup4",
        "bs4",
        "Logbook",
        "pycurl",
        "rs2wapy",
        "soupsieve",

    ]
)
