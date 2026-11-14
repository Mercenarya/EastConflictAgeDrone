from pathlib import Path
import re
import shutil

ROOT = Path(__file__).resolve().parent

# Mỗi đơn vị cần trỏ tới sprite phù hợp với chính sprite sheet của nó.
# Thêm các cặp "đường_dẫn_file_cấu_hình": "sprite.png" sau khi xác nhận ảnh.
SPRITE_MAP = {
    "RF/1 пехота/Т1 Мабута/ГП-25/gp25.ini": "T1_rus_gp25.png",
    "UKR/1 пехота/Т1 Мабута/ГП-25/gp25_ukr.ini": "T1_ukr_gp25.png",
}

# Để True chỉ xem trước; chuyển thành False để ghi thay đổi.
DRY_RUN = True


def is_gp25_config(text: str) -> bool:
    """Nhận diện cấu hình có cơ chế hoặc đạn GP-25."""
    lower = text.lower()
    return (
        "[turret_gp25]" in lower
        or "[projectile_vog25]" in lower
        or "action_gp25_fire" in lower
        or "vog25" in lower
        or "gp-25" in lower
    )


def get_graphics_image(text: str):
    """Đọc khóa image: trong riêng section [graphics]."""
    in_graphics = False

    for line in text.splitlines():
        section = re.match(r"^\s*\[([^\]]+)\]", line)
        if section:
            in_graphics = section.group(1).strip().lower() == "graphics"
            continue

        if in_graphics:
            match = re.match(r"^\s*image\s*:\s*(.*?)\s*$", line, re.IGNORECASE)
            if match:
                return match.group(1)

    return None


def replace_graphics_image(text: str, sprite_name: str) -> str:
    """Thay hoặc thêm image: trong section [graphics], không đụng section khác."""
    lines = text.splitlines(keepends=True)
    in_graphics = False
    image_found = False

    for index, line in enumerate(lines):
        section = re.match(r"^\s*\[([^\]]+)\]", line)
        if section:
            in_graphics = section.group(1).strip().lower() == "graphics"
            continue

        if in_graphics and re.match(r"^\s*image\s*:", line, re.IGNORECASE):
            ending = "\n" if line.endswith("\n") else ""
            indent = re.match(r"^(\s*)", line).group(1)
            lines[index] = f"{indent}image: {sprite_name}{ending}"
            image_found = True
            break

    if image_found:
        return "".join(lines)

    # Nếu chưa có image: trong [graphics], thêm khóa ngay sau section.
    for index, line in enumerate(lines):
        section = re.match(r"^\s*\[([^\]]+)\]", line)
        if section and section.group(1).strip().lower() == "graphics":
            lines.insert(index + 1, f"image: {sprite_name}\n")
            return "".join(lines)

    raise ValueError("Không tìm thấy section [graphics].")


def main():
    candidates = []

    for path in ROOT.rglob("*"):
        if path.suffix.lower() not in {".ini", ".txt"}:
            continue

        try:
            text = path.read_text(encoding="utf-8-sig")
        except UnicodeDecodeError:
            continue

        if is_gp25_config(text):
            candidates.append((path, get_graphics_image(text)))

    print("Các cấu hình có dấu hiệu dùng GP-25:")
    for path, current_image in sorted(candidates):
        print(f"  {path.relative_to(ROOT)}  | image hiện tại: {current_image or '(chưa khai báo)'}")

    print("\nĐồng bộ sprite theo SPRITE_MAP:")
    for relative_config, sprite_name in SPRITE_MAP.items():
        config_path = ROOT / relative_config
        sprite_path = config_path.parent / sprite_name

        if not config_path.is_file():
            print(f"  BỎ QUA: không tìm thấy cấu hình: {relative_config}")
            continue

        if not sprite_path.is_file():
            print(f"  BỎ QUA: không tìm thấy sprite: {sprite_path.relative_to(ROOT)}")
            continue

        text = config_path.read_text(encoding="utf-8-sig")
        if not is_gp25_config(text):
            print(f"  BỎ QUA: file không nhận diện là cấu hình GP-25: {relative_config}")
            continue

        old_image = get_graphics_image(text)
        if old_image == sprite_name:
            print(f"  ĐÃ KHỚP: {relative_config} -> {sprite_name}")
            continue

        updated = replace_graphics_image(text, sprite_name)

        if DRY_RUN:
            print(f"  XEM TRƯỚC: {relative_config}")
            print(f"    {old_image or '(chưa có image)'} -> {sprite_name}")
        else:
            backup_path = config_path.with_suffix(config_path.suffix + ".bak")
            shutil.copy2(config_path, backup_path)
            config_path.write_text(updated, encoding="utf-8")
            print(f"  ĐÃ SỬA: {relative_config} -> {sprite_name}")
            print(f"    Bản sao lưu: {backup_path.name}")


if __name__ == "__main__":
    main()