#!/usr/bin/env python3
"""
Turn a Resident Evil Outbreak PS2 ISO into a standalone native macOS .app bundle.
No launcher required. Fully standalone and Apple Silicon native.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import plistlib
import shlex
import shutil
import struct
import subprocess
import sys
import tempfile
import urllib.request

ROOT = Path(__file__).resolve().parent

SECTOR = 2048

GAMES = {
    "file1": {
        "elf": "SLUS_207.65",
        "title": "Resident Evil Outbreak",
        "app_name": "Resident Evil Outbreak.app",
        "bundle_id": "net.ninjacornix.reo.file1",
        "sha256": "06bd5fd7243144cd30cdd0c0023763a369738cb91b177b35e85f6a4782b4ca46",
        "binary_name": "reo_recomp",
        "cover_url": "https://images.launchbox-app.com/2584a6d0-4316-40a3-8c04-56d267fd2d83.jpg",
    },
    "file2": {
        "elf": "SLUS_209.84",
        "title": "Resident Evil Outbreak File #2",
        "app_name": "Resident Evil Outbreak - File #2.app",
        "bundle_id": "net.ninjacornix.reo.file2",
        "sha256": "5c0411a26247ef9974cd94b844ac5aecbcbf4705db543f51814aeed89da0fd8d",
        "binary_name": "reo_recomp_file2",
        "cover_url": "https://images.launchbox-app.com/r2_926a0694-7890-456a-a9f0-cf4b84571e2c.jpg",
    },
}

REQUIRED_BREW_PKGS = [
    "cmake",
    "ninja",
    "glslang",
    "spirv-tools",
    "molten-vk",
    "vulkan-headers",
]


def ensure_brew_path():
    for p in ["/opt/homebrew/bin", "/usr/local/bin"]:
        if p not in os.environ.get("PATH", "") and Path(p).exists():
            os.environ["PATH"] = f"{p}:{os.environ.get('PATH', '')}"


def find_molten_library():
    override = os.environ.get("GRANITE_VULKAN_LIBRARY")
    candidates = [Path(override)] if override else []
    sdk = os.environ.get("VULKAN_SDK")
    if sdk:
        candidates.append(Path(sdk) / "lib/libMoltenVK.dylib")
    candidates += [
        Path("/opt/homebrew/lib/libMoltenVK.dylib"),
        Path("/usr/local/lib/libMoltenVK.dylib"),
    ]
    for c in candidates:
        if c.is_file():
            return c.resolve()
    return None


def check_dependencies(auto_install=False):
    ensure_brew_path()
    if sys.platform != "darwin" or platform.machine() != "arm64":
        sys.exit("Error: This port requires an Apple Silicon Mac (macOS on ARM64).")

    if not shutil.which("clang"):
        sys.exit(
            "Error: Xcode Command Line Tools not found. Run 'xcode-select --install' first."
        )

    missing_tools = []
    for cmd in ["git", "cmake", "ninja", "glslangValidator", "spirv-val"]:
        if not shutil.which(cmd):
            missing_tools.append(cmd)

    molten_dylib = find_molten_library()
    if not molten_dylib:
        missing_tools.append("libMoltenVK.dylib")

    if missing_tools:
        print(f"Missing build prerequisites: {', '.join(missing_tools)}")
        brew_bin = shutil.which("brew") or "/opt/homebrew/bin/brew"
        if not Path(brew_bin).exists():
            sys.exit(
                "Error: Homebrew is required to install dependencies.\n"
                "Install Homebrew from https://brew.sh or install the missing tools manually."
            )

        if auto_install:
            print(f"Installing required packages via Homebrew: {' '.join(REQUIRED_BREW_PKGS)}...")
            subprocess.run([brew_bin, "install"] + REQUIRED_BREW_PKGS, check=True)
            ensure_brew_path()
            molten_dylib = find_molten_library()
            if not molten_dylib:
                sys.exit("Error: Could not locate libMoltenVK.dylib even after brew install.")
        else:
            print("\nPlease install the required packages with:")
            print(f"  brew install {' '.join(REQUIRED_BREW_PKGS)}\n")
            sys.exit("Rerun this script after installing dependencies, or pass --install-deps.")

    return molten_dylib


def inspect_iso(path: Path):
    if not path.is_file():
        return None, f"File does not exist: {path}"

    with path.open("rb") as f:
        pvd = None
        for i in range(16, 80):
            f.seek(i * SECTOR)
            buf = f.read(SECTOR)
            if len(buf) < SECTOR or buf[1:7] != b"CD001\x01":
                continue
            if buf[0] == 1:
                pvd = buf
                break
            if buf[0] == 255:
                break

        if not pvd:
            return None, "File is not a valid ISO9660 disc image."

        root_extent = struct.unpack_from("<I", pvd, 158)[0]
        root_size = struct.unpack_from("<I", pvd, 166)[0]

        f.seek(root_extent * SECTOR)
        root_dir = f.read(root_size)

        pos = 0
        detected_game = None
        elf_lba = 0
        elf_len = 0
        while pos < len(root_dir):
            length = root_dir[pos]
            if length == 0:
                pos = (pos // SECTOR + 1) * SECTOR
                continue
            record = root_dir[pos : pos + length]
            pos += length
            if length < 34:
                continue
            name_len = record[32]
            name = (
                record[33 : 33 + name_len]
                .decode("ascii", errors="ignore")
                .split(";", 1)[0]
                .rstrip(".")
            )
            for gkey, ginfo in GAMES.items():
                if name.upper() == ginfo["elf"].upper():
                    detected_game = gkey
                    elf_lba = struct.unpack_from("<I", record, 2)[0]
                    elf_len = struct.unpack_from("<I", record, 10)[0]
                    break
            if detected_game:
                break

        if not detected_game:
            return (
                None,
                "Could not find Outbreak File #1 (SLUS-207.65) or File #2 (SLUS-209.84) in the ISO.",
            )

        f.seek(elf_lba * SECTOR)
        elf_bytes = f.read(elf_len)
        elf_sha = hashlib.sha256(elf_bytes).hexdigest()
        expected = GAMES[detected_game]["sha256"]

        if elf_sha != expected:
            return (
                None,
                f"Found {GAMES[detected_game]['title']}, but SHA-256 hash does not match.\n"
                f"Expected: {expected}\n"
                f"Found:    {elf_sha}\n"
                "Note: Only the official NTSC-U releases are currently supported by the recompiler:\n"
                "  - File #1: NTSC-U v2.00 (SLUS-20765)\n"
                "  - File #2: NTSC-U v1.05 (SLUS-20984)",
            )

        return detected_game, None


def generate_icns_from_image(image_path: Path, output_icns: Path):
    """Builds a high-res macOS squircle icon (.icns) from a cover art image."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        converted_png = tmp / "base.png"
        square_png = tmp / "square.png"

        # Convert image to PNG
        subprocess.run(
            ["sips", "-s", "format", "png", str(image_path), "--out", str(converted_png)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        # Scale preserving aspect ratio within 1024x1024 box, then pad with stylish dark border
        subprocess.run(
            ["sips", "-z", "1024", "724", str(converted_png), "--out", str(converted_png)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        subprocess.run(
            [
                "sips",
                "-p",
                "1024",
                "1024",
                "--padColor",
                "111417",
                str(converted_png),
                "--out",
                str(square_png),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        # Generate standard iconset sizes
        iconset = tmp / "AppIcon.iconset"
        iconset.mkdir()
        for size in [16, 32, 64, 128, 256, 512]:
            subprocess.run(
                [
                    "sips",
                    "-z",
                    str(size),
                    str(size),
                    str(square_png),
                    "--out",
                    str(iconset / f"icon_{size}x{size}.png"),
                ],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            subprocess.run(
                [
                    "sips",
                    "-z",
                    str(size * 2),
                    str(size * 2),
                    str(square_png),
                    "--out",
                    str(iconset / f"icon_{size}x{size}@2x.png"),
                ],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        subprocess.run(
            ["iconutil", "-c", "icns", str(iconset), "-o", str(output_icns)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    return True


def prepare_cover_icon(game_key: str, custom_cover: Path, output_icns: Path):
    """Obtains cover art (custom, downloaded, or bundled fallback) and builds AppIcon.icns."""
    if custom_cover and custom_cover.is_file():
        print(f"Using custom cover art: {custom_cover.name}")
        try:
            generate_icns_from_image(custom_cover, output_icns)
            return
        except Exception as e:
            print(f"Warning: Failed to process custom cover ({e}), trying online cover art...")

    # Try downloading official retail cover scan
    cover_url = GAMES[game_key].get("cover_url")
    if cover_url:
        print(f"Fetching official retail cover art for {GAMES[game_key]['title']}...")
        try:
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp_file:
                tmp_path = Path(tmp_file.name)
            req = urllib.request.Request(
                cover_url,
                headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"},
            )
            with urllib.request.urlopen(req, timeout=10) as resp, open(tmp_path, "wb") as out:
                out.write(resp.read())
            generate_icns_from_image(tmp_path, output_icns)
            tmp_path.unlink(missing_ok=True)
            print("Successfully generated high-resolution cover art app icon!")
            return
        except Exception as e:
            print(f"Notice: Online cover download skipped ({e}). Using bundled icon.")

    # Fallback: launcher/Assets/app-icon.png
    fallback_png = ROOT / "launcher/Assets/app-icon.png"
    if fallback_png.is_file():
        generate_icns_from_image(fallback_png, output_icns)


def create_app_bundle(
    game_key: str,
    executable: Path,
    shaders_dir: Path,
    data_dir: Path,
    iso_path: Path,
    molten_dylib: Path,
    output_dir: Path,
    custom_cover: Path = None,
    resolution_scale: int = 4,
    post_aa: str = "smaa",
    fullscreen: bool = True,
    embed_iso: bool = True,
):
    game = GAMES[game_key]
    app_path = output_dir / game["app_name"]
    print(f"\nPackaging standalone macOS application bundle: {app_path.name}")

    if app_path.exists():
        shutil.rmtree(app_path)

    contents = app_path / "Contents"
    macos = contents / "MacOS"
    frameworks = contents / "Frameworks"
    resources = contents / "Resources"
    macos.mkdir(parents=True, exist_ok=True)
    frameworks.mkdir(parents=True, exist_ok=True)
    resources.mkdir(parents=True, exist_ok=True)

    # 1. Executable and shaders
    dest_exe = macos / game["binary_name"]
    shutil.copy2(executable, dest_exe)
    dest_exe.chmod(0o755)

    if shaders_dir.is_dir():
        shutil.copytree(shaders_dir, macos / "reo-gpu-present", dirs_exist_ok=True)

    # 2. MoltenVK framework
    shutil.copy2(molten_dylib, frameworks / "libMoltenVK.dylib")

    # 3. Game Assets & ISO
    res_data = resources / "data"
    print(f"Bundling extracted game assets into {res_data.name}...")
    shutil.copytree(data_dir, res_data, dirs_exist_ok=True)

    dest_iso = resources / "game.iso"
    if embed_iso:
        print(f"Embedding disc image into app bundle (standalone mode)...")
        try:
            os.link(iso_path, dest_iso)
        except OSError:
            shutil.copy2(iso_path, dest_iso)
    else:
        print(f"Symlinking disc image to app bundle (--link-iso mode)...")
        dest_iso.symlink_to(iso_path.resolve())

    # 4. App Icon (Original retail cover art)
    prepare_cover_icon(game_key, custom_cover, resources / "AppIcon.icns")

    # 5. Launch Script (Outbreak)
    elf_name = game["elf"]
    launch_script = f"""#!/bin/zsh
set -eu

app_contents="$(cd "$(dirname "$0")/.." && pwd)"
user_data="$HOME/Library/Application Support/OutbreakRecomp"
mkdir -p "$user_data/memory-cards/default/data"
cd "$user_data"

export GRANITE_VULKAN_LIBRARY="$app_contents/Frameworks/libMoltenVK.dylib"
export REO_MC0_ROOT="${{REO_MC0_ROOT:-$user_data/memory-cards/default/data}}"
export REO_MC1_ROOT="${{REO_MC1_ROOT:-:none:}}"

if [[ -f "$app_contents/Resources/game.iso" ]]; then
    export REO_ISO="$app_contents/Resources/game.iso"
elif [[ -L "$app_contents/Resources/game.iso" ]]; then
    export REO_ISO="$(readlink "$app_contents/Resources/game.iso")"
fi

# Graphics Quality & Anti-Aliasing (Fixes pixelation on Retina displays)
: ${{REO_INTERNAL_RESOLUTION:="{resolution_scale}"}}    # 4 = 4x scale (4K Ultra supersampled), 2 = 2x HD, 1 = native 480p
: ${{REO_DISPLAY_FILTER:="linear"}}                    # Smooth bilinear texture sampling (toggle with F2)
: ${{REO_POST_AA:="{post_aa}"}}                         # Hardware edge smoothing: smaa or fxaa
: ${{REO_FULLSCREEN:="{'1' if fullscreen else '0'}"}}  # 1 = Native macOS fullscreen (triggers Apple Game Mode)

# Core engine settings
: ${{REO_NATURAL:="1"}}
: ${{REO_TURBO:="1"}}
: ${{REO_GS_BACKEND:="parallel"}}
: ${{REO_GS_THREAD:="1"}}
: ${{REO_GS_GPU_PRESENT:="1"}}
: ${{REO_GS_DISPATCH_PACE:="2"}}
: ${{REO_GS_SPRITE_DEPTH_PARALLEL:="1"}}
: ${{REO_VIF1_GPU_RESIDENT:="0"}}
: ${{REO_VIF1_ASYNC:="1"}}
: ${{REO_DEBUG_PANEL:="0"}}
: ${{REO_GPU_MOVIE:="0"}}

export REO_NATURAL REO_TURBO REO_GS_BACKEND REO_GS_THREAD REO_GS_GPU_PRESENT
export REO_GS_DISPATCH_PACE REO_GS_SPRITE_DEPTH_PARALLEL REO_VIF1_GPU_RESIDENT
export REO_VIF1_ASYNC REO_INTERNAL_RESOLUTION REO_DISPLAY_FILTER REO_POST_AA
export REO_FULLSCREEN REO_DEBUG_PANEL REO_GPU_MOVIE

data_dir="$app_contents/Resources/data"
elf_file="$data_dir/{elf_name}"

exec "$app_contents/MacOS/{game['binary_name']}" --game {game_key} --elf "$elf_file" --data "$data_dir"
"""
    runner = macos / "Outbreak"
    runner.write_text(launch_script)
    runner.chmod(0o755)

    # 6. Info.plist & PkgInfo (Configured for macOS Game Mode recognition)
    plist_data = {
        "CFBundleIdentifier": game["bundle_id"],
        "CFBundleName": game["title"],
        "CFBundleDisplayName": game["title"],
        "CFBundleExecutable": "Outbreak",
        "CFBundleIconFile": "AppIcon",
        "CFBundlePackageType": "APPL",
        "CFBundleShortVersionString": "1.0.0",
        "CFBundleVersion": "1",
        "LSMinimumSystemVersion": "12.0",
        "NSHighResolutionCapable": True,
        "LSApplicationCategoryType": "public.app-category.games",
    }
    with (contents / "Info.plist").open("wb") as f:
        plistlib.dump(plist_data, f)
    (contents / "PkgInfo").write_bytes(b"APPL????")

    # 7. Ad-hoc codesign
    try:
        subprocess.run(
            ["codesign", "-s", "-", "--force", "--deep", str(app_path)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception as e:
        print(f"Notice: Ad-hoc signing note: {e}")

    return app_path


def clean_input_path(path_str: str) -> Path:
    s = path_str.strip().strip("'\"")
    s = s.replace("\\ ", " ")
    return Path(os.path.expanduser(s)).resolve()


def main():
    parser = argparse.ArgumentParser(
        description="Compile a Resident Evil Outbreak PS2 ISO into a standalone native macOS App."
    )
    parser.add_argument(
        "iso",
        nargs="?",
        type=str,
        help="Path to Resident Evil Outbreak File #1 or File #2 PS2 ISO",
    )
    parser.add_argument(
        "--jobs",
        "-j",
        type=int,
        default=max(1, os.cpu_count() or 4),
        help="Number of parallel compiler jobs (default: CPU cores)",
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        type=Path,
        default=ROOT,
        help="Directory to place the final .app bundle (default: current repository)",
    )
    parser.add_argument(
        "--cover",
        type=Path,
        help="Path to a custom cover image file (.jpg or .png) to use as app icon",
    )
    parser.add_argument(
        "--resolution",
        type=int,
        choices=[1, 2, 4],
        default=4,
        help="Internal rendering resolution scale: 1 (native 480p), 2 (2x HD), 4 (4x 4K Ultra, default)",
    )
    parser.add_argument(
        "--post-aa",
        choices=["smaa", "fxaa", "none"],
        default="smaa",
        help="Post-processing anti-aliasing method: smaa (default, crisp edge smoothing), fxaa (soft), or none",
    )
    parser.add_argument(
        "--windowed",
        action="store_true",
        help="Start in windowed mode instead of fullscreen (note: fullscreen triggers macOS Game Mode)",
    )
    parser.add_argument(
        "--link-iso",
        action="store_true",
        help="Symlink the ISO instead of embedding it into the app bundle (saves ~2-4 GB)",
    )
    parser.add_argument(
        "--install-deps",
        action="store_true",
        help="Automatically install missing Homebrew dependencies",
    )
    args = parser.parse_args()

    ensure_brew_path()
    molten_dylib = check_dependencies(auto_install=args.install_deps)

    iso_str = args.iso
    if not iso_str:
        print("\n=======================================================")
        print("  Resident Evil Outbreak - macOS Native App Compiler   ")
        print("=======================================================\n")
        try:
            iso_str = input("Drag and drop your Outbreak ISO file here, then press Enter: ")
        except (KeyboardInterrupt, EOFError):
            sys.exit("\nAborted.")

    iso_path = clean_input_path(iso_str)
    if not iso_path.exists():
        sys.exit(f"Error: Specified ISO file not found at: {iso_path}")

    print(f"\nAnalyzing ISO: {iso_path.name}...")
    game_key, error = inspect_iso(iso_path)
    if error:
        sys.exit(f"Error: {error}")

    game_info = GAMES[game_key]
    print(f"Recognized Game:     {game_info['title']} ({game_info['elf']})")
    print(f"Target Architecture: Apple Silicon ARM64 (Metal + Vulkan)")
    print(f"Internal Resolution: {args.resolution}x supersampling (anti-pixelation)")
    print(f"Anti-Aliasing:       {args.post_aa.upper()}")
    print(f"Display Mode:        {'Fullscreen (macOS Game Mode enabled)' if not args.windowed else 'Windowed'}")
    print(f"Parallel Jobs:       {args.jobs}\n")

    # Run tools/macos/build.py
    build_dir = ROOT / "build-macos"
    build_script = ROOT / "tools/macos/build.py"
    build_cmd = [
        sys.executable,
        str(build_script),
        "--iso",
        str(iso_path),
        "--game",
        game_key,
        "--jobs",
        str(args.jobs),
        "--build",
        str(build_dir),
    ]

    print("-------------------------------------------------------")
    print(f"Starting recompilation and build pipeline...")
    print("-------------------------------------------------------\n")
    try:
        subprocess.run(build_cmd, cwd=ROOT, check=True)
    except subprocess.CalledProcessError as e:
        sys.exit(f"\nBuild failed with exit code {e.returncode}.")

    # Locate build artifacts from macos-build.json
    record_file = build_dir / "macos-build.json"
    if not record_file.is_file():
        sys.exit(f"Error: Build record not found at {record_file}")

    record = json.loads(record_file.read_text(encoding="utf-8"))
    if game_key == "file1":
        executable = Path(record["executable"])
        data_dir = Path(record["data"])
    else:
        executable = Path(record["file2Executable"])
        data_dir = Path(record["file2Data"])

    shaders_dir = executable.parent / "reo-gpu-present"

    # Create the standalone .app bundle
    app_bundle = create_app_bundle(
        game_key=game_key,
        executable=executable,
        shaders_dir=shaders_dir,
        data_dir=data_dir,
        iso_path=iso_path,
        molten_dylib=molten_dylib,
        output_dir=args.output_dir.resolve(),
        custom_cover=args.cover,
        resolution_scale=args.resolution,
        post_aa=args.post_aa,
        fullscreen=not args.windowed,
        embed_iso=not args.link_iso,
    )

    print("\n=======================================================")
    print(f"  BUILD SUCCEEDED! ")
    print("=======================================================")
    print(f"Application Bundle: {app_bundle.resolve()}")
    print("\n🎮 QUICK CONTROLS CHEAT SHEET:")
    print("  • Move:       W / A / S / D")
    print("  • RUN:        Hold 'Q' while moving (W + Q)")
    print("  • Action:     Space (Cross)")
    print("  • Aim Weapon: Hold '2' (R1)")
    print("  • Shoot/Hit:  Hold '2', then press Space")
    print("  • Tackle:     '4' (R2 special ability)")
    print("  • Inventory:  'R' (Triangle)")
    print("  • Back/Exit:  'E' (Circle)")
    print("  • Toggle AA:  Press 'F2' in-game to toggle bilinear filter")
    print("\nSaves & memory cards are stored at:")
    print("  ~/Library/Application Support/OutbreakRecomp/memory-cards/")
    print("=======================================================\n")


if __name__ == "__main__":
    main()
