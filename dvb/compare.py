#!/usr/bin/env python3

import struct
import sys
from typing import Any, Tuple

import numpy as np


def _compare(
    actual: Tuple[int, ...], expected: Tuple[int, ...], tolerance: int
) -> Tuple[bool, float]:
    print("#######################")
    if len(actual) != len(expected):
        print("Expected %d bytes, got %d" % (len(actual), len(expected)))

    length = min(len(actual), len(expected))
    print(
        "Input lengths were %d and %d, using %d" % (len(actual), len(expected), length)
    )
    correlation = 0.0
    if length:
        correlation_matrix = np.corrcoef(actual[:length], expected[:length])
        correlation = min(correlation_matrix[0][1], correlation_matrix[1][0])
    print("Data correlation is %s" % correlation)

    errors = 0
    passed = True
    max_delta = 0
    for i, expected_word in enumerate(expected[:length]):
        try:
            actual_word = actual[i]
        except IndexError:
            print("Can't compare data, index %d was not found" % i)
            passed = False
            break

        lower_threshold = expected_word - tolerance
        upper_threshold = expected_word + tolerance

        report = True
        fmt = "%4d/%d || Got %6d (0x%.4X, % .8f), expected %6d (0x%.4X, % .8f) || Thresholds: [%6d, %6d] || delta = %d"
        max_delta = max(max_delta, abs(expected_word - actual_word))
        if lower_threshold <= actual_word <= upper_threshold:
            fmt = "[OK]  " + fmt
            report = False
        else:
            fmt = "[NOK] " + fmt
            errors += 1
            report = True

        if passed:  # and report:
            actual_bin = actual_word
            if actual_bin < 0:
                actual_bin += 1 << 16
            expected_bin = expected_word
            if expected_bin < 0:
                expected_bin += 1 << 16
            print(
                fmt
                % (
                    i / 2,
                    i % 2,
                    actual_word,
                    actual_bin,
                    actual_word / (1 << 15),
                    expected_word,
                    expected_bin,
                    expected_word / (1 << 15),
                    lower_threshold,
                    upper_threshold,
                    expected_word - actual_word,
                )
            )

        if errors >= 10:
            passed = False
            #  break

    print(
        f"Errors: {errors:d} / {len(expected)}",
        f"({100 * errors / len(expected):.2f}%%)",
    )

    print(f"Max abs delta: {max_delta}")

    return passed, correlation


def _toListOfInt(data: bytes) -> Tuple[Any, ...]:
    print("Data length is %d bytes" % len(data))
    return struct.unpack("<" + "h" * (len(data) // 2), data)


def main():
    print("Comparing")
    filename_actual = sys.argv[1]
    filename_expected = sys.argv[2]

    with open(filename_actual, "rb") as fd:
        actual = _toListOfInt(fd.read())
    with open(filename_expected, "rb") as fd:
        expected = _toListOfInt(fd.read())

    sys.stderr.write(f"{filename_expected}, {_compare(actual, expected, 64)}\n")
