# pylint: disable=missing-docstring
# pylint: disable=invalid-name
# type: ignore

import logging
import math
from collections import namedtuple

from common import (BaseMemoryRegion, CodeRate, ConstellationType, FrameType,
                    tabulate)

AxiInterface = namedtuple("AxiInterface", ("slave", "master"))
Strobes = namedtuple("Strobes", ("tvalid", "tready"))
FrameLengths = namedtuple("FrameLengths", ("max", "min"))


def toFixedPoint(value, width):
    value = round(((1 << width - 1) - 1) * value)
    if value >= 0:
        return value
    return value + (1 << width)


def _getModulationTable(
    frame_type: FrameType, constellation: ConstellationType, code_rate: CodeRate
):
    """
    Returns the modulation table for a given config. Please note we're scaling the
    import math
    constellation radius according to the old implementation of GNU Radio.  Once the CI's
    GNU Radio version is updated to include
    https://github.com/gnuradio/gnuradio/commit/efe3e6c1 we'll need to change here as well
    """
    # pylint: disable=invalid-name
    if constellation == ConstellationType.MOD_QPSK:
        return (
            # QPSK
            (math.cos(math.pi / 4.0), math.sin(math.pi / 4.0)),
            (math.cos(7 * math.pi / 4.0), math.sin(7 * math.pi / 4.0)),
            (math.cos(3 * math.pi / 4.0), math.sin(3 * math.pi / 4.0)),
            (math.cos(5 * math.pi / 4.0), math.sin(5 * math.pi / 4.0)),
        )

    if constellation == ConstellationType.MOD_8PSK:
        return (
            (math.cos(math.pi / 4.0), math.sin(math.pi / 4.0)),
            (math.cos(0.0), math.sin(0.0)),
            (math.cos(4 * math.pi / 4.0), math.sin(4 * math.pi / 4.0)),
            (math.cos(5 * math.pi / 4.0), math.sin(5 * math.pi / 4.0)),
            (math.cos(2 * math.pi / 4.0), math.sin(2 * math.pi / 4.0)),
            (math.cos(7 * math.pi / 4.0), math.sin(7 * math.pi / 4.0)),
            (math.cos(3 * math.pi / 4.0), math.sin(3 * math.pi / 4.0)),
            (math.cos(6 * math.pi / 4.0), math.sin(6 * math.pi / 4.0)),
        )

    if constellation == ConstellationType.MOD_16APSK:
        r1 = 1.0
        r2 = 1.0
        if frame_type == FrameType.FECFRAME_NORMAL:
            r1 = {
                CodeRate.C2_3: r2 / 3.15,
                CodeRate.C3_4: r2 / 2.85,
                CodeRate.C4_5: r2 / 2.75,
                CodeRate.C5_6: r2 / 2.70,
                CodeRate.C8_9: r2 / 2.60,
                CodeRate.C9_10: r2 / 2.57,
                CodeRate.C3_5: r2 / 3.70,
            }.get(code_rate, 0.0)
        elif frame_type == FrameType.FECFRAME_SHORT:
            r1 = {
                CodeRate.C2_3: r2 / 3.15,
                CodeRate.C3_4: r2 / 2.85,
                CodeRate.C4_5: r2 / 2.75,
                CodeRate.C5_6: r2 / 2.70,
                CodeRate.C8_9: r2 / 2.60,
                CodeRate.C3_5: r2 / 3.70,
            }.get(code_rate, 0.0)

        # TODO: Include this when changing CI's GNU Radio version to a version
        # that includes https://github.com/gnuradio/gnuradio/commit/efe3e6c1
        #  r0 = math.sqrt(4.0 / ((r1 * r1) + 3.0 * (r2 * r2)))
        #  r1 = r0 * r1
        #  r2 = r0 * r2

        return (
            (r2 * math.cos(math.pi / 4.0), r2 * math.sin(math.pi / 4.0)),
            (r2 * math.cos(-math.pi / 4.0), r2 * math.sin(-math.pi / 4.0)),
            (r2 * math.cos(3 * math.pi / 4.0), r2 * math.sin(3 * math.pi / 4.0)),
            (r2 * math.cos(-3 * math.pi / 4.0), r2 * math.sin(-3 * math.pi / 4.0)),
            (r2 * math.cos(math.pi / 12.0), r2 * math.sin(math.pi / 12.0)),
            (r2 * math.cos(-math.pi / 12.0), r2 * math.sin(-math.pi / 12.0)),
            (r2 * math.cos(11 * math.pi / 12.0), r2 * math.sin(11 * math.pi / 12.0)),
            (r2 * math.cos(-11 * math.pi / 12.0), r2 * math.sin(-11 * math.pi / 12.0)),
            (r2 * math.cos(5 * math.pi / 12.0), r2 * math.sin(5 * math.pi / 12.0)),
            (r2 * math.cos(-5 * math.pi / 12.0), r2 * math.sin(-5 * math.pi / 12.0)),
            (r2 * math.cos(7 * math.pi / 12.0), r2 * math.sin(7 * math.pi / 12.0)),
            (r2 * math.cos(-7 * math.pi / 12.0), r2 * math.sin(-7 * math.pi / 12.0)),
            (r1 * math.cos(math.pi / 4.0), r1 * math.sin(math.pi / 4.0)),
            (r1 * math.cos(-math.pi / 4.0), r1 * math.sin(-math.pi / 4.0)),
            (r1 * math.cos(3 * math.pi / 4.0), r1 * math.sin(3 * math.pi / 4.0)),
            (r1 * math.cos(-3 * math.pi / 4.0), r1 * math.sin(-3 * math.pi / 4.0)),
        )

    if constellation == ConstellationType.MOD_32APSK:
        r1 = 1.0
        r2 = 1.0
        r3 = 1.0
        r1 = {
            CodeRate.C3_4: r3 / 5.27,
            CodeRate.C4_5: r3 / 4.87,
            CodeRate.C5_6: r3 / 4.64,
            CodeRate.C8_9: r3 / 4.33,
            CodeRate.C9_10: r3 / 4.30,
        }.get(code_rate, 0.0)

        r2 = {
            CodeRate.C3_4: r1 * 2.84,
            CodeRate.C4_5: r1 * 2.72,
            CodeRate.C5_6: r1 * 2.64,
            CodeRate.C8_9: r1 * 2.54,
            CodeRate.C9_10: r1 * 2.53,
        }.get(code_rate, 0.0)

        # TODO: Include this when changing CI's GNU Radio version to a version
        # that includes https://github.com/gnuradio/gnuradio/commit/efe3e6c1
        #  r0 = math.sqrt(8.0 / ((r1 * r1) + 3.0 * (r2 * r2) + 4.0 * (r3 * r3)))
        #  r1 *= r0
        #  r2 *= r0
        #  r3 *= r0
        return (
            (r2 * math.cos(math.pi / 4.0), r2 * math.sin(math.pi / 4.0)),
            (r2 * math.cos(5 * math.pi / 12.0), r2 * math.sin(5 * math.pi / 12.0)),
            (r2 * math.cos(-math.pi / 4.0), r2 * math.sin(-math.pi / 4.0)),
            (
                r2 * math.cos(-5 * math.pi / 12.0),
                r2 * math.sin(-5 * math.pi / 12.0),
            ),
            (r2 * math.cos(3 * math.pi / 4.0), r2 * math.sin(3 * math.pi / 4.0)),
            (r2 * math.cos(7 * math.pi / 12.0), r2 * math.sin(7 * math.pi / 12.0)),
            (r2 * math.cos(-3 * math.pi / 4.0), r2 * math.sin(-3 * math.pi / 4.0)),
            (
                r2 * math.cos(-7 * math.pi / 12.0),
                r2 * math.sin(-7 * math.pi / 12.0),
            ),
            (r3 * math.cos(math.pi / 8.0), r3 * math.sin(math.pi / 8.0)),
            (r3 * math.cos(3 * math.pi / 8.0), r3 * math.sin(3 * math.pi / 8.0)),
            (r3 * math.cos(-math.pi / 4.0), r3 * math.sin(-math.pi / 4.0)),
            (r3 * math.cos(-math.pi / 2.0), r3 * math.sin(-math.pi / 2.0)),
            (r3 * math.cos(3 * math.pi / 4.0), r3 * math.sin(3 * math.pi / 4.0)),
            (r3 * math.cos(math.pi / 2.0), r3 * math.sin(math.pi / 2.0)),
            (r3 * math.cos(-7 * math.pi / 8.0), r3 * math.sin(-7 * math.pi / 8.0)),
            (r3 * math.cos(-5 * math.pi / 8.0), r3 * math.sin(-5 * math.pi / 8.0)),
            (r2 * math.cos(math.pi / 12.0), r2 * math.sin(math.pi / 12.0)),
            (r1 * math.cos(math.pi / 4.0), r1 * math.sin(math.pi / 4.0)),
            (r2 * math.cos(-math.pi / 12.0), r2 * math.sin(-math.pi / 12.0)),
            (r1 * math.cos(-math.pi / 4.0), r1 * math.sin(-math.pi / 4.0)),
            (
                r2 * math.cos(11 * math.pi / 12.0),
                r2 * math.sin(11 * math.pi / 12.0),
            ),
            (r1 * math.cos(3 * math.pi / 4.0), r1 * math.sin(3 * math.pi / 4.0)),
            (
                r2 * math.cos(-11 * math.pi / 12.0),
                r2 * math.sin(-11 * math.pi / 12.0),
            ),
            (r1 * math.cos(-3 * math.pi / 4.0), r1 * math.sin(-3 * math.pi / 4.0)),
            (r3 * math.cos(0.0), r3 * math.sin(0.0)),
            (r3 * math.cos(math.pi / 4.0), r3 * math.sin(math.pi / 4.0)),
            (r3 * math.cos(-math.pi / 8.0), r3 * math.sin(-math.pi / 8.0)),
            (r3 * math.cos(-3 * math.pi / 8.0), r3 * math.sin(-3 * math.pi / 8.0)),
            (r3 * math.cos(7 * math.pi / 8.0), r3 * math.sin(7 * math.pi / 8.0)),
            (r3 * math.cos(5 * math.pi / 8.0), r3 * math.sin(5 * math.pi / 8.0)),
            (r3 * math.cos(math.pi), r3 * math.sin(math.pi)),
            (r3 * math.cos(-3 * math.pi / 4.0), r3 * math.sin(-3 * math.pi / 4.0)),
        )

    # pylint: enable=invalid-name

    return ()


class AxiDebug:
    def __init__(self, write, read):
        self._write = write
        self._read = read
        self.word_count = 0
        self.max_frame_length = None
        self.min_frame_length = None
        self._logger = logging.getLogger("AxiDebug")

    def update(self):
        self.word_count = self.getWordCount()
        lengths = self.getFrameLengths()
        self.max_frame_length = lengths.max
        self.min_frame_length = lengths.min

        #  if self.max_frame_length is None:
        #      self.max_frame_length = lengths.max
        #  else:
        #      self.max_frame_length = max(self.max_frame_length, lengths.max)

        #  if self.min_frame_length is None:
        #      self.min_frame_length = lengths.min
        #  else:
        #      self.min_frame_length = min(self.min_frame_length, lengths.min)

    def clear(self):
        self.word_count = 0
        self.max_frame_length = None
        self.min_frame_length = None

    @property
    def block_data(self):
        return self._read(0) & 1

    @block_data.setter
    def block_data(self, value):
        current = self._read(0)
        self._write(0, current & ~1 | value & 1)

    @property
    def allow_word(self):
        return (self._read(0) >> 1) & 1

    @allow_word.setter
    def allow_word(self, value):
        current = self._read(0)
        self._write(0, current & ~2 | (value & 1) << 1)

    @property
    def allow_frame(self):
        return (self._read(0) >> 2) & 1

    @allow_frame.setter
    def allow_frame(self, value):
        current = self._read(0)
        self._write(0, current & ~4 | (value & 1) << 2)

    def getFrameCount(self):
        return self._read(0x4)

    def getLastFrameLength(self):
        return self._read(0x8)

    def getFrameLengths(self):
        value = self._read(0xC)
        return FrameLengths(
            max=(value >> 16) & ((1 << 16) - 1), min=value & ((1 << 16) - 1)
        )

    def getWordCount(self):
        return self._read(0x10)

    def getStrobes(self):
        strobes = self._read(0x14)
        s_tvalid = strobes & 1
        s_tready = (strobes >> 1) & 1
        m_tvalid = (strobes >> 2) & 1
        m_tready = (strobes >> 3) & 1
        return AxiInterface(
            slave=Strobes(tvalid=s_tvalid, tready=s_tready),
            master=Strobes(tvalid=m_tvalid, tready=m_tready),
        )


class DvbEncoder(BaseMemoryRegion):
    def __init__(self, base_addr, length):
        super().__init__(base_addr, length)
        self._logger = logging.getLogger("DvbEncoder")

        self.input_width_converter = AxiDebug(
            write=lambda addr, data: self._write(addr + 0xD00, data),
            read=lambda addr: self._read(addr + 0xD00),
        )
        self.bb_scrambler = AxiDebug(
            write=lambda addr, data: self._write(addr + 0xE00, data),
            read=lambda addr: self._read(addr + 0xE00),
        )
        self.bch_encoder = AxiDebug(
            write=lambda addr, data: self._write(addr + 0xF00, data),
            read=lambda addr: self._read(addr + 0xF00),
        )
        self.ldpc_encoder = AxiDebug(
            write=lambda addr, data: self._write(addr + 0x1000, data),
            read=lambda addr: self._read(addr + 0x1000),
        )
        self.bit_interleaver = AxiDebug(
            write=lambda addr, data: self._write(addr + 0x1100, data),
            read=lambda addr: self._read(addr + 0x1100),
        )
        self.plframe = AxiDebug(
            write=lambda addr, data: self._write(addr + 0x1200, data),
            read=lambda addr: self._read(addr + 0x1200),
        )
        self.output = AxiDebug(
            write=lambda addr, data: self._write(addr + 0x1300, data),
            read=lambda addr: self._read(addr + 0x1300),
        )

    def write_polyphase_filter_coefficients(self):
        self._logger.info("Updating polyphase filter coefficients")
        self._write(0x3D0, 0x003C003C)
        self._write(0x3D4, 0xFFF6FFF6)
        self._write(0x3D8, 0xFFC8FFC8)
        self._write(0x3DC, 0x00410041)
        self._write(0x3E0, 0x000B000B)
        self._write(0x3E4, 0xFF75FF75)
        self._write(0x3E8, 0x00640064)
        self._write(0x3EC, 0x00E000E0)
        self._write(0x3F0, 0xFECAFECA)
        self._write(0x3F4, 0xFECBFECB)
        self._write(0x3F8, 0x02B702B7)
        self._write(0x3FC, 0x017D017D)
        self._write(0x400, 0xFA18FA18)
        self._write(0x404, 0xFE52FE52)
        self._write(0x408, 0x140B140B)
        self._write(0x40C, 0x21B621B6)
        self._write(0x410, 0x140B140B)
        self._write(0x414, 0xFE52FE52)
        self._write(0x418, 0xFA18FA18)
        self._write(0x41C, 0x017D017D)
        self._write(0x420, 0x02B702B7)
        self._write(0x424, 0xFECBFECB)
        self._write(0x428, 0xFECAFECA)
        self._write(0x42C, 0x00E000E0)
        self._write(0x430, 0x00640064)
        self._write(0x434, 0xFF75FF75)
        self._write(0x438, 0x000B000B)
        self._write(0x43C, 0x00410041)
        self._write(0x440, 0xFFC8FFC8)
        self._write(0x444, 0xFFF6FFF6)
        self._write(0x448, 0x003C003C)
        self._write(0x44C, 0xFFE8FFE8)

    def updateBitMapperRam(
        self,
        frame_type: FrameType,
        constellation: ConstellationType,
        code_rate: CodeRate,
    ):
        self._logger.info("Updating bit mapper RAM for %s", constellation)

        bit_mapper_ram_base_addr = 0x0C

        if constellation == ConstellationType.MOD_QPSK:
            addr = 0
        elif constellation == ConstellationType.MOD_8PSK:
            addr = 4
        elif constellation == ConstellationType.MOD_16APSK:
            addr = 12
        elif constellation == ConstellationType.MOD_32APSK:
            addr = 28
        else:
            assert False, f"Constellation {constellation} not supported"

        for offset, (cos, sin) in enumerate(
            _getModulationTable(frame_type, constellation, code_rate),
            addr,
        ):
            #  self._logger.info("Bit mapper RAM: %2d: % .3f, % .3f", offset, cos, sin)
            reg = (toFixedPoint(cos, 16) << 16) | toFixedPoint(sin, 16)
            self._write(bit_mapper_ram_base_addr + 4 * offset, reg)

    def init(self):
        self._logger.info("Initializing DVB encoder")
        self.write_polyphase_filter_coefficients()

    @property
    def physical_layer_scrambler_shift_reg_init(self) -> int:
        return (self._read(0x0) >> 0x0) & 0x3FFFF

    @physical_layer_scrambler_shift_reg_init.setter
    def physical_layer_scrambler_shift_reg_init(self, value: int):
        current = self._read(0x0)
        current = current & ~0x3FFFF | ((value & 0x3FFFF) << 0)
        return self._write(0x0, current)

    @property
    def enable_dummy_frames(self) -> int:
        return (self._read(0x0) >> 0x12) & 0x1

    @enable_dummy_frames.setter
    def enable_dummy_frames(self, value: int):
        current = self._read(0x0)
        current = current & ~0x40000 | ((value & 0x1) << 18)
        return self._write(0x0, current)

    def getLdpcFifoStatusLdpcFifoEntries(self) -> int:
        return (self._read(0x4) >> 0x0) & 0x3FFF

    def getLdpcFifoStatusLdpcFifoEmpty(self) -> int:
        return (self._read(0x4) >> 0x10) & 0x1

    def getLdpcFifoStatusLdpcFifoFull(self) -> int:
        return (self._read(0x4) >> 0x11) & 0x1

    def getFramesInTransit(self) -> int:
        return (self._read(0x8) >> 0x0) & 0xFF

    def getStatus(self):
        result = {
            "general": {
                "physical_layer_scrambler_shift_reg_init": self.physical_layer_scrambler_shift_reg_init,
                "enable_dummy_frames": self.enable_dummy_frames,
                "frames_in_transit": self.getFramesInTransit(),
            }
        }

        axi = {}

        for name in (
            "input_width_converter",
            "bb_scrambler",
            "bch_encoder",
            "ldpc_encoder",
            "bit_interleaver",
            "plframe",
            "output",
        ):
            axi[name] = {}
            axi_debug = getattr(self, name)
            strobes = axi_debug.getStrobes()
            axi_debug.update()
            axi[name] = {
                "axi_master": {
                    "tvalid": strobes.master.tvalid,
                    "tready": strobes.master.tready,
                },
                "axi_slave": {
                    "tvalid": strobes.slave.tvalid,
                    "tready": strobes.slave.tready,
                },
                "frames": axi_debug.getFrameCount(),
                "words": axi_debug.word_count,
                "last_frame_length": axi_debug.getLastFrameLength(),
                "max_frame_length": axi_debug.max_frame_length,
                "min_frame_length": axi_debug.min_frame_length,
            }

        result["axi_debug"] = axi
        return result

    def printStatus(self):
        table = [
            ("General config",),
            (
                "PL scramb SR init",
                "0x%.5X" % self.physical_layer_scrambler_shift_reg_init,
            ),
            (
                "Enable dummy frames",
                self.enable_dummy_frames,
            ),
            ("-----",),
            ("Status",),
            ("Frames in transit", self.getFramesInTransit()),
        ]

        debug_table = [
            (
                "Waypoint",
                "AXI slave",
                "AXI master",
                "Frames",
                "Words",
                "Last frame length",
                "Max frame length",
                "Min frame length",
            )
        ]

        for name in (
            "input_width_converter",
            "bb_scrambler",
            "bch_encoder",
            "ldpc_encoder",
            "bit_interleaver",
            "plframe",
            "output",
        ):
            row = [
                name,
            ]
            #  debug_table += [("-----",), (f"AXI debug - {name}",)]
            axi_debug = getattr(self, name)
            strobes = axi_debug.getStrobes()
            axi_debug.update()
            row += [
                f"tvalid={strobes.slave.tvalid}, tready={strobes.slave.tready}",
                f"tvalid={strobes.master.tvalid}, tready={strobes.master.tready}",
                axi_debug.getFrameCount(),
                axi_debug.word_count,
                axi_debug.getLastFrameLength(),
                axi_debug.max_frame_length,
                axi_debug.min_frame_length,
            ]
            debug_table += [row]

        output = (
            ["{0} Debug tables {0}".format(50 * "=")]
            + [" ".join(x) for x in tabulate(table)]
            + ["-----"]
            + [" ".join(x) for x in tabulate(debug_table)]
            + [(2 * 50 + 14) * "="]
        )
        print("\n".join(output))
