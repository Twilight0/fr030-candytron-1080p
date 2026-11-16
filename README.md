# fr-030: Candytron — 1080p Fullscreen Edition

A patched 1920×1080 fullscreen build of Farbrausch's classic 64k demoscene intro **fr-030: Candytron** (`fr030-candytron-final-101.exe`), originally hardcoded to 800×600 (4:3) fullscreen.

- **Download:** Grab `fr030-candytron-final-101-1080p.exe` from the [Releases](../../releases) page.
- **Video:** Watch it running in 1080p on YouTube: https://youtu.be/AVm_lttiOq0

## Compatibility

- **Linux (Stock Wine):** Runs out of the box on stock Wine (`wine fr030-candytron-final-101-1080p.exe`) with no special overrides or wrappers required.
- **Windows:** Runs natively on Windows (DirectX 9).

---

## Technical Analysis of the Original Executable

### 1. Packer & PE Layout (`kkrunchy`)
The original `fr030-candytron-final-101.exe` is **65,536 bytes** (64 KiB, SHA-256: `2b437a3629f2c815be92df0765af8acd8a185eb3a59cd1fe95a11dce2a99cdc4`):

- **Overlapping DOS/PE Header:** Uses a custom compact PE32 (`i386`) header with `e_lfanew = 0x0c` and `"farb"` (`0x6166`, `0x6272`) embedded in the DOS MZ header fields, followed immediately by the `kkrunchy` compressed bitstream at file offset `0xd4` (`0x4000d4`).
- **Single Section:** One `kkrunchy` section (`0x401000`–`0x410000` on disk, `SizeOfImage = 0xb5f000` / ~11.4 MiB in virtual memory for unpacked code, data, and procedural generation buffers).
- **Decompression Stub (`0x40fdc3`):**
  - Initializes an arithmetic/range decoder state at `0x410000` (`ebp`) and decompresses the payload to `0x410dcb`–`0x440985` (~195.5 KiB).
  - Applies an x86 `call`/`jmp` (`0xe8`/`0xe9`) big-endian relative-offset filter over `0x411000`–`0x420000`.
  - Uses only `LoadLibraryA` and `GetProcAddress` from `KERNEL32.DLL` to dynamically resolve the intro's import table before jumping to the Original Entry Point (OEP) at `0x4110f2`.

### 2. Compiler, Runtime & Libraries
- **Architecture & Toolchain:** 32-bit x86 (`PE32`), compiled with MSVC-style calling conventions (`cdecl`, `stdcall`, and `thiscall` register usage) without `msvcrt.dll` — memory allocation (`0x411041` / `0x41104a`) wraps `GetProcessHeap`, `HeapAlloc`, and `HeapFree` directly.
- **Graphics (`d3d9.dll`):** Loaded dynamically via `LoadLibraryA` + `GetProcAddress("Direct3DCreate9")` with SDK version `0x1f` (31).
  - Attempts `D3DCREATE_HARDWARE_VERTEXPROCESSING` (`0x40`) and falls back to `D3DCREATE_SOFTWARE_VERTEXPROCESSING` (`0x20`).
  - Allocates a 1024×1024 surface/render target, 16×16 textures, and pre-fills a `0x40000`-byte index/quad buffer (`0x5555` quads).
- **Audio (`dsound.dll`, `WINMM.dll`):** Loaded dynamically via `LoadLibraryA` + `GetProcAddress("DirectSoundCreate8")` for procedural audio synthesis, paired with `timeBeginPeriod(1)` and `timeGetTime` for timing.
- **Windowing & Typography (`USER32.dll`, `GDI32.dll`):**
  - Window management via `RegisterClassA`, `CreateWindowExA`, `ShowCursor`, `SetCursorPos`, `GetAsyncKeyState`, `GetMessageA`, `TranslateMessage`, `DispatchMessageA`, and `MessageBoxA` (e.g., `"directx 9 needed"` fallback).
  - Text/glyph rasterization via `CreateFontIndirectA` (`"arial"`), `CreateCompatibleDC`, `CreateCompatibleBitmap`, `ExtTextOutA`, and `GetDIBits` / `SetDIBits`.

### 3. Why It Couldn't Run in 16:9 Natively & What Was Patched
The original executable has **no** PE resources (`0` dialog/UI resources), **no** command-line parsing (`GetCommandLine*` is not imported), and **no** display mode enumeration (`EnumDisplaySettings*` / `GetSystemMetrics` are not imported).

Instead, **800×600 (4:3) exclusive fullscreen** is hardcoded in two places:
1. **`CreateWindowExA` (`0x4111ce`–`0x4111ef`):** `nWidth = 0x320` (`800`) at `0x4111da`, `nHeight = 0x258` (`600`) at `0x4111d5`, `dwStyle = 0x80000000` (`WS_POPUP`), `dwExStyle = 0x8` (`WS_EX_TOPMOST`).
2. **`D3DPRESENT_PARAMETERS` (`0x4119bf`–`0x411a48`):** `BackBufferWidth = 0x320` (`800`) at `0x4119e2`, `BackBufferHeight = 0x258` (`600`) at `0x4119e7`, `BackBufferFormat = 0x16` (`D3DFMT_X8R8G8B8`), `Windowed = 0` (`FALSE`), `SwapEffect = 3` (`D3DSWAPEFFECT_COPY`).

To produce `fr030-candytron-final-101-1080p.exe`:
- The `kkrunchy`-decompressed image (`0x410000`–`0x441000`) was dumped at the OEP and rebuilt into a standard, unpacked PE32 binary with a valid `.idata` import directory (`WINMM.dll`, `KERNEL32.dll`, `USER32.dll`, `GDI32.dll`).
- All four hardcoded resolution immediates (`0x4111d5`, `0x4111da`, `0x4119e2`, `0x4119e7`) were patched from `800×600` (`0x320 × 0x258`) to `1920×1080` (`0x780 × 0x438`).
