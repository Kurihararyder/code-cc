import sys


def main():
    for line in sys.stdin:  # 多組測資：讀到 EOF
        line = line.rstrip("\n")  # 空行也可能是一筆資料；題目沒說就不要跳過
        # TODO


if __name__ == "__main__":
    main()
