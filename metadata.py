#!/usr/bin/env python3

from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import os


def get_image_metadata(image_path):
    try:
        # Open the image file
        img = Image.open(image_path)

        # Get basic info
        width, height = img.size
        format = img.format
        mode = img.mode
        file_size = os.path.getsize(image_path)

        # Initialize a dictionary for EXIF data
        exif_data = {}

        # Extract EXIF data
        if hasattr(img, "_getexif"):
            exif = img._getexif()
            if exif:
                for tag_id, value in exif.items():
                    tag = TAGS.get(tag_id, tag_id)
                    exif_data[tag] = value

        # Print the metadata
        print(f"Width: {width}")
        print(f"Height: {height}")
        print(f"Format: {format}")
        print(f"Mode: {mode}")
        print(f"File Size: {file_size} bytes")

        # Print EXIF data
        print("\nEXIF Data:")
        for key, value in exif_data.items():
            print(f"{key}: {value}")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    image_path = input("Enter the path to the image: ")
    get_image_metadata(image_path)
