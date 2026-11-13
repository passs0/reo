# RE: Outbreak — macOS Native App Compiler

Turn your legal PS2 **Resident Evil Outbreak** disc image into a standalone, native Apple Silicon macOS application bundle (`.app`) with a single command or drag-and-drop.

* **No Windows launchers or .NET/Avalonia bloat**
* **No emulators or Wine/Rosetta**
* **Pure static recompilation:** Native ARM64 code → Vulkan compute → MoltenVK → Metal
* **macOS Game Mode enabled automatically**

---

## ✨ Features

- **One-Step Compiler:** Drag and drop your `.iso` into the script, and it outputs a double-clickable macOS `.app` bundle.
- **Auto-Detection:** Automatically identifies and verifies whether your disc is **File #1** or **File #2**.
- **Authentic Cover Art Icon:** Automatically fetches and formats the official high-resolution retail box cover into a crisp macOS `AppIcon.icns`.
- **Anti-Pixelation & Supersampling:** Runs at **2× or 4× internal resolution** (up to 4K internal render) with hardware **SMAA** edge anti-aliasing and smooth bilinear filtering.
- **macOS Game Mode:** Launches in native macOS Fullscreen Space to automatically activate Apple's high-priority Game Mode on macOS Sonoma / Sequoia.
- **Self-Contained Bundle:** Generates a complete macOS app (`Resident Evil Outbreak.app` or `Resident Evil Outbreak - File #2.app`) with bundled shaders and MoltenVK.
- **Native Saves:** Game saves and memory cards are managed cleanly in `~/Library/Application Support/OutbreakRecomp/`.

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
  *(Or pass `--install-deps` to the compiler script to let it install them for you).*

---

## 🚀 Quick Start

### Method 1: Drag & Drop (Easiest)

1. Double-click **`MakeOutbreakApp.command`** in Finder.
2. Drag and drop your Outbreak `.iso` file into the Terminal window.
3. Press **Enter**.
4. The script will verify your game, compile the engine, download authentic cover art, and output your standalone `.app` bundle.

---

### Method 2: Terminal Command

```zsh
git clone https://github.com/passs0/reo.git
cd reo

# Basic build (creates a self-contained, 2x-supersampled .app)
./MakeOutbreakApp.command "/path/to/Resident Evil Outbreak.iso"
```

#### Custom Options:

```zsh
# 4K Ultra resolution on high-end Macs (M1/M2/M3/M4 Pro/Max):
python3 make_mac_app.py "/path/to/game.iso" --resolution 4

# Use your own custom cover image for the app icon:
python3 make_mac_app.py "/path/to/game.iso" --cover "/path/to/my_art.jpg"

# Output the .app directly to your Applications or Desktop folder:
python3 make_mac_app.py "/path/to/game.iso" -o /Applications

# Symlink the ISO instead of copying it (saves ~2-4 GB disk space):
python3 make_mac_app.py "/path/to/game.iso" --link-iso
```

---

## 🎮 Complete Controls Guide

Resident Evil Outbreak uses the classic PS2 dual-stick survival horror scheme.

### How to Run 🏃‍♂️
* **Keyboard:** Hold **`Q`** (Square) while moving with **`W`, `A`, `S`, `D`**.
* **PlayStation Controller:** Hold **`Square (□)`** while pushing the Left Stick.
* **Xbox Controller:** Hold **`X`** while pushing the Left Stick.
* *Pro Tip:* Go to the in-game **Options → Control** menu and switch from **Type A** to **Type B**. In Type B, pushing the stick or movement key all the way forward runs automatically!

### Complete Keyboard Mapping

| Action | Mac Key | PS2 Equivalent |
| :--- | :--- | :--- |
| **Move / Walk** | `W` / `A` / `S` / `D` | Left Stick / D-Pad |
| **RUN** | **Hold `Q`** while moving | **Square (□)** |
| **Action / Confirm / Attack** | `Space` | **Cross (✕)** |
| **Aim Weapon / Ready Stance** | **Hold `2`** | **R1** |
| **Shoot / Swing Weapon** | Hold `2`, then press `Space` | R1 + Cross |
| **Cancel / Back out of menus** | `E` | **Circle (○)** |
| **Status Screen & Inventory** | `R` | **Triangle (△)** |
| **Tackle / Special Ability** | `4` | **R2** (e.g. Kevin kick, Cindy duck) |
| **Switch Target** | `1` / `3` | **L1** / **L2** |
| **Voice Callouts ("Help!", "Go!")** | **Arrow Keys** | Right Stick |
| **Pause Menu** | `Return` | **Start** |
| **Map / Select** | `Delete` / `Backspace` | **Select** |
| **Toggle Display Filter** | `F2` | Bilinear smoothing on/off |

*Connected gamepads (PS4, PS5, Xbox, Switch Pro) work automatically out-of-the-box via macOS GameController framework.*

---

## 📺 Visuals & Anti-Pixelation

The default settings are tuned specifically for Apple Silicon Retina screens:
* **Internal Resolution:** Defaults to `2` (2× supersampling). You can change it to `4` (4K Ultra) or `1` (original 480p pixel look).
* **Anti-Aliasing:** Hardware SMAA (`REO_POST_AA=smaa`) smooths rough polygon edges without blurring HUD elements.
* **Display Filtering:** Smooth bilinear texture filtering is on by default. Press **`F2`** in-game at any time to toggle between smooth filtering and raw pixels.

---

## 🏆 Apple Game Mode

macOS Sonoma (14) and macOS Sequoia (15) automatically turn on **Game Mode** when the game starts in native fullscreen:
* Gives Outbreak top GPU and CPU scheduling priority.
* Drastically reduces latency for Bluetooth controllers (AirPods, DualSense, Xbox).
* Look for the **Game Mode** badge in the macOS menu bar.

---

## 📁 Saves & Memory Cards

Memory cards are stored in your user directory:
```
~/Library/Application Support/OutbreakRecomp/memory-cards/default/data
```
Deleting or updating your `.app` will never erase your saved games.

---

## ⚖️ Legal & Disclaimer

This is an unofficial, open-source fan project. **No copyrighted game files, ISOs, or proprietary assets are included in this repository.** Users must provide their own legally acquired disc image to compile the game.

## 🤝 Credits & Upstream

* Upstream project: [Ninjacornix/reo](https://github.com/Ninjacornix/reo)
* Static Recompilation: [PS2Recomp](https://github.com/sp00nznet/PS2Recomp)
* GPU Emulation: [paraLLEl-GS](https://github.com/Arntzen-Software/parallel-gs) & [Granite](https://github.com/Themaister/Granite)
* Metal Translation: [MoltenVK](https://github.com/KhronosGroup/MoltenVK)
