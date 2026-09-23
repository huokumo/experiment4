#!/usr/bin/env python3

import argparse
import csv
import statistics
import sys


FIELDS = ["angular_x", "angular_y", "angular_z", "linear_x", "linear_y", "linear_z"]


def parse_args():
    parser = argparse.ArgumentParser(description="Calculate stationary IMU bias from a CSV sample file.")
    parser.add_argument("csv_file", help="CSV file created by collect_imu_samples.py")
    parser.add_argument(
        "--expected-z",
        type=float,
        default=9.81,
        help="Expected stationary Z acceleration in m/s^2 (default: 9.81)",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    columns = {field: [] for field in FIELDS}
    try:
        with open(args.csv_file, newline="", encoding="utf-8") as source:
            reader = csv.DictReader(source)
            if reader.fieldnames != FIELDS:
                raise ValueError(f"Expected columns: {', '.join(FIELDS)}")
            for row in reader:
                for field in FIELDS:
                    columns[field].append(float(row[field]))
    except (OSError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    if not columns[FIELDS[0]]:
        print("ERROR: the sample file contains no data", file=sys.stderr)
        return 1

    means = {field: statistics.fmean(values) for field, values in columns.items()}
    linear_z_bias = means["linear_z"] - args.expected_z
    print(f"Samples: {len(columns[FIELDS[0]])}")
    print("Copy these values into imu_bias_corrector in config/sensor_calibration.yaml:")
    print("angular_velocity_bias: [{:.6f}, {:.6f}, {:.6f}]".format(
        means["angular_x"], means["angular_y"], means["angular_z"]
    ))
    print("linear_acceleration_bias: [{:.6f}, {:.6f}, {:.6f}]".format(
        means["linear_x"], means["linear_y"], linear_z_bias
    ))
    return 0


if __name__ == "__main__":
    sys.exit(main())
