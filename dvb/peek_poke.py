# pylint: disable=missing-docstring

import logging
import subprocess as subp

_logger = logging.getLogger(__name__)


def run(cmd):
    _logger.debug("$ %s", " ".join(map(str, cmd)))
    try:
        return subp.check_output(cmd)
    except subp.SubprocessError:
        _logger.error("Failed to run '%s'", " ".join(map(str, cmd)))
        raise


def _poke(addr: int, data: int):
    run(("poke", "0x%.8X" % addr, "0x%.8X" % data))


def _peek(addr: int) -> int:
    assert (addr >> 16) & 0xFF in (0xC0, 0xC1, 0xC2), f"Invalid address 0x{addr:X}"
    result = run(("peek", "0x%8X" % addr)).strip()
    return int(result, 16)


class BaseMemoryRegion:
    def __init__(self, base_addr, length):
        _logger.info("Creating object for 0x%X, length is %d", base_addr, length)
        self._base_addr = base_addr
        self._length = length

    def _write(self, addr: int, data: int):
        _poke(self._base_addr + addr, data)

    def _read(self, addr) -> int:
        return _peek(self._base_addr + addr)
