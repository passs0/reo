# RE: Outbreak — macOS Native App Compiler

Turn your legal PS2 **Resident Evil Outbreak** disc image into a standalone, native Apple Silicon macOS application bundle (`.app`) with a single command or drag-and-drop.

* **No Windows launchers**
* **No emulators or Wine/Rosetta**
* **Pure static recompilation:** Native ARM64 code → Vulkan compute → MoltenVK → Metal

---

## ✨ Features

- **One-Step Compiler:** Drag and drop your `.iso` into the script, and it outputs a double-clickable macOS `.app` bundle.
- **Auto-Detection:** Automatically identifies and verifies whether your disc is **File #1** or **File #2**.
- **Self-Contained Bundle:** Generates a complete macOS app (`Resident Evil Outbreak.app` or `Resident Evil Outbreak - File #2.app`) complete with native high-res application icons, bundled shaders, and MoltenVK libraries.
- **Apple Silicon Native:** High performance on M1 / M2 / M3 / M4 Macs using hardware Metal scanout and multi-threaded parallel-GS.
- **Native Saves:** Game saves and memory cards are managed in `~/Library/Application Support/OutbreakRecomp/`.

---

## 💿 Supported Games

You must provide your own legally dumped disc image (BYOG model). The compiler verifies the executable's SHA-256 hash:

* **Resident Evil Outbreak (File #1):** NTSC-U v2.00 (`SLUS-20765`)
* **Resident Evil Outbreak File #2:** NTSC-U v1.05 (`SLUS-20984`)

*(PAL and Japanese versions are not supported by the underlying recompilation tables).*

---

## 🛠 Prerequisites

* **Hardware:** Any Apple Silicon Mac (M1/M2/M3/M4, macOS 12 Monterey or newer).
* **Xcode Command Line Tools:**
  ```zsh
  xcode-select --install
  ```
* **Required Build Tools (via Homebrew):**
  ```zsh
  brew install cmake ninja glslang spirv-tools molten-vk vulkan-headers
  ```
  *(Or simply pass `--install-deps` to the compiler script to install them automatically).*

---

## 🚀 Quick Start

### Method 1: Drag & Drop (Easiest)

1. Double-click **`MakeOutbreakApp.command`** in Finder.
2. Drag and drop your Outbreak `.iso` file into the Terminal window.
3. Press **Enter**.
4. The script will verify your game, compile the engine, and output your standalone `.app` bundle.

---

### Method 2: Terminal Command

Clone this repository and run:

```zsh
git clone https://github.com/passs0/reo.git
cd reo

# Basic build (creates a self-contained .app)
./MakeOutbreakApp.command "/path/to/Resident Evil Outbreak.iso"
```

#### Useful CLI Options

You can also run the Python script directly:

```zsh
# Output the .app directly to your Desktop or Applications folder
python3 make_mac_app.py "/path/to/game.iso" -o ~/Desktop

# Symlink the ISO instead of embedding it (saves ~2-4 GB disk space)
python3 make_mac_app.py "/path/to/game.iso" --link-iso

# Specify parallel compiler threads (defaults to all CPU cores)
python3 make_mac_app.py "/path/to/game.iso" -j 8

# Automatically install missing dependencies via Homebrew
python3 make_mac_app.py "/path/to/game.iso" --install-deps
```

---

## 🎮 Controls & Settings

### Default Keyboard Controls

| PS2 Button | Mac Key |
| :--- | :--- |
| **D-Pad** | `W` / `A` / `S` / `D` |
| **Left Stick** | `W` / `A` / `S` / `D` |
| **Right Stick** | Arrow Keys |
| **Cross (✕)** | `Space` |
| **Circle (○)** | `E` |
| **Square (□)** | `Q` |
| **Triangle (△)** | `R` |
| **Start / Select** | `Return` / `Delete` |
| **L1 / R1** | `1` / `2` |
| **L2 / R2** | `3` / `4` |
| **L3 / R3** | `Z` / `X` |

*Controllers (DualSense, DualShock 4, Xbox) are automatically supported via macOS native GameController framework.*

### Saves & Memory Cards

Memory cards are kept in your user directory so updating or moving the app won't touch your save data:
```
~/Library/Application Support/OutbreakRecomp/memory-cards/default/data
```

---

## ⚖️ Legal & Disclaimer

This is an unofficial, open-source fan project. **No copyrighted game files, ISOs, or proprietary assets are included in this repository.** Users must provide their own legally acquired disc image to compile the game.

## 🤝 Credits & Upstream

* Upstream project: [Ninjacornix/reo](https://github.com/Ninjacornix/reo)
* Static Recompilation: [PS2Recomp](https://github.com/sp00nznet/PS2Recomp)
* GPU Emulation: [paraLLEl-GS](https://github.com/Arntzen-Software/parallel-gs) & [Granite](https://github.com/Themaister/Granite)
* Metal Translation: [MoltenVK](https://github.com/KhronosGroup/MoltenVK)
