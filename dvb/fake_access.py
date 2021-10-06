# pylint: disable=missing-docstring

import logging
from multiprocessing import Lock

_logger = logging.getLogger(__name__)

DATA = {}


def _dictWrite(addr: int, data: int):
    DATA[addr] = data


def _dictRead(addr: int) -> int:
    assert (addr >> 16) & 0xFF in (0xC0, 0xC1, 0xC2), f"Invalid address 0x{addr:X}"
    data = DATA.get(addr, 0)
    return data


class BaseMemoryRegion:
    _lock = Lock()
    _logger = logging.getLogger(__name__)

    def __init__(self, base_addr, length):
        _logger.info("Creating object for 0x%X, length is %d", base_addr, length)
        self._base_addr = base_addr
        self._length = length

    def _write(self, addr: int, data: int):
        self._logger.debug("W 0x%.8X <= 0x%.8X", addr, data)
        with self._lock:
            _dictWrite(self._base_addr + addr, data)

    def _read(self, addr: int) -> int:
        with self._lock:
            data = _dictRead(self._base_addr + addr)
        self._logger.debug("R 0x%.8X => 0x%.8X", addr, data)
        return data
