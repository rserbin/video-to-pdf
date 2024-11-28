import os
import cv2
from fpdf import FPDF
import tempfile

class ContentSegment:
    def __init__(self, image, text):
        self.image = image
        self.text = text

class ContentSegmentPdfBuilder:
    def generate_pdf(self, pages, output_filepath):
        try:
            print(f"Starting PDF generation to: {output_filepath}")
            output_dir = os.path.dirname(output_filepath)
            if not os.path.exists(output_dir):
                print(f"Creating output directory: {output_dir}")
                os.makedirs(output_dir)

            with tempfile.TemporaryDirectory() as temp_dir_path:
                pdf = FPDF(orientation='L')  # 'L' for landscape
                pdf.set_margins(5, 5, 5)
                
                # Check font path
                font_path = os.path.join("fonts", "DejaVuSansCondensed.ttf")
                print(f"Checking font at: {font_path}")
                if not os.path.exists(font_path):
                    print("Font not found!")
                    raise FileNotFoundError(f"Font file not found at {font_path}")
                
                pdf.add_font("DejaVu", "", font_path, uni=True)
                
                for i in range(0, len(pages)):
                    print(f"Processing frame {i+1} of {len(pages)}")
                    temp_filepath = os.path.join(temp_dir_path, f"{i}_frame.jpeg")
                    image = pages[i].image
                    
                    height, width = image.shape[:2]
                    
                    left_crop = int(width * 0.05)
                    right_crop = int(width * 0.82)
                    top_crop = int(height * 0.05)
                    bottom_crop = int(height * 0.95)
                    
                    cropped_image = image[top_crop:bottom_crop, left_crop:right_crop]
                    cv2.imwrite(temp_filepath, cropped_image)
                    
                    pdf.add_page()
                    page_width = pdf.w - 10
                    pdf.image(temp_filepath, x=5, y=5, w=page_width)
                
                print(f"Saving PDF to: {output_filepath}")
                pdf.output(output_filepath, "F")
                print(f"PDF saved successfully to: {output_filepath}")
                
                # Verify the file exists
                if os.path.exists(output_filepath):
                    print(f"Verified: PDF file exists at {output_filepath}")
                    print(f"File size: {os.path.getsize(output_filepath)} bytes")
                else:
                    print(f"Error: PDF file not found at {output_filepath}")
                    
        except Exception as e:
            print(f"Error in generate_pdf: {str(e)}")
            raise e
