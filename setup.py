import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
  name = 'openhomedevice',
  version = '1.1.0',
  author = 'Barry John Williams',
  author_email = 'barry@bjw.me.uk',
  description='Provides an API for requesting information from an Openhome device',
  long_description=long_description,
  long_description_content_type="text/markdown",
  url='https://github.com/bazwilliams/openhomedevice',
  packages=setuptools.find_packages(),
  download_url = 'https://github.com/bazwilliams/openhomedevice/tarball/1.1.0',
  keywords = ['upnp', 'dlna', 'openhome', 'linn', 'ds', 'music', 'render', 'async'],
  install_requires = ['async_upnp_client>=0.16.1', 'lxml>=4.6.3'],
      classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6'
)
