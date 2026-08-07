import sys
from pathlib import Path
from collections import defaultdict
from charset_normalizer import from_bytes

TARGET_EXT = {".c", ".cpp", ".h", ".hpp", ".md", ".qml", ".txt", ".tsv", ".csv", ".qrc", ".sh", ".py", ".xml", ".json", ".ps1"}

TARGET_ENCODING = "utf-8"
DEFAULT_NEWLINE = "\r\n"  # Windows (CRLF)
SHELL_NEWLINE = "\n"      # Linux (LF)


def get_target_newline(file_path):
    """Shell script는 LF, 나머지 파일은 CRLF를 사용한다."""
    if file_path.suffix.lower() == ".sh":
        return SHELL_NEWLINE
    return DEFAULT_NEWLINE


def convert_file(file_path):
    try:
        raw = file_path.read_bytes()
        if not raw.strip():
            return "skipped (empty)", None

        result = from_bytes(raw).best()
        detected_enc = result.encoding if result else None

        content = None
        original_encoding = None

        if result and (
            detected_enc.lower() == "ascii" or result.chaos == 0.0
        ):
            original_encoding = "ambiguous (ASCII/English only)"
            content = str(result)
        else:
            if detected_enc:
                try:
                    content = str(result)
                    original_encoding = detected_enc
                except UnicodeDecodeError:
                    content = None

            if content is None or detected_enc in ["iso-ir-149", "euc-kr"]:
                try:
                    content = raw.decode("cp949")
                    original_encoding = "cp949"
                except UnicodeDecodeError:
                    return "failed (decoding error)", None

        # 기존 줄바꿈을 모두 LF로 정규화한 후,
        # 파일 종류에 맞는 줄바꿈으로 저장한다.
        content = content.replace("\r\n", "\n").replace("\r", "\n")
        target_newline = get_target_newline(file_path)

        with open(
            file_path,
            "w",
            encoding=TARGET_ENCODING,
            newline=target_newline,
        ) as f:
            f.write(content)

        return "success", original_encoding

    except Exception as e:
        return f"error: {str(e)}", None


def main(root_dir):
    root = Path(root_dir)
    if not root.exists():
        print(f"Error: Directory {root_dir} not found.")
        return

    stats = defaultdict(int)
    total_files = 0

    print(f"Target Encoding: {TARGET_ENCODING}")
    print(f"Default Newline: {repr(DEFAULT_NEWLINE)}")
    print(f"Shell Script Newline: {repr(SHELL_NEWLINE)}\n")

    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in TARGET_EXT:
            status, old_enc = convert_file(path)
            total_files += 1

            if status == "success":
                stats[old_enc] += 1
                newline_name = (
                    "LF" if path.suffix.lower() == ".sh" else "CRLF"
                )
                print(
                    f"{path} : {status} "
                    f"({old_enc} -> {TARGET_ENCODING}, {newline_name})"
                )
            else:
                stats[status] += 1
                print(f"{path} : {status}")

    print("\n" + "=" * 40)
    print(f"{' Conversion Summary ':^40}")
    print("=" * 40)
    print(f"Total processed files: {total_files}")

    sorted_stats = sorted(
        stats.items(),
        key=lambda x: x[1],
        reverse=True,
    )

    for key, count in sorted_stats:
        if not key:
            continue

        if any(
            key.startswith(s)
            for s in ["error", "failed", "skipped"]
        ):
            print(f"- {key}: {count}")
        else:
            print(f"- {key} -> {TARGET_ENCODING}: {count}")

    print("=" * 40)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python convert_encoding.py <directory>")
        sys.exit(1)

    main(sys.argv[1])
