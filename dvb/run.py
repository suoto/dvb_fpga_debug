#!/usr/bin/env python3

import argparse
import logging
import os
import os.path as p
import re
import struct
import sys
import time
from multiprocessing.pool import ThreadPool
from typing import Any, List, Optional, Tuple

import numpy as np
from matplotlib import pyplot as plt  # type: ignore

from dvb.common import (
    TID_MAP,
    BaseMemoryRegion,
    CodeRate,
    ConstellationType,
    FrameType,
    run,
)
from dvb.dvb_encoder import DvbEncoder  # type: ignore
from dvb.logger import setupLogging

# pylint: disable=missing-docstring
# pylint: disable=invalid-name
# pylint: disable=wrong-import-position


_RE_CONFIG = re.compile(
    r"(FECFRAME_(?:SHORT|NORMAL))_(MOD_.*?)_(C.*?)_input.bin"
).search

_logger = logging.getLogger(__name__)

TOLERANCE = 64

SUPPORTED_CONFIGS = {
    "FECFRAME_SHORT_MOD_QPSK_C8_9_input.bin",
    "FECFRAME_SHORT_MOD_QPSK_C5_6_input.bin",
    "FECFRAME_SHORT_MOD_QPSK_C4_5_input.bin",
    "FECFRAME_SHORT_MOD_QPSK_C3_5_input.bin",
    "FECFRAME_SHORT_MOD_QPSK_C3_4_input.bin",
    "FECFRAME_SHORT_MOD_QPSK_C2_5_input.bin",
    "FECFRAME_SHORT_MOD_QPSK_C2_3_input.bin",
    "FECFRAME_SHORT_MOD_QPSK_C1_4_input.bin",
    "FECFRAME_SHORT_MOD_QPSK_C1_3_input.bin",
    "FECFRAME_SHORT_MOD_QPSK_C1_2_input.bin",
    "FECFRAME_SHORT_MOD_8PSK_C8_9_input.bin",
    "FECFRAME_SHORT_MOD_8PSK_C5_6_input.bin",
    "FECFRAME_SHORT_MOD_8PSK_C3_5_input.bin",
    "FECFRAME_SHORT_MOD_8PSK_C3_4_input.bin",
    "FECFRAME_SHORT_MOD_8PSK_C2_3_input.bin",
    "FECFRAME_SHORT_MOD_32APSK_C8_9_input.bin",
    "FECFRAME_SHORT_MOD_32APSK_C5_6_input.bin",
    "FECFRAME_SHORT_MOD_32APSK_C4_5_input.bin",
    "FECFRAME_SHORT_MOD_32APSK_C3_4_input.bin",
    "FECFRAME_SHORT_MOD_16APSK_C8_9_input.bin",
    "FECFRAME_SHORT_MOD_16APSK_C5_6_input.bin",
    "FECFRAME_SHORT_MOD_16APSK_C4_5_input.bin",
    "FECFRAME_SHORT_MOD_16APSK_C3_4_input.bin",
    "FECFRAME_SHORT_MOD_16APSK_C2_3_input.bin",
    "FECFRAME_NORMAL_MOD_QPSK_C9_10_input.bin",
    "FECFRAME_NORMAL_MOD_QPSK_C8_9_input.bin",
    "FECFRAME_NORMAL_MOD_QPSK_C5_6_input.bin",
    "FECFRAME_NORMAL_MOD_QPSK_C4_5_input.bin",
    "FECFRAME_NORMAL_MOD_QPSK_C3_5_input.bin",
    "FECFRAME_NORMAL_MOD_QPSK_C3_4_input.bin",
    "FECFRAME_NORMAL_MOD_QPSK_C2_5_input.bin",
    "FECFRAME_NORMAL_MOD_QPSK_C2_3_input.bin",
    "FECFRAME_NORMAL_MOD_QPSK_C1_4_input.bin",
    "FECFRAME_NORMAL_MOD_QPSK_C1_3_input.bin",
    "FECFRAME_NORMAL_MOD_QPSK_C1_2_input.bin",
    "FECFRAME_NORMAL_MOD_8PSK_C9_10_input.bin",
    "FECFRAME_NORMAL_MOD_8PSK_C8_9_input.bin",
    "FECFRAME_NORMAL_MOD_8PSK_C5_6_input.bin",
    "FECFRAME_NORMAL_MOD_8PSK_C3_5_input.bin",
    "FECFRAME_NORMAL_MOD_8PSK_C3_4_input.bin",
    "FECFRAME_NORMAL_MOD_8PSK_C2_3_input.bin",
    "FECFRAME_NORMAL_MOD_32APSK_C9_10_input.bin",
    "FECFRAME_NORMAL_MOD_32APSK_C8_9_input.bin",
    "FECFRAME_NORMAL_MOD_32APSK_C5_6_input.bin",
    "FECFRAME_NORMAL_MOD_32APSK_C4_5_input.bin",
    "FECFRAME_NORMAL_MOD_32APSK_C3_4_input.bin",
    "FECFRAME_NORMAL_MOD_16APSK_C9_10_input.bin",
    "FECFRAME_NORMAL_MOD_16APSK_C8_9_input.bin",
    "FECFRAME_NORMAL_MOD_16APSK_C5_6_input.bin",
    "FECFRAME_NORMAL_MOD_16APSK_C4_5_input.bin",
    "FECFRAME_NORMAL_MOD_16APSK_C3_4_input.bin",
    "FECFRAME_NORMAL_MOD_16APSK_C2_3_input.bin",
}


def _toListOfInt(data: bytes) -> Tuple[Any, ...]:
    _logger.debug("Data length is %d bytes", len(data))
    return struct.unpack("<" + "h" * (len(data) // 2), data)


def _compare(
    actual: Tuple[int, ...], expected: Tuple[int, ...], tolerance: int
) -> Tuple[bool, float]:
    if len(actual) != len(expected):
        _logger.warning("Expected %d bytes, got %d", len(actual), len(expected))

    length = min(len(actual), len(expected))
    _logger.debug(
        "Input lengths were %d and %d, using %d", len(actual), len(expected), length
    )
    correlation = 0.0
    if length:
        correlation_matrix = np.corrcoef(actual[:length], expected[:length])
        correlation = min(correlation_matrix[0][1], correlation_matrix[1][0])
    _logger.info("Data correlation is %s", correlation)

    errors = 0
    passed = True
    for i, expected_word in enumerate(expected):
        try:
            actual_word = actual[i]
        except IndexError:
            _logger.warning("Can't compare data, index %d was not found", i)
            passed = False
            break

        lower_threshold = expected_word - tolerance
        upper_threshold = expected_word + tolerance

        if lower_threshold <= actual_word <= upper_threshold:
            func = _logger.debug
        else:
            func = _logger.error
            errors += 1

        if passed:
            func(
                "%4d || Got %6d, expected %6d || Thresholds: [%6d, %6d] || delta = %d",
                i,
                actual_word,
                expected_word,
                lower_threshold,
                upper_threshold,
                expected_word - actual_word,
            )

        if errors >= 10:
            passed = False
            #  break

    if errors:
        _logger.error(
            "Errors: %d / %d (%.2f%%)",
            errors,
            len(expected),
            100 * errors / len(expected),
        )
    else:
        _logger.info(
            "Errors: %d / %d (%.2f%%)",
            errors,
            len(expected),
            100 * errors / len(expected),
        )

    return passed, correlation


def configureFpga():
    _logger.info("Configuring FPGA")
    run(("fpgautil", "-b", "~/design_1_wrapper.bit.bin"))


def _parseArgs():
    "Parse command line arguments"
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--verbose",
        "-v",
        action="append_const",
        const=1,
        help="Increases verbosity. Passing multiple times progressively increases verbosity",
    )

    parser.add_argument(
        "infiles",
        action="store",
        nargs="+",
        default=None,
        help="List of input files to test",
    )

    args = parser.parse_args()

    level = logging.WARNING

    if args.verbose:
        if len(args.verbose) == 1:
            level = "INFO"
        elif len(args.verbose) == 2:
            level = "DEBUG"
        elif len(args.verbose) > 2:
            level = 4

    print(f"Log level set to {repr(level)}")

    setupLogging(sys.stdout, level, True)
    globals()["_logger"] = logging.getLogger(__name__)

    return args


class Runner:
    _dev_write_data = "/dev/xdma0_h2c_0"
    _dev_read_data = "/dev/xdma0_c2h_0"
    _dev_metadata = "/dev/xdma0_h2c_1"

    def __init__(self):
        _logger.debug("Creating encoder")
        self.encoder = DvbEncoder(0, 16 * 1024)
        #  self.init()
        #  self.axi = BaseMemoryRegion(0x2000, 1024)
        #  self.reset()

    def sendFromFile(
        self,
        path,
        frame_type: FrameType,
        constellation: ConstellationType,
        code_rate: CodeRate,
    ):
        tid = TID_MAP[frame_type][constellation][code_rate]
        _logger.info(
            "TID for %s, %s, %s is %d (0x%.2X)",
            frame_type,
            constellation,
            code_rate,
            tid,
            tid,
        )

        self.encoder.updateBitMapperRam(
            frame_type=frame_type, constellation=constellation, code_rate=code_rate
        )

        #  _logger.info("Status before any write")
        #  self.encoder.printStatus()

        pool = ThreadPool(2)
        pool.apply_async(self.writeMetadata, (tid.to_bytes(1, "little"),))

        with open(path, "rb") as fd:
            pool.apply_async(self.writeData, (fd.read(),))

        pool.close()
        #  _logger.info("Status right after writing")
        #  self.encoder.printStatus()
        _logger.debug("Waiting for processes to complete")
        pool.join()
        #  _logger.info("Status after writes completed")
        #  self.encoder.printStatus()
        _logger.debug("All writes completed")

    def writeMetadata(self, tid: bytes):
        _logger.debug("Writing metadata")
        with open(self._dev_metadata, "wb") as fd:
            _logger.debug("Writing to fd")
            result = fd.write(tid)

        _logger.debug("Completed")
        return result

    def writeData(self, data: bytes):
        _logger.debug("Writing data")
        with open(self._dev_write_data, "wb") as fd:
            _logger.debug("Writing to fd")
            result = fd.write(data)

        _logger.debug("Completed")
        return result

    def readData(self) -> bytes:
        _logger.debug("Reading data")
        result: bytes = b""
        #  return result
        fd = os.open(self._dev_read_data, os.O_RDONLY)
        try:
            while True:
                _logger.log(5, "Bytes so far: %d", len(result))

                #  chunk = bytes([x for i, x in enumerate(os.read(fd, 32)) if i % 8 < 4])
                chunk = os.read(fd, 32)

                _logger.log(5, "Chunk length is %d", len(chunk))

                if len(result) < 1024:
                    _logger.debug("Chunk: %s", [f"{x:02x}" for x in chunk])

                result += (
                    chunk[2:4]
                    + chunk[0:2]
                    + chunk[6:8]
                    + chunk[4:6]
                    + chunk[10:12]
                    + chunk[8:10]
                    + chunk[14:16]
                    + chunk[12:14]
                    + chunk[18:20]
                    + chunk[16:18]
                    + chunk[22:24]
                    + chunk[20:22]
                    + chunk[26:28]
                    + chunk[24:26]
                    + chunk[30:32]
                    + chunk[28:30]
                )

                if len(result) < 1024:
                    _logger.debug("Chunk: %s", [f"{x:02x}" for x in chunk])

                if len(chunk) < 32:
                    _logger.log(
                        5, "Chunk has %d bytes, detected end of frame", len(chunk)
                    )
                    break

        finally:
            os.close(fd)

        if not result:
            _logger.error("Timed out trying to read data")

        with open("output.bin", "wb") as fp:
            fp.write(bytes(result))

        _logger.debug("Completed")
        _logger.info("Read %d bytes", len(result))
        return result

    def run(self, infile: Optional[str]) -> Tuple[bool, float]:
        if infile is None:
            self.encoder.printStatus()
            return True, 1

        _logger.debug("infile basename is %s", p.basename(infile))
        if p.basename(infile) not in SUPPORTED_CONFIGS:
            _logger.warning("Configuration %s is not supported", infile)

        outfile = infile.replace("_input", "_output")
        match = _RE_CONFIG(infile)
        assert match is not None
        frame_type, constellation, code_rate = match.groups()
        #  print("Status before sending data")
        #  self.encoder.printStatus()

        self.sendFromFile(
            infile,
            getattr(FrameType, frame_type),
            getattr(ConstellationType, constellation),
            getattr(CodeRate, code_rate),
        )

        #  _logger.info("Waiting for frame to complete")
        #  for _ in range(100):
        #      if not self.encoder.getFramesInTransit():
        #          break
        #      time.sleep(0.1)
        #  if self.encoder.getFramesInTransit():
        #      assert False, "Timed out waiting for frame to complete"
        #  _logger.info("No more frames in transit")

        try:
            result = _toListOfInt(self.readData())
        except KeyboardInterrupt:
            _logger.error("Unable to read data after sending %s", infile)
            raise
        #  print("Status after sending data")
        #  self.encoder.printStatus()

        with open(outfile, "rb") as fd:
            expected = _toListOfInt(fd.read())

        #  print("Status after receiving data")
        #  self.encoder.printStatus()

        return _compare(actual=result, expected=expected, tolerance=TOLERANCE)

    def init(self):
        self.encoder.init()

    def runMultiple(self, paths: List[str]):
        run_all = False
        tests_passed: List[Tuple[str, float, float]] = []
        tests_failed: List[Tuple[str, float, float]] = []
        with open("results.log", "a+") as fd:
            for infile in paths:
                reply = "a" if run_all else None
                while reply not in ("y", "s", "q", "a"):
                    print("Testing", infile, ". Continue? (y)es, (q)uit, (s)kip, (a)ll")
                    reply = input()
                if reply == "a":
                    run_all = True
                if reply == "s":
                    _logger.info("Skipping")
                    continue
                if reply == "q":
                    _logger.info("Quitting")
                    break

                start = time.time()
                passed, correlation = self.run(infile)
                duration = time.time() - start

                if passed:
                    print("PASSED", infile, duration)
                    tests_passed.append((infile, duration, correlation))
                    fd.write(
                        f"PASSED, {infile}, time={duration:.2f}, {correlation:f}\n"
                    )
                else:
                    print("FAILED", infile, duration)
                    fd.write(
                        f"FAILED, {infile}, time={duration:.2f}, {correlation:f}\n"
                    )
                    tests_failed.append((infile, duration, correlation))

                time.sleep(0.5)

        print(len(tests_passed), "tests passed:")
        for name in tests_passed:
            print("-", name)
        print(len(tests_failed), "tests failed:")
        for name in tests_failed:
            print("-", name)


def main():
    args = _parseArgs()
    runner = Runner()

    if len(args.infiles) > 1:
        runner.runMultiple(args.infiles)
    elif len(args.infiles) == 1:
        infile = args.infiles.pop()
        while True:
            start = time.time()
            passed, correlation = runner.run(infile)
            print(
                f"{infile}, time={time.time() - start:.2f}, correlation={correlation}, passed={passed}"
            )
    else:
        runner.encoder.printStatus()

    return runner
