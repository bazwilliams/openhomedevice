import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="openhomedevice",
    version="2.5",
    author="Barry John Williams",
    author_email="barry@bjw.me.uk",
    description="Provides an API for requesting information from an Openhome device",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/bazwilliams/openhomedevice",
    project_urls={
        "Source": "https://github.com/bazwilliams/openhomedevice",
        "Release notes": "https://github.com/bazwilliams/openhomedevice/releases",
    },
    packages=setuptools.find_packages(exclude=["tests", "tools"]),
    keywords=["upnp", "dlna", "openhome", "linn", "ds", "music", "render", "async"],
    install_requires=["async_upnp_client>=0.40"],
    license="MIT",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
        "Topic :: Multimedia :: Sound/Audio",
    ],
    python_requires=">=3.10",
)
