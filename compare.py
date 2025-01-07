#!/usr/bin/env python3

def count_matching_end_bytes(file1_path, file2_path, print_progress=True):
    """
    Count how many bytes match from the end of both files.
    Returns the count of matching bytes.
    """
    try:
        with open(file1_path, 'rb') as f1, open(file2_path, 'rb') as f2:
            # Seek to end of each file
            f1.seek(0, 2)
            f2.seek(0, 2)

            # Get file sizes
            size1 = f1.tell()
            size2 = f2.tell()

            # Use smaller file size as limit
            bytes_to_check = min(size1, size2)

            matching_bytes = 0
            last_percent = 0
            chunk_size = 1024*10

            remaining = bytes_to_check
            while remaining > 0:
                # Calculate size of next chunk
                current_chunk = min(chunk_size, remaining)

                # Seek backwards by chunk size
                f1.seek(-current_chunk, 1)
                f2.seek(-current_chunk, 1)

                # Read chunks
                chunk1 = f1.read(current_chunk)
                f1.seek(-current_chunk, 1)  # Go back to start of chunk
                chunk2 = f2.read(current_chunk)
                f2.seek(-current_chunk, 1)

                # Compare bytes from end to start
                for b1, b2 in zip(reversed(chunk1), reversed(chunk2)):
                    if b1 != b2:
                        return matching_bytes
                    matching_bytes += 1
                    if print_progress:
                        percent = (matching_bytes * 100) // bytes_to_check
                        if percent > last_percent:
                            print(f"\rChecked: {matching_bytes}/{bytes_to_check} bytes ({percent}%)", end='', flush=True)
                            last_percent = percent

                remaining -= current_chunk

            if print_progress:
                print()  # New line after progress

            return matching_bytes


    except IOError as e:
        print(f"Error reading files: {e}")
        return False

def main():
    import sys
    if len(sys.argv) != 3:
        print("Usage: python compare.py file1 file2")
        sys.exit(1)

    file1, file2 = sys.argv[1], sys.argv[2]
    matching = count_matching_end_bytes(file1, file2)
    
    # Get file sizes
    with open(file1, 'rb') as f1, open(file2, 'rb') as f2:
        f1.seek(0, 2)
        f2.seek(0, 2)
        size1 = f1.tell()
        size2 = f2.tell()
    
    # Calculate differences
    total = min(size1, size2)
    different = total - matching
    match_percent = (matching * 100) // total if total > 0 else 0
    diff_percent = 100 - match_percent
    
    # Report results
    print(f"File sizes: {size1} vs {size2} bytes (diff: {abs(size1 - size2)} bytes)")
    print(f"Last {matching} bytes match ({match_percent}%)")
    print(f"First {different} bytes differ ({diff_percent}%)")
    
    # Show per-file differences
    if size1 > size2:
        print(f"File 1 has {size1 - size2} extra bytes at start")
    elif size2 > size1:
        print(f"File 2 has {size2 - size1} extra bytes at start")
    sys.exit(0)

if __name__ == "__main__":
    main()
