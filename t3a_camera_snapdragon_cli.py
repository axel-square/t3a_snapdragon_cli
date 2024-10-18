#!/usr/bin/env python3

import subprocess
import time
import os
from datetime import datetime, timedelta
import click
import tempfile
from PIL import Image, ExifTags


PICTURES_PATH = "/storage/emulated/0/DCIM/Camera"
MAX_PICTURE_AGE_MINUTES = 2
PICTURE_CAPTURE_DELAY_SECONDS = 5

# From https://exiftool.org/TagNames/EXIF.html#Flash
FLASH_METADATA_NO_FLASH = 0x0
FLASH_METADATA_FIRED = 0x1
FLASH_METADATA_FIRED_NO_RETURN = 0x5
FLASH_METADATA_FIRED_RETURN = 0x7
FLASH_METADATA_ON_NOT_FIRED = 0x8
FLASH_METADATA_ON_FIRED = 0x9
FLASH_METADATA_ON_FIRED_NO_RETURN = 0xD
FLASH_METADATA_ON_FIRED_RETURN = 0xF
FLASH_METADATA_OFF_NOT_FIRED = 0x10
FLASH_METADATA_OFF_NOT_FIRED_NO_RETURN = 0x14
FLASH_METADATA_AUTO_DID_NOT_FIRE = 0x18
FLASH_METADATA_AUTO_FIRED = 0x19
FLASH_METADATA_AUTO_FIRED_NO_RETURN = 0x1D
FLASH_METADATA_AUTO_FIRED_RETURN = 0x1F
FLASH_METADATA_NO_FLASH_FUNCTION = 0x20
FLASH_METADATA_OFF_NO_FLASH_FUNCTION = 0x30
FLASH_METADATA_FIRED_RED_EYE = 0x41
FLASH_METADATA_FIRED_RED_EYE_NO_RETURN = 0x45
FLASH_METADATA_FIRED_RED_EYE_RETURN = 0x47
FLASH_METADATA_ON_RED_EYE = 0x49
FLASH_METADATA_ON_RED_EYE_NO_RETURN = 0x4D
FLASH_METADATA_ON_RED_EYE_RETURN = 0x4F
FLASH_METADATA_OFF_RED_EYE = 0x50
FLASH_METADATA_AUTO_DID_NOT_FIRE_RED_EYE = 0x58
FLASH_METADATA_AUTO_FIRED_RED_EYE = 0x59
FLASH_METADATA_AUTO_FIRED_RED_EYE_NO_RETURN = 0x5D
FLASH_METADATA_AUTO_FIRED_RED_EYE_RETURN = 0x5F

VALID_ISO = ["auto", "100", "200", "400", "800", "1600", "3200"]

VALID_RESOLUTIONS = [
    "16000x16000",
    "8192x8192",
    "8192x4320",
    "7680x4320",
    "8000x6000",
    "6928x5196",
    "6560x4928",
    "6112x4584",
    "5184x4882",
    "5656x4242",
    "5344x4008",
    "5184x3880",
    "4608x3456",
    "5312x2988",
    "4160x3120",
    "4208x3120",
    "4000x3000",
    "3840x2160",
    "3264x2448",
    "2976x2976",
    "2592x1944",
    "2592x1936",
    "2560x1920",
    "2688x1512",
    "2048x1536",
    "2048x1520",
    "1920x1080",
    "1600x1200",
    "1920x1088",
    "1440x1080",
    "1280x960",
    "1280x768",
    "1280x720",
    "1280x400",
    "1024x768",
    "800x600",
    "800x480",
    "960x720",
    "720x480",
    "640x480",
    "352x288",
    "320x240",
]

EXPOSURE_MODE_METADATA_AUTO = 0x0
EXPOSURE_MODE_METADATA_MANUAL = 0x1
EXPOSURE_MODE_METADATA_AUTO_BRACKET = 0x2


def run_command(command):
    print(f"Running command: {command}")
    result = subprocess.run(
        command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    return (
        result.stdout.decode("utf-8"),
        result.stderr.decode("utf-8"),
        result.returncode,
    )


def kill_app(package_name):
    run_command(f"adb shell am force-stop {package_name}")


def send_intent(intent):
    run_command(f"adb shell am start -a {intent}")


def check_for_recent_picture(
    filename,
    flash,
    _autofocus,  # Can't seem to be an EXIF tag for autofocus
    iso,
    exposure_time_ns,  # TODO: broken
    resolution,
):
    image_path = f"{PICTURES_PATH}/{filename}.jpg"

    # Find the picture and check its date
    command = f"adb shell ls -l {image_path}"
    stdout, stderr, return_code = run_command(command)
    if return_code != 0:
        print(f"Error accessing directory: {stderr}")
        return False

    current_time = datetime.now()
    time_limit = current_time - timedelta(minutes=MAX_PICTURE_AGE_MINUTES)
    parts = stdout.split()
    timestamp_str = " ".join(parts[-3:-1])
    try:
        file_time = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M")
        if file_time < time_limit:
            print("Picture is too old")
            return False
    except ValueError:
        print(f"Error parsing timestamp: {timestamp_str}")
        return False

    # Download it and get its metadata
    exif_data = get_image_metadata(image_path)
    if not exif_data:
        print("Error getting image metadata")
        return False

    print("EXIF Data:" + str(exif_data))

    # Check correct flash info
    exif_flash = exif_data.get("Flash")
    if flash:
        if exif_flash not in [
            FLASH_METADATA_FIRED,
            FLASH_METADATA_FIRED_NO_RETURN,
            FLASH_METADATA_FIRED_RETURN,
            FLASH_METADATA_ON_FIRED,
            FLASH_METADATA_ON_FIRED_NO_RETURN,
            FLASH_METADATA_ON_FIRED_RETURN,
            FLASH_METADATA_AUTO_FIRED,
            FLASH_METADATA_AUTO_FIRED_NO_RETURN,
            FLASH_METADATA_AUTO_FIRED_RETURN,
            FLASH_METADATA_FIRED_RED_EYE,
            FLASH_METADATA_FIRED_RED_EYE_NO_RETURN,
            FLASH_METADATA_FIRED_RED_EYE_RETURN,
            FLASH_METADATA_ON_RED_EYE,
            FLASH_METADATA_ON_RED_EYE_NO_RETURN,
            FLASH_METADATA_ON_RED_EYE_RETURN,
            FLASH_METADATA_AUTO_FIRED_RED_EYE,
            FLASH_METADATA_AUTO_FIRED_RED_EYE_NO_RETURN,
            FLASH_METADATA_AUTO_FIRED_RED_EYE_RETURN,
        ]:
            print("Flash wrongly not enabled in picture metadata: " + str(exif_flash))
            return False
    else:
        if exif_flash not in [
            FLASH_METADATA_NO_FLASH,
            FLASH_METADATA_OFF_NOT_FIRED,
            FLASH_METADATA_OFF_NOT_FIRED_NO_RETURN,
            FLASH_METADATA_AUTO_DID_NOT_FIRE,
            FLASH_METADATA_AUTO_FIRED,
            FLASH_METADATA_AUTO_FIRED_NO_RETURN,
            FLASH_METADATA_NO_FLASH_FUNCTION,
            FLASH_METADATA_OFF_NO_FLASH_FUNCTION,
            FLASH_METADATA_OFF_RED_EYE,
            FLASH_METADATA_AUTO_DID_NOT_FIRE_RED_EYE,
        ]:
            print("Flash wrongly enabled in picture metadata: " + str(exif_flash))
            return False

    # Check the correct ISO value
    if iso:
        exif_iso = exif_data.get("ISOSpeedRatings")
        if exif_iso is None:
            print("ISO value not found in metadata")
            return False
        # The exif iso value is directly an int
        if exif_iso != int(iso):
            print(f"ISO value is incorrect: {exif_iso} instead of {iso}")
            return False

    # TODO: figure out why exposure time doesn't work
    # if exposure_time_ns:
    #     exif_exposure_time_s = exif_data.get("ExposureTime")
    #     if exif_exposure_time_s is None:
    #         print("Exposure time not found in metadata")
    #         return False
    #     if exposure_time_ns / 1000000000 != exif_exposure_time_s:
    #         print(
    #             f"Exposure time is incorrect: {exif_exposure_time_s} instead of {exposure_time_ns / 1000000000}"
    #         )
    #         return False

    if resolution:
        exif_resolution = exif_data.get("ImageWidth"), exif_data.get("ImageLength")
        if exif_resolution is None:
            print("Resolution not found in metadata")
            return False
        exif_resolution = f"{exif_resolution[0]}x{exif_resolution[1]}"
        if exif_resolution != resolution:
            print(f"Resolution is incorrect: {exif_resolution} instead of {resolution}")
            return False

    return True


def get_image_metadata(image_path):
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp_file:
        tmp_image_path = tmp_file.name

        # Pull the image from the Android device to the temporary file
        _, stderr, return_code = run_command(f"adb pull {image_path} {tmp_image_path}")
        if return_code != 0:
            print(f"Error pulling image: {stderr}")
            return None

        # Open the image file and get its metadata
        with Image.open(tmp_image_path) as img:
            if not hasattr(img, "_getexif"):
                print("No EXIF data found in the image")
                return None

            exif_dict = {}
            exif = img._getexif()
            for tag_id, value in exif.items():
                tag = ExifTags.TAGS.get(tag_id, tag_id)
                exif_dict[tag] = value

            return exif_dict


@click.command()
@click.option(
    "--filename",
    default=None,
    help="Filename to save the picture as (.jpg will be automatically appended).",
)
@click.option("--flash", is_flag=True, help="Enable flash mode.")
@click.option("--autofocus", is_flag=True, help="Enable autofocus mode.")
@click.option("--iso", type=click.Choice(VALID_ISO), help="ISO value.")
@click.option(
    "--exposure_time", type=int, help="Exposure time in nanoseconds. (WIP: broken)"
)
@click.option(
    "--resolution",
    type=click.Choice(VALID_RESOLUTIONS),
    help="Resolution in the format 'widthxheight'.",
)
def cli(filename, flash, autofocus, iso, exposure_time, resolution):
    package_name = "org.codeaurora.snapcam"
    intent = "android.media.action.IMAGE_CAPTURE_NOW"

    if not filename:
        now = datetime.now()
        filename = now.strftime("%Y%m%d_%H%M%S")
    intent += f" --es filename {filename}"

    if flash:
        intent += " --es flash_mode on"

    if autofocus:
        intent += " --es autofocus on"

    if iso:
        intent += f" --es iso {iso}"

    if exposure_time:
        intent += f" --es exposure {exposure_time}"

    if resolution:
        intent += f" --es resolution {resolution}"

    # Kill the app before sending the intent
    kill_app(package_name)

    # Send the intent to start the app and take a picture
    send_intent(intent)

    # Wait for a few seconds to allow the picture to be taken
    time.sleep(PICTURE_CAPTURE_DELAY_SECONDS)

    # Kill the app after sending the intent
    kill_app(package_name)

    # Check for a recent picture
    if check_for_recent_picture(
        filename, flash, autofocus, iso, exposure_time, resolution
    ):
        print("OK")
    else:
        print("FAILED")


if __name__ == "__main__":
    cli()
