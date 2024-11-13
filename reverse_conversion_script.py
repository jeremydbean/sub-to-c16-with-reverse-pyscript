
import struct
import numpy as np

def read_txt_metadata(txt_file_path):
    """Read frequency and sample rate from .TXT file."""
    metadata = {}
    with open(txt_file_path, 'r') as file:
        for line in file:
            key, value = line.strip().split('=')
            metadata[key] = int(value)
    return metadata


def decode_c16_to_durations(c16_file_path):
    """Decode .C16 file to a list of timing durations."""
    durations = []
    with open(c16_file_path, 'rb') as file:
        while True:
            iq_pair = file.read(4)
            if not iq_pair:
                break
            i, q = struct.unpack('<hh', iq_pair)
            amplitude = int(np.sqrt(i**2 + q**2))
            # Determine signal duration based on amplitude level
            durations.append(amplitude)
    return durations


def convert_to_sub(c16_file_path, txt_file_path, output_path):
    """Convert .C16 and .TXT files to .sub format."""
    # Read metadata from .TXT file
    metadata = read_txt_metadata(txt_file_path)
    frequency = metadata.get('center_frequency', 0)
    sampling_rate = metadata.get('sample_rate', 500000)

    # Decode binary data from .C16 file
    durations = decode_c16_to_durations(c16_file_path)

    # Write .sub file using reconstructed metadata and RAW_Data
    with open(output_path, 'w') as file:
        file.write(f"Filetype: Flipper SubGhz RAW File\n")
        file.write(f"Version: 1\n")
        file.write(f"Frequency: {frequency}\n")
        file.write(f"Preset: FuriHalSubGhzPresetOok650Async\n")
        file.write(f"Protocol: RAW\n")
        file.write("RAW_Data: ")
        file.write(" ".join(map(str, durations)))

    print(f"Converted to .sub format: {output_path}")


# Example usage
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Convert .C16 and .TXT to .sub")
    parser.add_argument("--c16", required=True, help="Input .C16 file path")
    parser.add_argument("--txt", required=True, help="Input .TXT file path")
    parser.add_argument("--output", required=True, help="Output .sub file path")
    args = parser.parse_args()

    convert_to_sub(args.c16, args.txt, args.output)
