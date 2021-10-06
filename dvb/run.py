#!/usr/bin/env python3

# pylint: disable=missing-docstring
# pylint: disable=invalid-name
# pylint: disable=wrong-import-position

import argparse
import logging
import os.path as p
import re
import struct
import sys
import time
from typing import Any, List, Optional, Tuple

import numpy as np

sys.path.insert(0, p.abspath(p.dirname(__file__)))

from common import (TID_MAP, CodeRate, ConstellationType,  # type: ignore
                     FrameType, run)
from dvb_encoder import DvbEncoder  # type: ignore
from logger import setupLogging  # type: ignore

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
            break

    _logger.info(
        "Errors: %d / %d (%.2f%%)", errors, len(expected), 100 * errors / len(expected)
    )

    return passed, correlation


def configureFpga():
    _logger.info("Configuring FPGA")
    run(("fpgautil", "-b", "~/design_1_wrapper.bit.bin"))


class Runner:
    def __init__(self):
        _logger.debug("Creating encoder")
        self.encoder = DvbEncoder(0x44A0_0000, 16 * 1024)
        self.init()
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

        #  self.meta_fifo.send(tid.to_bytes(1, "little"))
        #  with open(path, "rb") as fd:
        #      self.data_fifo.send(fd.read(), tid)

    def run(self, infile: Optional[str]) -> Tuple[bool, float]:
        if infile is None:
            self.encoder.printStatus()
            return True, 1

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
        #  print("Status after sending data")
        #  self.encoder.printStatus()

        _logger.info("Waiting for frame to complete")
        for _ in range(100):
            if not self.encoder.getFramesInTransit():
                break
            time.sleep(0.1)
        if self.encoder.getFramesInTransit():
            assert False, "Timed out waiting for frame to complete"
        #  result = _toListOfInt(self.data_fifo.receive())

        with open(outfile, "rb") as fd:
            expected = _toListOfInt(fd.read())

        #  print("Status after receiving data")
        #  self.encoder.printStatus()

        return _compare(actual=result, expected=expected, tolerance=TOLERANCE)

    def reset(self):
        _logger.info("Resetting data FIFOs")

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

        print(len(tests_passed), "tests passed:")
        for name in tests_passed:
            print("-", name)
        print(len(tests_failed), "tests failed:")
        for name in tests_failed:
            print("-", name)


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
        "--monitor",
        "-m",
        action="store",
        help="Address to listen to when publishing stats",
    )

    parser.add_argument(
        "infiles",
        action="store",
        nargs="*",
        default=None,
        help="List of input files to test",
    )

    args = parser.parse_args()

    level = logging.WARNING

    if args.verbose:
        if len(args.verbose) == 1:
            level = logging.INFO
        elif len(args.verbose) > 1:
            level = logging.DEBUG

    setupLogging(sys.stdout, level, True)
    globals()["_logger"] = logging.getLogger(__name__)

    return args


def main():
    args = _parseArgs()
    _runner = Runner()

    if args.monitor is not None:
        import bottle  # type: ignore

        @bottle.route("/read/status")
        def index():
            result = _runner.encoder.getStatus()
            return result

        host = args.monitor.split(":")
        port = 60001
        if isinstance(host, list):
            host, port = host
        bottle.run(host=host, port=port)

    elif len(args.infiles) > 1:
        _runner.runMultiple(args.infiles)
    elif len(args.infiles) == 1:
        infile = args.infiles.pop()
        start = time.time()
        passed, correlation = _runner.run(infile)
        print(
            f"{infile}, time={time.time() - start:.2f}, correlation={correlation}, passed={passed}"
        )
    else:
        _runner.encoder.printStatus()

    return _runner


runner = main()
