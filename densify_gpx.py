import argparse
import copy
import math
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path


def split_xml_tag(tag: str) -> tuple[str, str]:
    if tag.startswith("{"):
        namespace, local_name = tag[1:].split("}", 1)
        return namespace, local_name
    return "", tag


def parse_time(value: str | None) -> datetime:
    if not value:
        raise ValueError("track point has no timestamp")

    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    return datetime.fromisoformat(normalized)


def format_time(value: datetime) -> str:
    result = value.isoformat(timespec="milliseconds")
    if result.endswith("+00:00"):
        result = result[:-6] + "Z"
    return result


def parse_float(value: str | None) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def interpolate_value(start: float, end: float, fraction: float) -> float:
    return start + (end - start) * fraction


def create_trackpoint(
    template: ET.Element,
    latitude: float,
    longitude: float,
    timestamp: datetime,
    elevation: float | None,
    namespace: str,
) -> ET.Element:
    point = ET.Element(template.tag)
    point.set("lat", f"{latitude:.15f}".rstrip("0").rstrip("."))
    point.set("lon", f"{longitude:.15f}".rstrip("0").rstrip("."))

    if elevation is not None:
        elevation_element = ET.SubElement(point, f"{{{namespace}}}ele" if namespace else "ele")
        elevation_element.text = f"{elevation:.3f}".rstrip("0").rstrip(".")

    time_element = ET.SubElement(point, f"{{{namespace}}}time" if namespace else "time")
    time_element.text = format_time(timestamp)
    return point


def densify_segment(
    segment: ET.Element,
    interval_seconds: float,
) -> tuple[int, int, int]:
    trackpoints = [child for child in segment if split_xml_tag(child.tag)[1] == "trkpt"]
    if len(trackpoints) < 2:
        return 0, len(trackpoints), 0

    namespace, _ = split_xml_tag(trackpoints[0].tag)
    time_tag = f"{{{namespace}}}time" if namespace else "time"
    elevation_tag = f"{{{namespace}}}ele" if namespace else "ele"

    new_points: list[ET.Element] = [copy.deepcopy(trackpoints[0])]
    inserted_count = 0
    duplicate_count = 0
    previous = trackpoints[0]

    for point_index, end in enumerate(trackpoints[1:], start=1):
        start_latitude = parse_float(previous.get("lat"))
        start_longitude = parse_float(previous.get("lon"))
        end_latitude = parse_float(end.get("lat"))
        end_longitude = parse_float(end.get("lon"))
        start_time = parse_time(previous.findtext(time_tag))
        end_time = parse_time(end.findtext(time_tag))

        if None in (start_latitude, start_longitude, end_latitude, end_longitude):
            raise ValueError("track point has an invalid latitude or longitude")
        if end_time == start_time:
            same_coordinates = (
                previous.get("lat") == end.get("lat")
                and previous.get("lon") == end.get("lon")
            )
            if same_coordinates:
                duplicate_count += 1
                continue
            raise ValueError(
                f"point {point_index} has the same timestamp as the previous point "
                "but different coordinates"
            )
        if end_time < start_time:
            raise ValueError(
                f"timestamps go backwards at point {point_index}: "
                f"{format_time(start_time)} -> {format_time(end_time)}"
            )

        duration = (end_time - start_time).total_seconds()
        steps = max(1, math.ceil(duration / interval_seconds))
        start_elevation = parse_float(previous.findtext(elevation_tag))
        end_elevation = parse_float(end.findtext(elevation_tag))

        for step in range(1, steps):
            fraction = step / steps
            latitude = interpolate_value(start_latitude, end_latitude, fraction)
            longitude = interpolate_value(start_longitude, end_longitude, fraction)
            timestamp = start_time + (end_time - start_time) * fraction
            elevation = None
            if start_elevation is not None and end_elevation is not None:
                elevation = interpolate_value(start_elevation, end_elevation, fraction)

            new_points.append(
                create_trackpoint(
                    template=previous,
                    latitude=latitude,
                    longitude=longitude,
                    timestamp=timestamp,
                    elevation=elevation,
                    namespace=namespace,
                )
            )
            inserted_count += 1

        new_points.append(copy.deepcopy(end))
        previous = end

    segment[:] = new_points
    return inserted_count, len(new_points), duplicate_count


def densify_gpx(
    input_path: Path,
    output_path: Path,
    interval_seconds: float,
) -> tuple[int, int, int]:
    if not input_path.is_file():
        raise FileNotFoundError(f"input GPX not found: {input_path}")
    if interval_seconds <= 0:
        raise ValueError("interval must be greater than zero")
    if input_path.resolve() == output_path.resolve():
        raise ValueError("input and output paths must be different")

    tree = ET.parse(input_path)
    root = tree.getroot()
    namespace, _ = split_xml_tag(root.tag)
    if namespace:
        ET.register_namespace("", namespace)

    segments = [element for element in root.iter() if split_xml_tag(element.tag)[1] == "trkseg"]
    if not segments:
        raise ValueError("no <trkseg> found; convert the GPX route to track points first")

    inserted_total = 0
    point_total = 0
    duplicate_total = 0
    for segment in segments:
        inserted, points, duplicates = densify_segment(segment, interval_seconds)
        inserted_total += inserted
        point_total += points
        duplicate_total += duplicates

    output_path.parent.mkdir(parents=True, exist_ok=True)
    ET.indent(tree, space="  ")
    tree.write(output_path, encoding="utf-8", xml_declaration=True)
    return inserted_total, point_total, duplicate_total


def positive_float(value: str) -> float:
    parsed = float(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("interval must be greater than zero")
    return parsed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Insert intermediate points into GPX tracks while preserving their pace."
    )
    parser.add_argument("input", type=Path, help="source GPX file")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="output GPX file; defaults to <input>-smooth.gpx",
    )
    parser.add_argument(
        "-i",
        "--interval",
        type=positive_float,
        default=1.0,
        help="maximum seconds between points (default: 1.0)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output = args.output or args.input.with_name(f"{args.input.stem}-smooth{args.input.suffix}")
    inserted, total, duplicates = densify_gpx(args.input, output, args.interval)
    print(
        f"Removed {duplicates} duplicate points; inserted {inserted} points; "
        f"output contains {total} points."
    )
    print(f"Saved to: {output}")


if __name__ == "__main__":
    main()
