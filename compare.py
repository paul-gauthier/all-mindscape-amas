#!/usr/bin/env python3

N = 1000

def count_matching_end_bytes(file1_path, file2_path, max_bytes=N):
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
            
            # Calculate how many bytes to check
            bytes_to_check = min(max_bytes, size1, size2)
            
            matching_bytes = 0
            chunk_size = 1024  # Read in 1KB chunks for efficiency
            
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
                
                remaining -= current_chunk
            
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
    print(f"Last {matching} bytes match")
    sys.exit(0 if matching == N else 1)

if __name__ == "__main__":
    main()
