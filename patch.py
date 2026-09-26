#!/usr/bin/env python3
"""
Patches Earth & Water 1.0.5-hotfix1 (26.1.x) to fix a random title-screen crash.

Bug: its SplashTextMixin adds 13 splash texts to the title screen's splash list as
plain Strings:

    splashes.add(Component.translatable("splash.earth-and-water.herobrine").getString());

In 26.1.2 that list (SplashManager.splashes) holds Components, not Strings, and the
mixin's @Shadow field still declares List<String>, so nothing stops it at load time.
The game only breaks when the title screen randomly picks one of those 13 entries:
SplashManager.getSplash casts it to Component and throws

    ClassCastException: class java.lang.String cannot be cast to class
    net.minecraft.network.chat.Component

Found 2026-09-26 on the Working test client; the same crash had already hit it on
2026-09-20 and 2026-09-21. Any player could hit it on any launch.

Fix: drop the `.getString()` call, so the MutableComponent from
Component.translatable goes into the list as-is. Each of the 13 entries compiles to

    invokestatic  Component.translatable   B8 00 14
    invokevirtual MutableComponent.getString B6 00 1A   <- replaced by 3x nop
    invokeinterface List.add, 2             B9 00 20 02 00

getString pops one reference and pushes one, and List.add takes any Object, so
replacing it with three nops is length-preserving and stack-neutral. No branch
targets fall between these instructions, so no StackMapTable frame changes.

Usage:
    python3 patch.py <path-to-earth-and-water-1.0.5-hotfix1-26.1.x.jar>

Patches the jar in place (after making a `.bak` backup alongside it).
"""
import shutil
import sys
import zipfile
from pathlib import Path

ENTRY = "potatowolfie/earth_and_water/mixin/SplashTextMixin.class"
EXPECTED = 13

OLD_PATTERN = bytes.fromhex("B80014B6001AB900200200")
NEW_PATTERN = bytes.fromhex("B80014000000B900200200")


def patch_class(data: bytes) -> bytes:
    count = data.count(OLD_PATTERN)
    if count == 0:
        if data.count(NEW_PATTERN) == EXPECTED:
            print("Already patched, nothing to do.")
            return data
        raise SystemExit(
            "Expected byte pattern not found - this jar's SplashTextMixin.class doesn't "
            "match the known 1.0.5-hotfix1 build. Re-check with javap -p -c first."
        )
    if count != EXPECTED:
        raise SystemExit(f"Expected {EXPECTED} matches, found {count} - refusing to guess.")
    return data.replace(OLD_PATTERN, NEW_PATTERN)


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)

    jar_path = Path(sys.argv[1])
    backup_path = jar_path.with_suffix(jar_path.suffix + ".bak")

    with zipfile.ZipFile(jar_path, "r") as zin:
        if ENTRY not in zin.namelist():
            raise SystemExit(f"{ENTRY} not found in {jar_path} - wrong jar?")
        class_data = zin.read(ENTRY)

    patched = patch_class(class_data)
    if patched is class_data:
        return

    if not backup_path.exists():
        shutil.copy2(jar_path, backup_path)
        print(f"Backed up original to {backup_path}")

    tmp_path = jar_path.with_suffix(jar_path.suffix + ".tmp")
    with zipfile.ZipFile(jar_path, "r") as zin, zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = patched if item.filename == ENTRY else zin.read(item.filename)
            zout.writestr(item, data)

    tmp_path.replace(jar_path)
    print(f"Patched {jar_path}")


if __name__ == "__main__":
    main()
