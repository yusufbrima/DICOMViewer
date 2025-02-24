import numpy as np
import pydicom
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import json
from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional
import uuid
import os
import glob
import cv2

def normalize_image(image_arr, min_val=None, max_val=None):
    """
    Normalizes the image array to the range 0-255.
    Args:
        image_arr (numpy.ndarray): The image array to normalize.
    Returns:
        numpy.ndarray: The normalized image array.
    """
    image_arr = np.array(image_arr).astype(np.float32)
    if min_val is None:
        min_val = np.min(image_arr)
    if max_val is None:
        max_val = np.max(image_arr)
    image_arr = (image_arr - min_val) / (max_val - min_val)
    return (image_arr.astype(np.float32)*255).astype(np.uint8)

def read_dicom_file(file_path, min_val=None, max_val=None):
    """
    Reads a dicom file and returns the pixel array.
    Args:
        file_path (str): The path to the dicom file.
    Returns:
        numpy.ndarray: The pixel array.
    """
    # check if the file is a dicom file
    if not file_path.endswith('.dcm'):
        raise ValueError('The file is not a dicom file.')
    dcm_file = pydicom.dcmread(file_path)
    pixel_array = dcm_file.pixel_array
    return normalize_image(pixel_array, min_val=min_val, max_val=max_val)

def dicom_to_video(
    dicom_path: str,
    frame_rate: int = 15,
    num_frames: int = None,
    write_video: bool = True,
    save_path: str = "output.mp4"
):
    """
    Convert a sequence of DICOM images into a video and return frames.

    Parameters:
    - dicom_path (str): Path to the folder containing DICOM files.
    - frame_rate (int): Frames per second for the output video.
    - num_frames (int, optional): Number of frames to process. If None, all frames are used.
    - write_video (bool): Whether to save the output video.
    - save_path (str): Path to save the output video.

    Returns:
    - List of frames (NumPy arrays)
    """

    # Get sorted list of DICOM files
    dicom_files = sorted(glob.glob(os.path.join(dicom_path, "*.dcm")))

    if not dicom_files:
        raise ValueError(f"No DICOM files found in {dicom_path}")

    # Limit the number of frames if specified
    if num_frames is not None:
        dicom_files = dicom_files[:num_frames]

    # Read the first frame to get dimensions
    first_frame = pydicom.dcmread(dicom_files[0]).pixel_array
    frame_size = (first_frame.shape[1], first_frame.shape[0])  # (width, height)

    # Prepare the video writer if needed
    video_writer = None
    if write_video:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)  # Ensure save directory exists
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        video_writer = cv2.VideoWriter(save_path, fourcc, frame_rate, frame_size)

    frames = []  # To store frames

    for file in dicom_files:
        pixel_array = read_dicom_file(file)

        # Ensure data type is uint8
        if pixel_array.dtype != np.uint8:
            pixel_array = (pixel_array / pixel_array.max() * 255).astype(np.uint8)

        # Convert grayscale (1-channel) to 3-channel BGR
        pixel_array = cv2.cvtColor(pixel_array, cv2.COLOR_RGB2BGR)
        # pixel_array = cv2.cvtColor(pixel_array, cv2.COLOR_GRAY2BGR)

        frames.append(pixel_array)  # Store frame

        if write_video:
            video_writer.write(pixel_array)

    # Release resources
    if write_video:
        video_writer.release()
        print(f"Video saved at {save_path}")

    return frames  # Return frames regardless of write_video flag

# create a function for dicom to cv2 image 
def dicom_to_cv2_image(dicom_path, min_val=None, max_val=None, save_path=None):
    pixel_array = read_dicom_file(dicom_path, min_val=min_val, max_val=max_val)
    cv2_img = cv2.cvtColor(pixel_array, cv2.COLOR_RGB2BGR)
    if save_path:
        cv2.imwrite(save_path, cv2_img)
    return cv2_img


if __name__ == "__main__":
    pass

