# pylint: disable=missing-docstring

import logging
import os
import platform
import subprocess as subp
from enum import Enum

_logger = logging.getLogger(__name__)
IS_ARM = "armv7l" in os.uname()
IS_ODYSSEY = platform.node() == "odyssey"

if IS_ARM:
    if os.environ.get("FORCE_PEEKPOKE", None) is not None:
        from dvb.arm import BaseMemoryRegion
    else:
        from dvb.peek_poke import BaseMemoryRegion
elif IS_ODYSSEY:
    from dvb.xdma import BaseMemoryRegion
else:
    from dvb.fake_access import BaseMemoryRegion


def run(cmd):
    _logger.debug("$ %s", " ".join(map(str, cmd)))
    try:
        return subp.check_output(cmd)
    except subp.SubprocessError:
        _logger.error("Failed to run '%s'", " ".join(map(str, cmd)))
        raise


def tabulate(table):
    widths = {}
    for line in table:
        for i, row in enumerate(line):
            widths[i] = max(widths.get(i, 0), len(str(row)))

    result = []
    for line in table:
        current_line = []
        for i, row in enumerate(line):
            current_line.append(str(row).ljust(widths[i]))
        result.append(current_line)

    return result


class ConstellationType(Enum):
    """
    Constellation types as defined in the DVB-S2 spec. Enum names should match
    the C/C++ defines, values are a nice string representation for the test
    names.
    """

    MOD_QPSK = "QPSK"
    MOD_8PSK = "8PSK"
    MOD_16APSK = "16APSK"
    MOD_32APSK = "32APSK"


class FrameType(Enum):
    """
    Frame types as defined in the DVB-S2 spec. Enum names should match
    the C/C++ defines, values are a nice string representation for the test
    names.
    """

    FECFRAME_NORMAL = "normal"
    FECFRAME_SHORT = "short"


class CodeRate(Enum):
    """
    Code rates as defined in the DVB-S2 spec. Enum names should match the C/C++
    defines, values are a nice string representation for the test names.
    """

    C1_4 = "1/4"
    C1_3 = "1/3"
    C2_5 = "2/5"
    C1_2 = "1/2"
    C3_5 = "3/5"
    C2_3 = "2/3"
    C3_4 = "3/4"
    C4_5 = "4/5"
    C5_6 = "5/6"
    C8_9 = "8/9"
    C9_10 = "9/10"


TID_MAP = {
    FrameType.FECFRAME_SHORT: {
        ConstellationType.MOD_QPSK: {
            CodeRate.C1_4: 0x00,
            CodeRate.C1_3: 0x01,
            CodeRate.C2_5: 0x02,
            CodeRate.C1_2: 0x03,
            CodeRate.C3_5: 0x04,
            CodeRate.C2_3: 0x05,
            CodeRate.C3_4: 0x06,
            CodeRate.C4_5: 0x07,
            CodeRate.C5_6: 0x08,
            CodeRate.C8_9: 0x09,
            CodeRate.C9_10: 0x0A,
        },
        ConstellationType.MOD_8PSK: {
            CodeRate.C1_4: 0x0B,
            CodeRate.C1_3: 0x0C,
            CodeRate.C2_5: 0x0D,
            CodeRate.C1_2: 0x0E,
            CodeRate.C3_5: 0x0F,
            CodeRate.C2_3: 0x10,
            CodeRate.C3_4: 0x11,
            CodeRate.C4_5: 0x12,
            CodeRate.C5_6: 0x13,
            CodeRate.C8_9: 0x14,
            CodeRate.C9_10: 0x15,
        },
        ConstellationType.MOD_16APSK: {
            CodeRate.C1_4: 0x16,
            CodeRate.C1_3: 0x17,
            CodeRate.C2_5: 0x18,
            CodeRate.C1_2: 0x19,
            CodeRate.C3_5: 0x1A,
            CodeRate.C2_3: 0x1B,
            CodeRate.C3_4: 0x1C,
            CodeRate.C4_5: 0x1D,
            CodeRate.C5_6: 0x1E,
            CodeRate.C8_9: 0x1F,
            CodeRate.C9_10: 0x20,
        },
        ConstellationType.MOD_32APSK: {
            CodeRate.C1_4: 0x21,
            CodeRate.C1_3: 0x22,
            CodeRate.C2_5: 0x23,
            CodeRate.C1_2: 0x24,
            CodeRate.C3_5: 0x25,
            CodeRate.C2_3: 0x26,
            CodeRate.C3_4: 0x27,
            CodeRate.C4_5: 0x28,
            CodeRate.C5_6: 0x29,
            CodeRate.C8_9: 0x2A,
            CodeRate.C9_10: 0x2B,
        },
    },
    FrameType.FECFRAME_NORMAL: {
        ConstellationType.MOD_QPSK: {
            CodeRate.C1_4: 0x2C,
            CodeRate.C1_3: 0x2D,
            CodeRate.C2_5: 0x2E,
            CodeRate.C1_2: 0x2F,
            CodeRate.C3_5: 0x30,
            CodeRate.C2_3: 0x31,
            CodeRate.C3_4: 0x32,
            CodeRate.C4_5: 0x33,
            CodeRate.C5_6: 0x34,
            CodeRate.C8_9: 0x35,
            CodeRate.C9_10: 0x36,
        },
        ConstellationType.MOD_8PSK: {
            CodeRate.C1_4: 0x37,
            CodeRate.C1_3: 0x38,
            CodeRate.C2_5: 0x39,
            CodeRate.C1_2: 0x3A,
            CodeRate.C3_5: 0x3B,
            CodeRate.C2_3: 0x3C,
            CodeRate.C3_4: 0x3D,
            CodeRate.C4_5: 0x3E,
            CodeRate.C5_6: 0x3F,
            CodeRate.C8_9: 0x40,
            CodeRate.C9_10: 0x41,
        },
        ConstellationType.MOD_16APSK: {
            CodeRate.C1_4: 0x42,
            CodeRate.C1_3: 0x43,
            CodeRate.C2_5: 0x44,
            CodeRate.C1_2: 0x45,
            CodeRate.C3_5: 0x46,
            CodeRate.C2_3: 0x47,
            CodeRate.C3_4: 0x48,
            CodeRate.C4_5: 0x49,
            CodeRate.C5_6: 0x4A,
            CodeRate.C8_9: 0x4B,
            CodeRate.C9_10: 0x4C,
        },
        ConstellationType.MOD_32APSK: {
            CodeRate.C1_4: 0x4D,
            CodeRate.C1_3: 0x4E,
            CodeRate.C2_5: 0x4F,
            CodeRate.C1_2: 0x50,
            CodeRate.C3_5: 0x51,
            CodeRate.C2_3: 0x52,
            CodeRate.C3_4: 0x53,
            CodeRate.C4_5: 0x54,
            CodeRate.C5_6: 0x55,
            CodeRate.C8_9: 0x56,
            CodeRate.C9_10: 0x57,
        },
    },
}
__all__ = ["tabulate", "BaseMemoryRegion", "ConstellationType"]
