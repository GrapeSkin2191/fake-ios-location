import argparse
import asyncio
import os
import sys
import xml.etree.ElementTree as ET
from contextlib import suppress
from ipaddress import ip_address
from pathlib import Path

from pymobiledevice3.bonjour import browse_remotepairing
from pymobiledevice3.remote.tunnel_service import RemotePairingTunnelService
from pymobiledevice3.remote.userspace_tunnel import TunnelProvider, UserspaceRsdTunnel
from pymobiledevice3.services.dvt.instruments.dvt_provider import DvtProvider
from pymobiledevice3.services.dvt.instruments.location_simulation import LocationSimulation


REMOTEPAIRING_PORT = 49152


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


async def wait_for_enter(prompt: str) -> None:
    print(prompt, flush=True)

    # Polling the Windows console keeps the event loop responsive, so Ctrl+C
    # can cancel the wait and the location session can still be cleared.
    if os.name == "nt" and sys.stdin.isatty():
        import msvcrt

        while True:
            await asyncio.sleep(0.05)
            if not msvcrt.kbhit():
                continue

            key = msvcrt.getwch()
            if key == "\x03":
                raise KeyboardInterrupt
            if key in ("\r", "\n"):
                print(flush=True)
                return

    await asyncio.to_thread(input)


def connection_preference(address: str) -> tuple[int, str]:
    """Prefer a normal LAN IPv4 address over VPN and link-local addresses."""
    bare_address = address.split("%", 1)[0]
    try:
        parsed = ip_address(bare_address)
    except ValueError:
        return (3, address)

    if parsed.version == 4:
        if parsed.is_private and not parsed.is_link_local:
            return (0, address)
        return (1, address)
    if parsed.is_link_local:
        return (3, address)
    return (2, address)


async def remote_pairing_provider(
    udid: str,
    host: str | None,
) -> TunnelProvider:
    if host is not None:
        endpoints = [(host, REMOTEPAIRING_PORT)]
    else:
        answers = await browse_remotepairing(timeout=6)
        endpoints = sorted(
            (
                (address.full_ip, answer.port)
                for answer in answers
                for address in answer.addresses
            ),
            key=lambda endpoint: connection_preference(endpoint[0]),
        )
        if not endpoints:
            raise ConnectionError(
                "No RemotePairing device was found over Bonjour. "
                "Check that the iPhone and PC are on the same Wi-Fi network."
            )

    errors: list[str] = []
    for endpoint_host, endpoint_port in dict.fromkeys(endpoints):
        service = RemotePairingTunnelService(
            udid,
            endpoint_host,
            endpoint_port,
            connect_timeout=8,
        )
        try:
            await service.connect(autopair=False)
        except Exception as exc:
            await service.close()
            errors.append(f"{endpoint_host}:{endpoint_port}: {exc}")
            continue

        print(
            f"Wi-Fi: {endpoint_host}:{endpoint_port}",
            flush=True,
        )
        return TunnelProvider(service)

    details = "\n".join(errors)
    raise ConnectionError(f"RemotePairing connection failed:\n{details}")


async def follow_gpx(
    gpx_file: Path,
    initial_point: tuple[float, float],
    tunnel: UserspaceRsdTunnel,
) -> None:
    if not gpx_file.is_file():
        raise FileNotFoundError(f"GPX file not found: {gpx_file}")

    print(f"GPX: {gpx_file}", flush=True)

    # iOS 17+ developer services need an RSD connection. The userspace tunnel
    # provides one without requiring administrator privileges.
    async with tunnel as rsd:
        async with DvtProvider(rsd) as dvt:
            async with LocationSimulation(dvt) as location:
                try:
                    latitude, longitude = initial_point
                    await location.set(latitude, longitude)
                    print(
                        f"Fixed location: {latitude:.6f}, {longitude:.6f}",
                        flush=True,
                    )
                    await wait_for_enter(
                        "按 Enter 开始按路线移动，按 Ctrl+C 随时退出。"
                    )

                    print("开始移动。", flush=True)
                    await location.play_gpx_file(
                        str(gpx_file),
                        timing_randomness_range=0,
                        disable_sleep=False,
                    )
                    await wait_for_enter(
                        "路线移动完成，定位将固定在最后一个点。"
                        "按 Enter 结束并恢复真实定位，按 Ctrl+C 随时退出。"
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
        "--udid",
        help="Target iPhone UDID; use this to force a specific device",
    )
    parser.add_argument(
        "--wireless",
        action="store_true",
        help="Connect through RemotePairing over Wi-Fi",
    )
    parser.add_argument(
        "--wireless-host",
        metavar="IP",
        help="Wi-Fi IPv4 address of the iPhone; implies --wireless",
    )
    args = parser.parse_args()
    if args.wireless_host is not None:
        args.wireless = True
    if args.wireless and args.udid is None:
        parser.error("--wireless requires --udid")
    return args


if __name__ == "__main__":
    args = parse_args()
    initial_point = first_gpx_point(args.gpx_file)
    validate_point(*initial_point)
    if args.wireless:
        tunnel = UserspaceRsdTunnel(
            provider_factory=lambda: remote_pairing_provider(
                args.udid,
                args.wireless_host,
            )
        )
    else:
        tunnel = UserspaceRsdTunnel(serial=args.udid)
    asyncio.run(follow_gpx(args.gpx_file, initial_point, tunnel))
