# Image Orientation Corrector

## Overview

This project is designed to automatically detect and correct the orientation of text in images using a combination of Tesseract and AWS Textract. Many OCR systems, like AWS Textract, may not provide explicit information about the rotation of an image, leading to incorrect text extraction. This tool solves that problem by correcting the image orientation before passing it through AWS Textract for text extraction.

## How it Works

1. **Image Loading and Preparation:** The image is loaded and converted to RGB format for optimal Tesseract performance.
2. **Initial Orientation Detection with Tesseract OSD:** Tesseract detects the initial orientation and rotates the image if necessary.
3. **Text Extraction using AWS Textract:** After correcting the orientation, AWS Textract extracts the text and bounding box coordinates.
4. **Orientation Inference from Bounding Boxes:** The positions of the first and last characters in each bounding box are used to infer the correct orientation.
5. **Final Rotation:** Based on the bounding box analysis, the image is rotated to its correct orientation and saved as the final output.

## Installation

Ensure you have Python 3.9 installed. Install the required dependencies using the following command:

```bash
pip install -r requirements.txt
```

## Requirements

- Python 3.9
- Tesseract OCR (`pytesseract`)
- OpenCV (`cv2`)
- Imutils
- AWS SDK (`boto3`)

## Usage

1. Place your images in the input directory.
2. Update your AWS Textract credentials in a `.env` file.
3. Run the main script to process the images, and get the corrected output in the specified folder.

For a more detailed guide, check the `main.py` file to see how the system handles image orientation and text extraction.
