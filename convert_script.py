import argparse
import os
import struct
import numpy as np

def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Process and convert a file to binary sequence.")
    parser.add_argument("--file", required=True, help="Input .sub file path")
    parser.add_argument("--output", help="Output file path")
    parser.add_argument("--intermediate_freq", type=int, help="Intermediate frequency")
    parser.add_argument("--sampling_rate", type=int, default=500000, help="Sampling rate (default: 500000)")
    parser.add_argument("--amplitude", type=int, default=100, help="Amplitude (default: 100)")
    return parser.parse_args()


def parse_sub(file_path):
    """Parse the input file and extract metadata and chunks, including handling RAW_Data if specified."""
    try:
        with open(file_path, 'r') as file:
            lines = file.read().splitlines()
    except FileNotFoundError:
        raise Exception("Cannot read input file")

    # Initialize metadata dictionary
    metadata = {}
    chunks = []

    # Process each line to collect metadata and handle special cases like RAW_Data
    for line in lines:
        if ':' in line:  # Expect metadata lines to contain a colon
            key, value = line.split(":", 1)
            key = key.strip().lower()  # Normalize key to lowercase
            value = value.strip()
            
            # Special handling for RAW_Data field, to store as chunks
            if key == "raw_data":
                chunks = [[int(x) for x in value.split()]]  # Parse RAW_Data as integer list
            else:
                metadata[key] = value

    # Add parsed chunks to metadata if RAW_Data was processed
    metadata["chunks"] = chunks if chunks else []

    return metadata


def durations_to_bin_sequence(durations, sampling_rate, intermediate_freq, amplitude):
    sequence = []
    for duration in durations:
        level = duration > 0
        duration = abs(duration)
        sequence.extend(us_to_sin(level, duration, sampling_rate, intermediate_freq, amplitude))
    return sequence


def us_to_sin(level, duration, sampling_rate, intermediate_freq, amplitude):
    iterations = int(sampling_rate * duration / 1_000_000)
    data_step = 2 * np.pi / (sampling_rate / intermediate_freq)
    amplitude_scale = (256**2 - 1) * (amplitude / 100)
    
    if level:
        return [[int(np.cos(i * data_step) * (amplitude_scale / 2)), int(np.sin(i * data_step) * (amplitude_scale / 2))] for i in range(iterations)]
    else:
        return [[0, 0] for _ in range(iterations)]


def sequence_to_16le_buffer(sequence):
    buffer = bytearray()
    for i, q in sequence:
        buffer.extend(struct.pack('<h', i))
        buffer.extend(struct.pack('<h', q))
    return buffer


def write_hrf_file(output_path, buffer, frequency, sampling_rate):
    output_c16 = f"{output_path}.C16"
    output_txt = f"{output_path}.TXT"
    
    with open(output_c16, 'wb') as file:
        file.write(buffer)
    
    with open(output_txt, 'w') as file:
        file.write(f"sample_rate={sampling_rate}
center_frequency={frequency}
")
    
    return [output_c16, output_txt]


if __name__ == "__main__":
    args = parse_args()
    parsed_metadata = parse_sub(args.file)
    
    sequence = parsed_metadata["chunks"][0] if parsed_metadata["chunks"] else []
    buffer = sequence_to_16le_buffer(durations_to_bin_sequence(sequence, args.sampling_rate, args.intermediate_freq or 5000, args.amplitude))
    
    output_path = args.output or os.path.splitext(args.file)[0]
    write_hrf_file(output_path, buffer, parsed_metadata.get("frequency", "0"), args.sampling_rate)