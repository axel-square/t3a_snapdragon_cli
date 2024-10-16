#!/usr/bin/env python3

import subprocess
import time
import os
from datetime import datetime, timedelta
import click
from PIL import Image


def run_command(command):
    result = subprocess.run(
        command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    return result.stdout.decode("utf-8"), result.stderr.decode("utf-8")


def kill_app(package_name):
    run_command(f"adb shell am force-stop {package_name}")


def send_intent(intent):
    run_command(f"adb shell am start -a {intent}")


def check_for_recent_picture(directory, time_limit_minutes=1):
    current_time = datetime.now()
    time_limit = current_time - timedelta(minutes=time_limit_minutes)

    stdout, stderr = run_command(f"adb shell ls -l {directory}")
    if stderr:
        print(f"Error accessing directory: {stderr}")
        return False

    for line in stdout.splitlines():
        parts = line.split()
        if len(parts) < 8:
            continue
        timestamp_str = " ".join(parts[-3:-1])
        try:
            file_time = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M")
            if file_time > time_limit:
                return True
        except ValueError:
            print(f"Error parsing timestamp: {timestamp_str}")
            continue

    return False


@click.command()
@click.option("--filename", default=None, help="Filename to save the picture as.")
def cli(filename):
    package_name = "org.codeaurora.snapcam"
    intent = "android.media.action.IMAGE_CAPTURE_NOW"
    directory = "/storage/emulated/0/DCIM/Camera"

    if filename:
        intent += f" --es filename {filename}"

    # Kill the app before sending the intent
    kill_app(package_name)

    # Send the intent to start the app and take a picture
    send_intent(intent)

    # Wait for a few seconds to allow the picture to be taken
    time.sleep(5)

    # Kill the app after sending the intent
    kill_app(package_name)

    # Check for a recent picture
    if check_for_recent_picture(directory):
        print("OK")
    else:
        print("FAILED")


if __name__ == "__main__":
    cli()
