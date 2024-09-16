""""
Code : Faizan 
Eid : 80271

Req
Python 3.9
pytesseract         0.3.13
imutils             0.5.4

"""

import os
import cv2
import pytesseract
from pytesseract import Output
import imutils
import boto3
from dotenv import load_dotenv
import json

# Load environment variables from .env file
load_dotenv()

# AWS Textract credentials from environment variables
aws_textract_access_key = os.getenv('aws_textract_access_key')
aws_textract_secret_key = os.getenv('aws_textract_secret_key')
aws_textract_region = os.getenv('aws_textract_region')

AWS_S3_CREDS = {
    "aws_access_key_id": aws_textract_access_key,
    "aws_secret_access_key": aws_textract_secret_key,
    "region_name": aws_textract_region
}

# Initialize AWS Textract client
textract = boto3.client('textract', **AWS_S3_CREDS)

# Function to rotate image based on Tesseract OSD and save it
def correct_image_orientation(image_path, output_path):
    image = cv2.imread(image_path)
    if image is None:
        print(f"Error: Could not open image {image_path}")
        return None, None
    
    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    try:
        # Get orientation info from Tesseract
        results = pytesseract.image_to_osd(rgb, output_type=Output.DICT)
        angle = results["rotate"]
        print(f"[INFO] Image: {image_path} needs to be rotated by {angle} degrees.")

        # Rotate the image if needed
        if angle != 0:
            rotated = imutils.rotate_bound(image, angle)
        else:
            rotated = image
        
        # Save the rotated image
        rotated_image_path = os.path.join(output_path, os.path.basename(image_path))
        cv2.imwrite(rotated_image_path, rotated)
        return rotated_image_path, angle
    
    except pytesseract.TesseractError as e:
        print(f"TesseractError for image {image_path}: {e}")
        return None, None

# Function to infer image orientation from word bounding boxes using AWS Textract
def infer_image_orientation(word_bounding_boxes):
    orientations = []
    tolerance = 0.01

    for word in word_bounding_boxes:
        first_char = word['Geometry']['Polygon'][0]
        last_char = word['Geometry']['Polygon'][2]
        first_char_center = (first_char['X'], first_char['Y'])
        last_char_center = (last_char['X'], last_char['Y'])
        
        x_diff = last_char_center[0] - first_char_center[0]
        y_diff = last_char_center[1] - first_char_center[1]

        if abs(y_diff) < abs(x_diff) - tolerance:
            if x_diff > tolerance:
                orientations.append(0)
            elif x_diff < -tolerance:
                orientations.append(180)
        elif abs(x_diff) < abs(y_diff) - tolerance:
            if y_diff > tolerance:
                orientations.append(90)
            elif y_diff < -tolerance:
                orientations.append(270)

    # Majority voting
    orientation_counts = {0: 0, 90: 0, 180: 0, 270: 0}
    for orientation in orientations:
        orientation_counts[orientation] += 1
    
    return max(orientation_counts, key=orientation_counts.get)

# Function to rotate the image anti-clockwise by AWS inferred orientation and save it
def rotate_image_by_aws(image_path, aws_inferred_degree, final_output_path):
    image = cv2.imread(image_path)
    if image is None:
        print(f"Error: Could not open image {image_path}")
        return None

    # Rotate the image anti-clockwise by the AWS inferred angle
    rotated = imutils.rotate_bound(image, -aws_inferred_degree)  # Negative degree for anti-clockwise rotation

    # Save the final rotated image
    rotated_image_path = os.path.join(final_output_path, os.path.basename(image_path))
    cv2.imwrite(rotated_image_path, rotated)
    return rotated_image_path

# Main function to process a single image, correct orientation with Tesseract, infer degrees with AWS, and rotate
def process_image(image_path, tessarct_output_directory, final_output_directory):
    if not os.path.exists(tessarct_output_directory):
        os.makedirs(tessarct_output_directory)

    if not os.path.exists(final_output_directory):
        os.makedirs(final_output_directory)

    # Step 1: Rotate image with Tesseract OSD and save it in tessarct_aws
    corrected_image_path, tessarct_angle = correct_image_orientation(image_path, tessarct_output_directory)
    if not corrected_image_path:
        return None, None  # Skip if Tesseract failed to process the image
    
    # Step 2: Use AWS Textract to detect orientation on the rotated image
    with open(corrected_image_path, 'rb') as img_file:
        img_bytes = img_file.read()
    
    response = textract.detect_document_text(Document={'Bytes': img_bytes})
    word_bounding_boxes = [
        item for item in response['Blocks'] if item['BlockType'] == 'WORD'
    ]

    # Step 3: Infer orientation using AWS Textract
    aws_orientation = infer_image_orientation(word_bounding_boxes)
    print(f"Image {corrected_image_path} inferred to be at {aws_orientation} degrees.")

    # Step 4: Rotate the image anti-clockwise based on AWS inferred orientation and save it
    final_image_path = rotate_image_by_aws(corrected_image_path, aws_orientation, final_output_directory)
    if final_image_path:
        print(f"Final rotated image saved: {final_image_path}")

    # Return the final image path and angles from both Tesseract and AWS
    result_json = {
        os.path.basename(image_path): {
            "tessarct": tessarct_angle,
            "aws": aws_orientation
        }
    }

    return final_image_path, result_json

if __name__ == "__main__":
    image_path = '/home/faizan/2024/adhar_marking_orientaion_class/adhar_marking/test_final_data/1_90.png'  # Input image path
    tessarct_output_directory = '/home/faizan/2024/adhar_marking_orientaion_class/adhar_marking/test_final_data/aws_output'  # Folder to save Tesseract-corrected images
    final_output_directory = '/home/faizan/2024/adhar_marking_orientaion_class/adhar_marking/test_final_data/tessarct_output'  # Folder to save AWS-rotated images
    
    final_image, result = process_image(image_path, tessarct_output_directory, final_output_directory)

    if final_image and result:
        print(f"Final rotated image: {final_image}")
        print("Result JSON:", result)
