from setuptools import find_packages, setup

VERSION = "0.0.1"
DESCRIPTION = "MVS Camera conrol for python"
LONG_DESCRIPTION = " Setup tools using MVS software for asynchronous grab in python"

# Setting up
setup(
    # the name must match the folder name 'verysimplemodule'
    name="mvs_camera",
    version=VERSION,
    author="Mauricio Gonzalez",
    author_email="<ing.mauricioglez1409@outlook.com>",
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    packages=find_packages(),
    install_requires=[],  # add any additional packages that
    # needs to be installed along with your package. Eg: 'caer'
    keywords=["python", "first package"],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Development",
        "Programming Language :: Python :: 2",
        "Operating System :: Linux :: Linux",
    ],
)
