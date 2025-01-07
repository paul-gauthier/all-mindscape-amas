#!/usr/bin/env python3

def compare_file_endings(file1_path, file2_path, num_bytes=100):
    """
    Compare the last num_bytes of two files.
    Returns True if they match, False otherwise.
    """
    try:
        with open(file1_path, 'rb') as f1, open(file2_path, 'rb') as f2:
            # Seek to num_bytes from end of each file
            f1.seek(0, 2)  # Seek to end
            f2.seek(0, 2)
            
            # Get file sizes
            size1 = f1.tell()
            size2 = f2.tell()
            
            # Calculate how many bytes to read (minimum of num_bytes or file size)
            bytes_to_read = min(num_bytes, size1, size2)
            
            # Seek to the right position from end
            f1.seek(-bytes_to_read, 2)
            f2.seek(-bytes_to_read, 2)
            
            # Read and compare the bytes
            return f1.read(bytes_to_read) == f2.read(bytes_to_read)
            
    except IOError as e:
        print(f"Error reading files: {e}")
        return False

def main():
    import sys
    if len(sys.argv) != 3:
        print("Usage: python compare.py file1 file2")
        sys.exit(1)
        
    file1, file2 = sys.argv[1], sys.argv[2]
    if compare_file_endings(file1, file2):
        print("Last 100 bytes match")
        sys.exit(0)
    else:
        print("Last 100 bytes differ")
        sys.exit(1)

if __name__ == "__main__":
    main()
