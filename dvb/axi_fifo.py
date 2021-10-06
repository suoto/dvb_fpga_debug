# type: ignore
# pylint: disable=missing-docstring
import logging

from common import BaseMemoryRegion

ISR = 0x0  # Read/Clear on Write(1)Interrupt Enable Register (IER))
IER = 0x4  # Read/WriteTransmit Data FIFO Reset (TDFR)
TX_FIFO_RESET = 0x8  # Write(2)Transmit Data FIFO Vacancy (TDFV)
TX_FIFO_VACANCY = 0xC  # ReadTransmit Data FIFO 32-bit Wide Data Write Port (TDFD)
TX_FIFO_DATA = 0x10
TX_LENGTH_REGISTER = 0x14  # WriteReceive Data FIFO reset (RDFR)
RX_FIFO_RESET = 0x18  # Write(2)Receive Data FIFO Occupancy (RDFO)
RX_FIFO_OCCUPANCY = 0x1C  # ReadSend

RX_FIFO_DATA = 0x20  # Receive Length Register (RLR)
RX_LENGTH_REGISTER = 0x24  # ReadAXI4-Stream Reset (SRR)
AXI4_STREAM_RESET = 0x28  # Write(2)Transmit Destination Register (TDR)
TX_DEST_REGISTER = 0x2C  # WriteReceive Destination Register (RDR)
RX_DEST_REGISTER = 0x30  # ReadTransmit ID Register(4)
TX_ID_REGISTER = 0x34  # Transmit ID register
TX_USER_REGISTER = 0x38  # Transmit USER register
RX_ID_REGISTER = 0x3C  # Receive ID register
RX_USER_REGISTER = 0x40  # Receive USER register


class AxiFifo(BaseMemoryRegion):
    count = 0

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._logger = logging.getLogger(f"axi_fifo_{self.count}")
        AxiFifo.count += 1

    def reset(self):
        self._logger.info("Resetting AXI FIFO")
        self._write(TX_FIFO_RESET, 0xA5)
        self._write(AXI4_STREAM_RESET, 0xA5)
        self._write(RX_FIFO_RESET, 0xA5)

    def init(self):
        self._logger.info("Initializing AXI FIFO")
        self._logger.debug("ISR = 0x%X", self._read(ISR))
        self._write(ISR, 0xFFFFFFFF)
        self._logger.debug("ISR = 0x%X", self._read(ISR))
        self._logger.debug("IER = 0x%X", self._read(IER))

        self._logger.debug("TX_FIFO_VACANCY = %d", self._read(TX_FIFO_VACANCY))
        self._logger.debug("RX_FIFO_VACANCY = %d", self._read(RX_FIFO_OCCUPANCY))

    def send(self, data: bytes, tid: int = 0):
        words = (len(data) + 3) // 4
        self._logger.info(
            "Sending %d bytes (%d beats), TID = %d", len(data), words, tid
        )
        # Enable transmit complete and receive complete interrupts
        self._write(IER, 0x0C000000)
        self._write(TX_DEST_REGISTER, 0)
        self._write(TX_ID_REGISTER, tid)
        self._write(TX_USER_REGISTER, tid)
        for i in range(words):
            word = data[4 * i : 4 * i + 4]
            self._write(TX_FIFO_DATA, int.from_bytes(word, "big"))

        self._logger.info("Tx FIFO vac: %d", self._read(TX_FIFO_VACANCY))
        self._writeTxLength(len(data))

        self._logger.debug("ISR = 0x%X", self._read(ISR))
        self._write(ISR, 0xFFFFFFFF)
        self._logger.debug("ISR = 0x%X", self._read(ISR))
        self._logger.info("Tx FIFO vac: %d", self._read(TX_FIFO_VACANCY))

    def receive(self, entries=None):
        entries = entries or self.getRxOccupation()
        self._logger.info("Reading %d entries", entries)
        result = b""
        for i in range(entries):
            word = f"{self._read(RX_FIFO_DATA):08X}"
            word = word[2:4] + word[0:2] + word[6:8] + word[4:6]
            self._logger.debug("%3d | 0x%s", i, word)
            result += bytes.fromhex(word)

        return result

    def _receiveCutThrough(self):
        self._write(IER, 0x04100000)
        self._logger.info("ISR before reading: 0x%.8X", self._read(ISR))
        self._write(ISR, 0x00100000)
        self._logger.info("ISR after clearing: 0x%.8X", self._read(ISR))

        partial, length = self._getRxLength()
        self._logger.info("Partial frame: %d, length is %d bytes", partial, length)
        entries = (length + 3) // 4
        dest = self._read(RX_DEST_REGISTER)

        self._logger.info("Destination: 0x%.8X", dest)
        self._logger.info("ID: 0x%.8X", self._read(RX_ID_REGISTER))
        for i in range(entries):
            self._logger.info("%2d: 0x%.8X", i, self._read(RX_FIFO_DATA))

        #  self._logger.info("RX FIFO occupancy: %d", self.getRxOccupation())

    def _writeTxLength(self, length_in_bytes):
        self._write(TX_LENGTH_REGISTER, length_in_bytes)

    def _getRxLength(self):
        value = self._read(RX_LENGTH_REGISTER)
        partial = (value >> 31) & 1
        length = value & ((1 << 30) - 1)
        return partial, length

    def _resetTxFifo(self):
        self._write(TX_FIFO_RESET, 0xA5)

    def _resetRxFifo(self):
        self._write(RX_FIFO_RESET, 0xA5)

    def _resetFifos(self):
        self._resetTxFifo()
        self._resetRxFifo()

    def getTxOccupation(self):
        return self._read(TX_FIFO_VACANCY)

    def getRxOccupation(self):
        return self._read(RX_FIFO_OCCUPANCY)
