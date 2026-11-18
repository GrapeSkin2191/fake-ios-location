import argparse
import math
import random
import xml.etree.ElementTree as ET
from pathlib import Path


METERS_PER_DEGREE_LATITUDE = 111_320.0


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def namespace_of(tag: str) -> str:
    if tag.startswith("{"):
        return tag[1:].split("}", 1)[0]
    return ""


def format_coordinate(value: float) -> str:
    return f"{value:.12f}".rstrip("0").rstrip(".")


def smooth(values: list[float], window: int) -> list[float]:
    half_window = max(1, window // 2)
    result: list[float] = []
    for index in range(len(values)):
        start = max(0, index - half_window)
        end = min(len(values), index + half_window + 1)
        result.append(sum(values[start:end]) / (end - start))
    return result


def coordinates_in_meters(
    trackpoints: list[ET.Element],
) -> list[tuple[float, float]]:
    latitudes = [float(point.attrib["lat"]) for point in trackpoints]
    longitudes = [float(point.attrib["lon"]) for point in trackpoints]
    reference_latitude = sum(latitudes) / len(latitudes)
    reference_longitude = sum(longitudes) / len(longitudes)
    longitude_scale = METERS_PER_DEGREE_LATITUDE * max(
        math.cos(math.radians(reference_latitude)),
        1e-6,
    )

    return [
        (
            (longitude - reference_longitude) * longitude_scale,
            (latitude - reference_latitude) * METERS_PER_DEGREE_LATITUDE,
        )
        for latitude, longitude in zip(latitudes, longitudes)
    ]


def tangent_at(points: list[tuple[float, float]], index: int) -> tuple[float, float]:
    previous = points[max(0, index - 1)]
    following = points[min(len(points) - 1, index + 1)]
    east = following[0] - previous[0]
    north = following[1] - previous[1]
    length = math.hypot(east, north)
    if length == 0:
        return 1.0, 0.0
    return east / length, north / length


def add_realistic_drift(
    trackpoints: list[ET.Element],
    max_offset_meters: float,
    correlation_points: int,
    generator: random.Random,
) -> None:
    if len(trackpoints) < 3:
        return

    points = coordinates_in_meters(trackpoints)
    point_count = len(points)

    lateral_noise = [generator.uniform(-1, 1) for _ in range(point_count)]
    along_noise = [generator.uniform(-1, 1) for _ in range(point_count)]
    lateral = smooth(lateral_noise, correlation_points)
    along = smooth(along_noise, correlation_points)

    offsets: list[tuple[float, float]] = []
    for index in range(point_count):
        tangent_east, tangent_north = tangent_at(points, index)
        normal_east, normal_north = -tangent_north, tangent_east

        lateral_distance = lateral[index] * max_offset_meters * 0.55
        along_distance = along[index] * max_offset_meters * 0.25
        offsets.append(
            (
                normal_east * lateral_distance + tangent_east * along_distance,
                normal_north * lateral_distance + tangent_north * along_distance,
            )
        )

    peak = max(math.hypot(east, north) for east, north in offsets)
    reduction = max_offset_meters / peak if peak > max_offset_meters else 1.0
    original_coordinates = [
        (float(point.attrib["lat"]), float(point.attrib["lon"]))
        for point in trackpoints
    ]

    for point, (latitude, longitude), (east, north) in zip(
        trackpoints,
        original_coordinates,
        offsets,
    ):
        east *= reduction
        north *= reduction
        longitude_scale = METERS_PER_DEGREE_LATITUDE * max(
            math.cos(math.radians(latitude)),
            1e-6,
        )
        point.set(
            "lat",
            format_coordinate(latitude + north / METERS_PER_DEGREE_LATITUDE),
        )
        point.set(
            "lon",
            format_coordinate(longitude + east / longitude_scale),
        )


def realistic_gpx(
    input_path: Path,
    output_path: Path,
    max_offset_meters: float,
    correlation_points: int,
    seed: int | None,
) -> int:
    if not input_path.is_file():
        raise FileNotFoundError(f"input GPX not found: {input_path}")
    if max_offset_meters < 0:
        raise ValueError("maximum offset must not be negative")
    if correlation_points < 1:
        raise ValueError("correlation points must be at least 1")
    if input_path.resolve() == output_path.resolve():
        raise ValueError("input and output paths must be different")

    tree = ET.parse(input_path)
    root = tree.getroot()
    namespace = namespace_of(root.tag)
    if namespace:
        ET.register_namespace("", namespace)

    generator = random.Random(seed)
    point_count = 0
    for segment in root.iter():
        if local_name(segment.tag) != "trkseg":
            continue

        trackpoints = [
            child for child in segment if local_name(child.tag) == "trkpt"
        ]
        if not trackpoints:
            continue

        add_realistic_drift(
            trackpoints,
            max_offset_meters,
            correlation_points,
            generator,
        )
        point_count += len(trackpoints)

    if point_count == 0:
        raise ValueError("GPX contains no <trkpt> elements")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    ET.indent(tree, space="  ")
    tree.write(output_path, encoding="utf-8", xml_declaration=True)
    return point_count


def non_negative_float(value: str) -> float:
    parsed = float(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("maximum offset must not be negative")
    return parsed


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("correlation points must be at least 1")
    return parsed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Add smooth, GPS-like drift to GPX track points."
    )
    parser.add_argument("input", type=Path, help="source GPX file")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="output GPX file; defaults to <input>-realistic.gpx",
    )
    parser.add_argument(
        "--max-offset",
        type=non_negative_float,
        default=1.5,
        help="maximum coordinate displacement in meters (default: 1.5)",
    )
    parser.add_argument(
        "--correlation",
        type=positive_int,
        default=9,
        help="smoothing window in track points (default: 9)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        help="optional random seed for reproducible output",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output = args.output or args.input.with_name(
        f"{args.input.stem}-realistic{args.input.suffix}"
    )
    count = realistic_gpx(
        args.input,
        output,
        args.max_offset,
        args.correlation,
        args.seed,
    )
    print(
        f"Adjusted {count} points with smooth drift up to "
        f"{args.max_offset:g} meters."
    )
    print(f"Saved to: {output}")


if __name__ == "__main__":
    main()
