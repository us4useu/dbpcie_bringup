import subprocess
import os
import struct
import argparse
import sys

CLI = "STM32_Programmer_CLI"

FW_DIR = "fw_elf"
BL_ELF = "DBARLitePcie_Bootloader_1.2.0.BB.elf"
APP_ELF = "DBARLitePcie-Application-1.3.0.0.elf"

def generate_config_bitstream(sn, option):
    data = bytearray([0xFF] * 32)

    # Convert SN to integer values (each 2 characters = 1 integer)
    sn_bytes = [int(sn[i:i+2]) for i in range(0, len(sn), 2)]

    data[0] = 0xAA  # First byte fixed to 0xAA
    data[1:4] = sn_bytes[:3]  # Next 5 bytes are SN integers
    data[8] = sn_bytes[4]
    data[9] = sn_bytes[3]

    if(option>0) :
        data[4] = 0xAA
        data[5] = option & 0xFF
        data[6] = ((option & 0xFF00) >> 8)
        data[7] = ((option & 0xFF0000) >> 16)

    # Last 16 bytes are "AAAA" + serial as string
    serial_str = "DBLP" + sn + "  "
    serial_bytes = serial_str.encode('ascii')[:16]  # Ensure it fits in 16 bytes
    data[-16:] = serial_bytes.ljust(16, b'\x00')  # Pad with nulls if necessary

    return data

def decode_sn_config(sn, option):
    # Convert SN to integer values (each 2 characters = 1 integer)
    serial_str = "DBLP" + sn
    revision = sn[-4:-3] + "." + sn[-3:-2]  # Extract last 2 characters as variant
    variant_voltage =  sn[-1:]  # Extract last 2 characters as variant
    variant_conn =  sn[-2:-1]  # Extract last 2 characters as variant
    print("")
    print(("Program DBARLitePCIe with SN: " + serial_str))
    print("PCB revision: " + revision)
    print("Variant: " + variant_conn + variant_voltage)
    if variant_voltage == "0":
        print("    Voltage: 12 V")
    elif variant_voltage == "1":
        print("    Voltage: 13-24 V")
    if variant_conn == "0":
        print("    Connector: SFF8643")
    elif variant_conn == "1":
        print("    Connector: SFF8644")
    print("")

    #options
    if option > 0:
        print("Optional configuration:")
        if option & 0b00000001:
            print("    Power switch monostable")
        if option & 0b00000010:
            print("    HV discharge control enable (rev 2.0 only)")
        if option & 0b00000100:
            print("    Host PC power control")
        if option & 0b00001000:
            print("    Host PC power sync")
        if option & 0b00010000:
            print("    Autostart on power-up (software)")
        if option & 0b00100000:
            print("    Disable OEM staggered start")
        print("")


def generate_elf(sn, option):
    #variant = sn[-2:]  # Extract last 2 characters as variant
    output_file = f"DBLP{sn}_conf.elf"
    flash_address = 0x080E0000
    
    data = generate_config_bitstream(sn, option)
    
    print(f"Generated file: {output_file}")
    print(f"Flash Address: {hex(flash_address)}")
    print("Data: " + ' '.join(f"{b:02X}" for b in data))
    
    # Generate linker script
    linker_script = "linker.ld"
    with open(linker_script, "w") as f:
        f.write(f"""
        MEMORY
        {{
            FLASH (rx) : ORIGIN = {hex(flash_address)}, LENGTH = 32
        }}
        
        SECTIONS
        {{
            .text :
            {{
                *(.text)
            }} > FLASH
        }}
        """.strip())
    
    # Generate assembly source file
    asm_file = "data.S"
    with open(asm_file, "w") as f:
        f.write(f"""
        .section .text
        .global _start
        _start:
        .byte {', '.join(f'0x{b:02X}' for b in data)}
        """.strip())
    
    # Compile to ELF
    subprocess.run(["arm-none-eabi-as", "-o", "data.o", asm_file], check=True)
    subprocess.run(["arm-none-eabi-ld", "-T", linker_script, "data.o", "-o", output_file], check=True)
    
    print(f"ELF file '{output_file}' successfully generated.")
    
    # Cleanup
    os.remove(linker_script)
    os.remove(asm_file)
    os.remove("data.o")

    return output_file

def validate_sn(s: str) -> bool:
    
    errors = []
    
    #validate format
    if len(s) != 10:
        errors.append(("E01", "Code must be exactly 10 characters long (after prefix removal)"))

    if not s.isdigit():
        errors.append(("E02", "Code must contain only digits"))

    if errors:
        print("Validation failed with the following errors:")
        for code, msg in errors:
            print(f"{code}: {msg}")
            print("Example of valid code: DBLP2301011020 or 2301011020 (year=23, week=01, unit=01, revision=20, variant=00)")
        return False
    
    year = int(s[0:2])
    week = int(s[2:4])
    unit = int(s[4:6])
    revision = s[6:8]
    variant = s[8:10]

    if not (23 <= year <= 30):
        errors.append(("E10", f"Invalid year '{year:02d}' (allowed: 23–30)"))

    if not (1 <= week <= 53):
        errors.append(("E11", f"Invalid week '{week:02d}' (allowed: 01–53)"))

    if not (0 <= unit <= 99):
        errors.append(("E12", f"Invalid unit '{unit:02d}' (allowed: 00–99)"))

    if revision not in {"20", "21"}:
        errors.append(("E13", f"Invalid revision '{revision}' (allowed: 20 or 21)"))

    if variant not in {"00", "01", "10", "11"}:
        errors.append(("E14", f"Invalid variant '{variant}' (allowed: 00, 01, 10, 11)"))

    if errors:
        print("Validation failed with the following errors:")
        for code, msg in errors:
            print(f"{code}: {msg}")
        return False
    else:
        return True

def validate_options(option: int) -> bool:
    if option < 0 or option > 0xFF:
        print("Invalid option value. Must be between 0 and 0xFF.")
        return False
    
    if option & 0b00010000 and option & 0b00000001:
        print("Autostart and power switch monostable options cannot be enabled together.")
        return False
    
    if option & 0b00001000:
        print("Host PC power sync option requires enabling host PC power control")
        return False

    return True

def main():
    parser = argparse.ArgumentParser(description="Programs DBARLitePCIe fw 1.2.0.BB/1.3.0.0 and generates config ELF based on provided SN and options")
    parser.add_argument("--sn", required=True, help="DBARLitePCIe serial number (example: -sn DBLP2301012100 or -sn 2301012100)")    
    parser.add_argument("--pwr_mono", action="store_true", help="Power switch monostable option")
    parser.add_argument("--hv_discharge", action="store_true", help="HV discharge control enable option (rev 2.0 only)")
    parser.add_argument("--host_pwrctrl", action="store_true", help="Host PC power control option")
    parser.add_argument("--host_pwrsync", action="store_true", help="Host PC power sync option")
    parser.add_argument("--autostart", action="store_true", help="Enable autostart on power-up")
    parser.add_argument("--disable_ss", action="store_true", help="Disable OEM staggered start")
    #parser.add_argument("-option", type=int, required=False, help="Optional configuration", default=0)
    args = parser.parse_args()

    if args.sn.startswith("DBLP"):
        args.sn = args.sn[4:]

    #build options byte
    options = 0
    if args.pwr_mono:
        options |= 1 << 0
    if args.hv_discharge:
        options |= 1 << 1
    if args.host_pwrctrl:
        options |= 1 << 2
    if args.host_pwrsync:
        options |= 1 << 3
    if args.autostart:
        options |= 1 << 4
    if args.disable_ss:
        options |= 1 << 5


    validate_sn(args.sn)
    if not validate_options(options):
        print("Invalid options provided. Exiting.")
        return

    decode_sn_config(args.sn, options)

    #ask user if valid
    valid = input("Is the configuration valid? (y/n): ")
    if valid.lower() != "y":
        print("Configuration aborted.")
        return

    file = generate_elf(args.sn, options)

    cmd = [
        CLI,
        "-c", "port=SWD",
        "-e", "all"
    ]
    # bootloader
    cmd += ["-d", os.path.join(FW_DIR, BL_ELF)]
    # app
    cmd += ["-d", os.path.join(FW_DIR, APP_ELF)]
    #config
    cmd += ["-d", file]

    cmd += ["-rst"]

    print("\nFlashing STM32...\n")
    print("Command:", " ".join(cmd))

    result = subprocess.run(cmd)
    
    if result.returncode != 0:
        print("❌ Flashing failed!")
        sys.exit(result.returncode)

    print("\n✅ Flashing completed successfully!")

if __name__ == "__main__":
    main()