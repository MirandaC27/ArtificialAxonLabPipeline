#This script exist because 3D image processing in pyimagej was probably a form of medieval torture at some point.
import imagej
import scyjava

ij = imagej.init("sc.fiji:fiji", mode="headless")
print(f"ImageJ version: {ij.getVersion()}")


import jpype
cp = str(jpype.java.lang.System.getProperty("java.class.path"))
entries = cp.split(":")

print("Classpath entries containing '3d' or 'mcib':")
matches = [e for e in entries if "3d" in e.lower() or "mcib" in e.lower()]
if matches:
    for e in matches: print(f"  {e}")
else:
    print("  (none found)")

print(f"\nTotal classpath entries: {len(entries)}")
