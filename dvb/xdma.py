# pylint: disable=missing-docstring

import atexit
import logging
import mmap
import re
import subprocess as subp
from multiprocessing import Lock

_logger = logging.getLogger(__name__)

_RE_READ = re.compile(
    b"Read 32-bit value at address .*?: 0x(?P<data>[0-9a-f]+)", flags=re.M
)


class BaseMemoryRegion:
    _fd = open("/dev/xdma0_user", "wb")
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
            fileno=self._fd.fileno(),
            length=length,
            offset=base_addr,
            access=mmap.MAP_SHARED,
            prot=mmap.PROT_WRITE | mmap.PROT_READ,
        )

        self._write(0, 0)

    #  map_base = mmap(0, MAP_SIZE, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);

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


# def run(cmd):
#     _logger.log(5, "$ %s", " ".join(map(str, cmd)))
#     try:
#         return subp.check_output(cmd, stderr=subp.STDOUT)
#     except subp.CalledProcessError as error:
#         #  _logger.log(5, "Failed to run '%s'", " ".join(map(str, cmd)))
#         return error.output


# def _poke(addr: int, data: int):
#     run(
#         (
#             "/home/souto/dev/dma_ip_drivers/XDMA/linux-kernel/tools/reg_rw",
#             "/dev/xdma0_user",
#             f"0x{addr:x}",
#             "w",
#             f"0x{data:x}",
#         )
#     )


# def _peek(addr: int) -> int:
#     result = run(
#         (
#             "/home/souto/dev/dma_ip_drivers/XDMA/linux-kernel/tools/reg_rw",
#             "/dev/xdma0_user",
#             f"0x{addr:x}",
#             "w",
#         )
#     )

#     match = _RE_READ.search(result)
#     assert (
#         match is not None
#     ), f"Failed to interpret result for reading 0x{addr:X}: {result}"

#     return int(match.groupdict()["data"], 16)


# class BaseMemoryRegion:
#     def __init__(self, base_addr, length):
#         _logger.info("Creating object for 0x%X, length is %d", base_addr, length)
#         self._base_addr = base_addr
#         self._length = length

#     def _write(self, addr: int, data: int):
#         assert not addr % 4, f"Address 0x{addr:08X} is not aligned to 4 bytes"
#         _logger.log(5, "W @ 0x%.8X: 0x%.8X", self._base_addr + addr, data)
#         _poke(self._base_addr + addr, data)

#     def _read(self, addr) -> int:
#         assert not addr % 4, f"Address 0x{addr:08X} is not aligned to 4 bytes"
#         data = _peek(self._base_addr + addr)
#         _logger.log(5, "R @ 0x%.8X: 0x%.8X", self._base_addr + addr, data)
#         return data
