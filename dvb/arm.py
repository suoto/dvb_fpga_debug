# pylint: disable=missing-docstring

import atexit
import logging
import mmap
from multiprocessing import Lock

_logger = logging.getLogger(__name__)


class BaseMemoryRegion:
    _fd = open("/dev/mem", "r+b")
    _lock = Lock()

    @staticmethod
    @atexit.register
    def closeIoMem():
        _logger.info("Closing /dev/mem file pointer")
        BaseMemoryRegion._fd.close()

    def __init__(self, base_addr, length):
        _logger.info("Creating object for 0x%X, length is %d", base_addr, length)
        self._base_addr = base_addr
        self._length = length
        self._mmap = mmap.mmap(
            fileno=self._fd.fileno(), length=length, offset=base_addr
        )

    def _write(self, addr: int, data: int):
        with self._lock:
            _logger.debug("W @ 0x%.8X: 0x%.8X", self._base_addr + addr, data)
            try:
                self._mmap.seek(addr)
                self._mmap.write(data.to_bytes(4, "little"))
            except:
                _logger.error("Failed to write to 0x%.8X", addr)
                raise

    def _read(self, addr: int) -> int:
        with self._lock:
            #  _logger.debug("R @ 0x%.8X: ?", self._base_addr + addr)
            try:
                self._mmap.seek(addr)
                data = int.from_bytes(self._mmap.read(4), "little")
            except:
                _logger.error("Failed to read from 0x%.8X", addr)
                raise
            _logger.debug("R @ 0x%.8X: 0x%.8X", self._base_addr + addr, data)
            return data
