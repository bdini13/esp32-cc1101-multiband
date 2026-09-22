# Bring-up firmware

This PlatformIO/Arduino program verifies the initial digital hardware without
transmitting RF. It:

1. Configures both RF switches in their all-paths-isolated safe state.
2. Initializes the SPI bus at 1 MHz.
3. Resets the CC1101.
4. Reads the CC1101 PARTNUM and VERSION status registers.
5. Lights the status LED if the returned values are plausible.

It intentionally does not load a modem profile or issue a transmit command.
Full register profiles will be added only after the PCB and regional operating
requirements are verified.
