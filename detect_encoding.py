import sys
from pathlib import Path
from collections import defaultdict
from charset_normalizer import from_bytes

TARGET_EXT = {".c", ".cpp", ".h", ".hpp", ".md", ".qml", ".txt", ".tsv", ".csv", ".qrc", ".sh", ".py", ".xml", ".json", ".ts"}

def detect_encoding(file_path):
    try:
        raw = file_path.read_bytes()

        if not raw.strip():
            return "empty", 1.0

        has_bom = raw.startswith(b'\xef\xbb\xbf')
        result = from_bytes(raw).best()

        if result is None:
            return "unknown", 0.0

        encoding = result.encoding.lower()

        if encoding == "ascii" or result.chaos == 0.0:
            return "ambiguous (ASCII/English only)", 0.0

        if has_bom and encoding.replace("-", "_") == "utf_8":
            encoding = "utf-8-bom"

        return encoding, result.chaos
    
    except Exception as e:
        return f"error: {str(e)}", 0.0

def main(root_dir):
    root = Path(root_dir)
    if not root.exists():
        print(f"Error: Directory {root_dir} not found.")
        return

    stats = defaultdict(int)
    total_files = 0

    print(f"Scanning Directory: {root_dir}\n")

    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in TARGET_EXT:
            enc, chaos = detect_encoding(path)
            stats[enc] += 1
            total_files += 1
            print(f"{path} -> {enc} (chaos={chaos:.3f})")

    print("\n" + "="*40)
    print(f"{' Detection Summary ':^40}")
    print("="*40)
    print(f"Total scanned files: {total_files}")
    
    for enc, count in sorted(stats.items(), key=lambda x: -x[1]):
        print(f"- {enc}: {count}")
    print("="*40)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python detect_encoding.py <directory>")
        sys.exit(1)

    main(sys.argv[1])
