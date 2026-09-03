"""Exceptions raised by openhomedevice.

Callers only need to catch these. The underlying async_upnp_client and
aiohttp exception types are translated at the boundary of this library so
they do not leak into consuming code, which would otherwise have to import
async_upnp_client purely to catch a failed request.
"""


class OpenhomeError(Exception):
    """Base class for every error raised by this library."""


class OpenhomeConnectionError(OpenhomeError):
    """The device could not be reached.

    Raised when the device is off, on standby with the network interface
    down, or otherwise not answering on the network.
    """


class OpenhomeTimeoutError(OpenhomeConnectionError):
    """The device did not answer in time.

    A subclass of OpenhomeConnectionError, so callers that do not care why
    the device was unreachable can catch the one exception.
    """


class OpenhomeDeviceError(OpenhomeError):
    """The device answered, but rejected the request or replied unusably.

    Covers a SOAP fault from the device, an HTTP error status, and a
    response whose XML could not be understood.
    """
