import argparse
import asyncio
import xml.etree.ElementTree as ET
from contextlib import suppress
from pathlib import Path

from pymobiledevice3.remote.userspace_tunnel import UserspaceRsdTunnel
from pymobiledevice3.services.dvt.instruments.dvt_provider import DvtProvider
from pymobiledevice3.services.dvt.instruments.location_simulation import LocationSimulation


def first_gpx_point(gpx_file: Path) -> tuple[float, float]:
    root = ET.parse(gpx_file).getroot()
    for element in root.iter():
        if element.tag.rsplit("}", 1)[-1] != "trkpt":
            continue

        return float(element.attrib["lat"]), float(element.attrib["lon"])

    raise ValueError(f"GPX contains no <trkpt>: {gpx_file}")


def validate_point(latitude: float, longitude: float) -> None:
    if not -90 <= latitude <= 90:
        raise ValueError("latitude must be between -90 and 90")
    if not -180 <= longitude <= 180:
        raise ValueError("longitude must be between -180 and 180")


async def follow_gpx(gpx_file: Path, initial_point: tuple[float, float]) -> None:
    if not gpx_file.is_file():
        raise FileNotFoundError(f"GPX file not found: {gpx_file}")

    print(f"GPX: {gpx_file}", flush=True)

    # iOS 17+ developer services need an RSD connection. The userspace tunnel
    # provides one over USB without requiring administrator privileges.
    async with UserspaceRsdTunnel() as rsd:
        async with DvtProvider(rsd) as dvt:
            async with LocationSimulation(dvt) as location:
                try:
                    latitude, longitude = initial_point
                    await location.set(latitude, longitude)
                    print(
                        f"Fixed location: {latitude:.6f}, {longitude:.6f}",
                        flush=True,
                    )
                    print("按 Enter 开始按路线移动，按 Ctrl+C 退出。", flush=True)

                    # Keep the event loop running while waiting for input so the
                    # userspace tunnel and location session remain active.
                    await asyncio.to_thread(input)

                    print("开始移动。", flush=True)
                    await location.play_gpx_file(
                        str(gpx_file),
                        timing_randomness_range=0,
                        disable_sleep=False,
                    )
                finally:
                    # Passing Ctrl+C still restores the device's real location.
                    with suppress(Exception):
                        await location.clear()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Play a GPX route on an iOS device.")
    parser.add_argument(
        "gpx_file",
        type=Path,
        help="GPX file to play",
    )
    parser.add_argument(
        "--start",
        nargs=2,
        type=float,
        metavar=("LAT", "LON"),
        help="fixed waiting point; defaults to the first GPX track point",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    initial_point = tuple(args.start) if args.start else first_gpx_point(args.gpx_file)
    validate_point(*initial_point)
    asyncio.run(follow_gpx(args.gpx_file, initial_point))
