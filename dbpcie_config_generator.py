
import subprocess
import os
import struct

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

def generate_elf(sn, option):
    #variant = sn[-2:]  # Extract last 2 characters as variant
    output_file = f"DBLP{sn}_conf.elf"
    flash_address = 0x080E0000
    
    data = generate_config_bitstream(sn, option)

    decode_sn_config(sn, option)
    
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

