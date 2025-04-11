import os
import sys
import streamlit as st
from pathlib import Path
import tempfile
from PIL import Image
import cv2
import numpy as np
import pytesseract

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

# Import OCR components
from digitized_journal.ocr.preprocessor import ImagePreprocessor
from digitized_journal.ocr.ocr_engine import OCREngine
from digitized_journal.config import IMAGES_DIR

# Ensure directories exist
os.makedirs(IMAGES_DIR, exist_ok=True)

st.title("OCR Optimization Tool")
st.write("Upload a handwritten page to test different OCR settings")

# File uploader
uploaded_file = st.file_uploader("Upload image", type=["jpg", "jpeg", "png"])

if uploaded_file:
    # Save file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
        tmp.write(uploaded_file.getvalue())
        img_path = tmp.name
    
    # Display original
    original_img = Image.open(img_path)
    st.image(original_img, caption="Original Image", use_container_width =True)
    
    # OCR settings
    st.subheader("OCR Settings")
    col1, col2 = st.columns(2)
    
    with col1:
        preprocess = st.checkbox("Apply preprocessing", value=True)
        grayscale = st.checkbox("Convert to grayscale", value=True)
        denoise = st.checkbox("Apply denoising", value=True)
        threshold = st.checkbox("Apply thresholding", value=True)
        deskew = st.checkbox("Deskew image", value=True)
        
    with col2:
        psm_mode = st.selectbox(
            "Page segmentation mode",
            options=list(range(0, 14)),
            format_func=lambda x: f"PSM {x}",
            index=6
        )
        oem_mode = st.selectbox(
            "OCR Engine mode",
            options=list(range(0, 4)),
            format_func=lambda x: f"OEM {x}",
            index=3
        )
        language = st.selectbox(
            "Language",
            options=["eng", "eng+osd"],
            index=0
        )
    
    if st.button("Process Image"):
        with st.spinner("Processing..."):
            # Create preprocessor
            preprocessor = ImagePreprocessor()
            
            if preprocess:
                # Process the image with selected options
                processed_img = preprocessor.preprocess(
                    img_path,
                    denoise=denoise,
                    threshold=threshold,
                    deskew=deskew
                )
                
                # Convert to numpy array for display
                processed_np = np.array(processed_img)
                st.image(processed_np, caption="Processed Image", use_container_width =True)
                
                # Convert back to PIL for Tesseract
                img_for_ocr = processed_img
            else:
                img_for_ocr = original_img
            
            # Run OCR with custom config
            config = f"--psm {psm_mode} --oem {oem_mode}"
            text = pytesseract.image_to_string(img_for_ocr, lang=language, config=config)
            
            # Display results
            st.subheader("Extracted Text")
            st.text_area("Text", text, height=300)
            
            # Display OCR debugging info
            st.subheader("OCR Debug Info")
            st.code(f"Tesseract config: {config}")
            
            # Get confidence data
            data = pytesseract.image_to_data(
                img_for_ocr, 
                lang=language, 
                config=config,
                output_type=pytesseract.Output.DICT
            )
            
            # Calculate average confidence
            confidences = [conf for conf in data['conf'] if conf > 0]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            st.metric("Average confidence", f"{avg_confidence:.2f}%")
            
    # Clean up temp file when done
    if os.path.exists(img_path):
        os.unlink(img_path)