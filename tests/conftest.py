import inspect
from unittest.mock import Mock

from aiohttp import ClientResponse

# aioresponses builds an aiohttp ClientResponse by hand, and aiohttp 3.14 added
# a required stream_writer argument to its constructor, so every mocked request
# raises TypeError. aiohttp only reads stream_writer.output_size, so default it
# to a stand-in. Remove this once aioresponses supports aiohttp 3.14
# (pnuckowski/aioresponses#288).
if "stream_writer" in inspect.signature(ClientResponse.__init__).parameters:
    _init = ClientResponse.__init__

    def _init_with_stream_writer(self, *args, stream_writer=None, **kwargs):
        if stream_writer is None:
            stream_writer = Mock(output_size=0)
        _init(self, *args, stream_writer=stream_writer, **kwargs)

    ClientResponse.__init__ = _init_with_stream_writer
