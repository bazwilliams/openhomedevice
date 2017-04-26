from distutils.core import setup
setup(
  name = 'openhomedevice',
  packages = ['openhomedevice'],
  version = '0.2.2',
  description = 'Provides an API for requesting information from an Openhome device',
  author = 'Barry John Williams',
  author_email = 'barry@bjw.me.uk',
  url = 'https://github.com/cak85/openhomedevice',
  download_url = 'https://github.com/cak85/openhomedevice/tarball/0.2.2',
  keywords = ['upnp', 'dlna', 'openhome', 'linn', 'ds', 'music', 'render'],
  install_requires = ['requests', 'lxml'],
  classifiers = [],
)
