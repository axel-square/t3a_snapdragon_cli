#!/usr/bin/env python3

import subprocess
import time
import os
from datetime import datetime, timedelta
import click
import PIL


PICTURES_PATH = "/storage/emulated/0/DCIM/Camera"
MAX_PICTURE_AGE_MINUTES = 1
PICTURE_CAPTURE_DELAY_SECONDS = 5


def run_command(command):
    print(f"Running command: {command}")
    result = subprocess.run(
        command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    return result.stdout.decode("utf-8"), result.stderr.decode("utf-8")


def kill_app(package_name):
    run_command(f"adb shell am force-stop {package_name}")


def send_intent(intent):
    run_command(f"adb shell am start -a {intent}")


def check_for_recent_picture(filename=None):
    def ls_line_is_recent_enough(line):
        current_time = datetime.now()
        time_limit = current_time - timedelta(minutes=MAX_PICTURE_AGE_MINUTES)
        parts = line.split()
        if len(parts) < 8:
            return False
        timestamp_str = " ".join(parts[-3:-1])
        try:
            file_time = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M")
            if file_time > time_limit:
                return True
        except ValueError:
            print(f"Error parsing timestamp: {timestamp_str}")
        return False

    command = f"adb shell ls -l {PICTURES_PATH}"
    if filename:
        command += f"/{filename}.jpg"
    stdout, stderr = run_command(command)
    if stderr:
        print(f"Error accessing directory: {stderr}")
        return False

    if filename:
        return ls_line_is_recent_enough(stdout)
    else:
        for line in stdout.splitlines():
            parts = line.split()
            if len(parts) < 8:
                continue
            if ls_line_is_recent_enough(line):
                return True

    return False


def get_image_metadata(image_path):
    # Open the image file
    img = PIL.Image.open(image_path)

    # Initialize a dictionary for EXIF data
    exif_data = {}

    # Extract EXIF data
    if hasattr(img, "_getexif"):
        exif = img._getexif()
        if exif:
            for tag_id, value in exif.items():
                tag = PIL.TAGS.get(tag_id, tag_id)
                exif_data[tag] = value

    return img, exif_data


@click.command()
@click.option("--filename", default=None, help="Filename to save the picture as.")
def cli(filename):
    package_name = "org.codeaurora.snapcam"
    intent = "android.media.action.IMAGE_CAPTURE_NOW"

    if filename:
        intent += f" --es filename {filename}"

    # Kill the app before sending the intent
    kill_app(package_name)

    # Send the intent to start the app and take a picture
    send_intent(intent)

    # Wait for a few seconds to allow the picture to be taken
    time.sleep(PICTURE_CAPTURE_DELAY_SECONDS)

    # Kill the app after sending the intent
    kill_app(package_name)

    # Check for a recent picture
    if check_for_recent_picture(filename):
        print("OK")
    else:
        print("FAILED")


if __name__ == "__main__":
    cli()
