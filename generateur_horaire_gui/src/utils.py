def validate_file_path(file_path: str) -> bool:
    import os
    return os.path.isfile(file_path)

def validate_positive_integer(value: str) -> bool:
    return value.isdigit() and int(value) > 0

def read_ini_file(file_path: str) -> list:
    salles = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                s = line.strip()
                if not s or s.startswith("#"):
                    continue
                if "=" in s:
                    _, val = s.split("=", 1)
                    val = val.strip()
                    if val:
                        salles.append(val)
    except Exception as e:
        print(f"Error reading INI file: {e}")
    return salles

def write_output_file(file_path: str, content: str) -> None:
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
    except Exception as e:
        print(f"Error writing output file: {e}")