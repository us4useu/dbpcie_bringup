# DBARLitePCIe Firmware Programmer

This script generates a configuration **ELF** file based on the provided serial number and selected hardware options and programs **DBARLitePCIe** bootloader and application firmware.

## Description

The tool is used to configure and program DBARLitePCIe devices by assigning a serial number and enabling optional hardware features through command-line arguments.

It supports the following configuration options:

* Power switch monostable mode
* HV discharge control (revision 2.0 only)
* Host PC power control
* Host PC power synchronization
* Automatic startup on power-up
* Disabling OEM staggered start

---

## Requirements

* STM32CubeProgrammer 2.13 installed and added to the system PATH so the CLI tools are accessible from the command line.
* Python 3.x
* Required programming tools and dependencies installed in the environment
* Access to the DBARLitePCIe target hardware

---

## Usage

```bash
python dbcie_bringup.py --sn <SERIAL_NUMBER> [OPTIONS]
```

---

## Required Argument

### `--sn`

Specifies the DBARLitePCIe serial number.

### Format

Accepted formats:

```bash
--sn DBLP2301012100
```

or

```bash
--sn 2301012100
```

### Example

```bash
python dbcie_bringup.py --sn DBLP2301012100
```

---

## Optional Arguments

### `--pwr_mono`

Enable **power switch monostable** option.

```bash
python dbcie_bringup.py --sn DBLP2301012100 --pwr_mono
```

---

### `--hv_discharge`

Enable **HV discharge control** option.

> Applicable for hardware revision **2.0 only**

```bash
python dbcie_bringup.py --sn DBLP2301012100 --hv_discharge
```

---

### `--host_pwrctrl`

Enable **Host PC power control** option.

```bash
python script.py --sn DBLP2601012100 --host_pwrctrl
```

---

### `--host_pwrctrl` and `--host_pwrsync`

Enable **Host PC power synchronization** option.

```bash
python dbcie_bringup.py --sn DBLP2601012100 --host_pwrctrl --host_pwrsync
```

---

### `--autostart`

Enable **automatic startup on power-up**.

```bash
python dbcie_bringup.py --sn DBLP2601012100 --autostart
```

---

### `--disable_ss`

Disable **OEM staggered start**.

```bash
python dbcie_bringup.py --sn DBLP2601012100 --disable_ss
```

---

## Notes

* `--sn` is mandatory.
* All other options are optional flags.
* If an option is not provided, it remains disabled.
* Ensure the hardware revision supports the selected features before programming.

---

## Output

The script performs:

1. Firmware programming
2. Configuration ELF generation
3. Device setup according to selected options

