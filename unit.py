import os
import pydicom
import numpy as np
import streamlit as st
from io import BytesIO
import cv2
import tempfile
import matplotlib.pyplot as plt
from PIL import Image  # For handling image conversion to different formats
from utils import dicom_to_cv2_image
from utils import normalize_image

# Set up Streamlit page config
st.set_page_config(page_title="DICOM Viewer", layout="wide")

# Default image URL (placeholder)
DEFAULT_IMAGE_URL = "https://static.scientificamerican.com/sciam/cache/file/01C9741F-6F6D-4882-8217D92370325AA7_source.jpg?w=900"

# Sidebar: Upload DICOM files
st.sidebar.title("Upload DICOM File(s)")
uploaded_files = st.sidebar.file_uploader(
    "Choose DICOM file(s)", type=["dcm"], accept_multiple_files=True
)

# Temporary folder to store uploaded files
temp_folder = tempfile.mkdtemp()

# Default placeholder values
selected_image = None
selected_metadata = {}

# Temporary video file path
temp_video_path = tempfile.mktemp(suffix=".mp4")

# Process uploaded files and create a video
if uploaded_files:
    # Sort files based on their names
    sorted_files = sorted(uploaded_files, key=lambda file: file.name)

    # Create a VideoWriter object
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # Codec for mp4 video
    frame_width = 512  # You can adjust this based on the image size
    frame_height = 512
    video_writer = cv2.VideoWriter(temp_video_path, fourcc, 10.0, (frame_width, frame_height))  # 10 FPS

    # Store the sorted files and process them
    for uploaded_file in sorted_files:
        # Store the uploaded file in the temp folder
        file_path = os.path.join(temp_folder, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        dicom_data = pydicom.dcmread(file_path)
        
        # Extract pixel data and normalize
        pixel_array = dicom_data.pixel_array.astype(np.float32)
        pixel_array = normalize_image(pixel_array)

        # Convert the image to a format suitable for OpenCV (uint8)
        # windowed_image = np.clip(pixel_array, 0, 255).astype(np.uint8)

        windowed_image = cv2.cvtColor(pixel_array, cv2.COLOR_RGB2BGR)

        # Resize image to match the video dimensions (if necessary)
        resized_image = cv2.resize(windowed_image, (frame_width, frame_height))

        # Write the image frame to the video
        video_writer.write(resized_image)

    # Release the VideoWriter object after writing all frames
    video_writer.release()

    # Provide a download button for the video
    with open(temp_video_path, "rb") as video_file:
        st.download_button(
            label="Download MP4 Video",
            data=video_file,
            file_name="dicom_video.mp4",
            mime="video/mp4"
        )

    # Create a dropdown to select a file (now based on the files stored in temp_folder)
    sorted_file_names = sorted([file.name for file in sorted_files])
    selected_file_name = st.sidebar.selectbox("Select a DICOM file", sorted_file_names)

    # Find the corresponding file object
    selected_file = next(file for file in sorted_files if file.name == selected_file_name)
    
    # Read DICOM data
    dicom_data = pydicom.dcmread(BytesIO(selected_file.read()))

    # Extract pixel data
    pixel_array = dicom_data.pixel_array.astype(np.float32)

    pixel_array = normalize_image(pixel_array)

    selected_image = pixel_array
    selected_metadata = {
        "Patient Name": dicom_data.get("PatientName", "N/A"),
        "Patient ID": dicom_data.get("PatientID", "N/A"),
        "Modality": dicom_data.get("Modality", "N/A"),
        "Study Date": dicom_data.get("StudyDate", "N/A"),
    }

# Layout: Two columns (Left: Image, Right: Patient Info)
col1, col2 = st.columns([2, 1])  # 2:1 ratio

with col1:
    st.title("DICOM Viewer")
    st.write("### Selected Image")

    if selected_image is not None:
        # Image contrast adjustment sliders
        min_val = st.slider("Min Pixel Value", 0, 255, 0)
        max_val = st.slider("Max Pixel Value", 0, 255, 255)

        # Apply windowing
        windowed_image = np.clip(selected_image, min_val, max_val)
        windowed_image = ((windowed_image - min_val) / (max_val - min_val) * 255).astype(np.uint8)

        # Display Image using Matplotlib
        fig, ax = plt.subplots()
        ax.imshow(windowed_image, cmap="gray")
        ax.axis("off")
        st.pyplot(fig)

    else:
        # Display default image
        st.image(DEFAULT_IMAGE_URL, caption="Default Placeholder Image", use_column_width=True)

with col2:
    st.subheader("Patient Information")
    if selected_metadata:
        for key, value in selected_metadata.items():
            st.write(f"**{key}:** {value}")
    else:
        st.write("No DICOM file uploaded.")

    # Format selection dropdown
    download_format = st.selectbox(
        "Select format to download", ("PNG", "JPEG", "BMP")
    )

    # Button to download image
    if st.button("Download Image"):
        # st.write(selected_file_name)
        if selected_image is not None:
            # Convert numpy array to image using PIL
            pil_image = Image.fromarray(windowed_image)

            # Convert image based on selected format
            if download_format == "PNG":
                img_bytes = BytesIO()
                pil_image.save(img_bytes, format="PNG")
                img_bytes.seek(0)
                st.download_button(
                    label="Download PNG",
                    data=img_bytes,
                    file_name=f"{selected_file_name}.png",
                    mime="image/png"
                )
            elif download_format == "JPEG":
                img_bytes = BytesIO()
                pil_image.save(img_bytes, format="JPEG")
                img_bytes.seek(0)
                st.download_button(
                    label="Download JPEG",
                    data=img_bytes,
                    file_name=f"{selected_file_name}.jpg",
                    mime="image/jpeg"
                )
            elif download_format == "BMP":
                img_bytes = BytesIO()
                pil_image.save(img_bytes, format="BMP")
                img_bytes.seek(0)
                st.download_button(
                    label="Download BMP",
                    data=img_bytes,
                    file_name=f"{selected_file_name}.bmp",
                    mime="image/bmp"
                )
        else:
            st.error("No image available to download")

# Footer
st.markdown("---")
st.markdown(
    """
    **Developed by Yusuf Brima**  
    🚀 *DICOM Viewer - Built with Streamlit*  
    📧 Contact: your.email@example.com  
    """
)
