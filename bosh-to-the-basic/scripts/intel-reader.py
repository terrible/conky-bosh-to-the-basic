"""Compatibility entry point for the original two-line Intel output."""
from hardware_metrics import intel_load


if __name__ == "__main__":
    load = intel_load()
    if load is None:
        print("${alignr}N/D\n ")
    else:
        print(f"${{alignr}}{load:.2f}%")
        print(f"${{execbar 4,259 echo {load:.2f}}}")
