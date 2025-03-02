import json
import machine
import binascii

def firmware_update(_ssa, update_str):
    """
    Updates the device firmware from a JSON update package.
    
    This function decodes a firmware update provided as a JSON string that includes a base64‐encoded
    firmware binary and its expected CRC32 checksum (in hexadecimal format). It verifies the integrity
    of the decoded binary, writes it to "user/app.py" (creating the directory if necessary), and
    initiates a device restart. If the checksum verification fails, the update is aborted.
    
    Args:
        _ssa: Device state or configuration object (unused in current implementation).
        update_str: JSON string with keys "base64" for the firmware data and "crc32" for the expected checksum.
    """
    print(f"[INFO] Firmware update received with size {len(update_str)}")
    update = json.loads(update_str)

    binary = binascii.a2b_base64(update["base64"])
    expected_crc = int(update["crc32"], 16)
    bin_crc = binascii.crc32(binary)

    if bin_crc != expected_crc:
        print(f"[ERROR] CRC32 mismatch: expected:{hex(expected_crc)}, \
                got {hex(bin_crc)} Firmware update failed.")
        return

    if "user" not in os.listdir():
        os.mkdir("user")

    print("[INFO] Writing firmware to device")
    with open("user/app.py", "w") as f:
        f.write(binary.decode("utf-8"))

    print("[INFO] Firmware write complete. Restarting device.")
    from machine import soft_reset
    soft_reset()

def property_update(ssa, value, prop):
    """
    Updates a property on the given SSA instance from a JSON string.
    
    This function checks whether the specified property exists on the SSA object, parses
    the provided JSON string to obtain the new value, and updates the property using the SSA
    setter. If an error occurs during this process, an error message is printed with the details.
    
    Args:
        ssa: The object whose property is to be updated.
        value: A JSON-formatted string representing the new value for the property.
        prop: The name of the property to update.
    """
    try:
        _ = ssa.get_property(prop) # Check if property exists
        value = json.loads(value)
        ssa.set_property(prop, value)
    except Exception as e:
        print(f"[ERROR] Failed to update property '{prop}': {e}")
