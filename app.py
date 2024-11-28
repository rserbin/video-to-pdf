from flask import Flask, render_template, request, send_file, jsonify
import os
from werkzeug.utils import secure_filename
import time
from src.video_segment_finder import VideoSegmentFinder
from src.content_segment_exporter import ContentSegment, ContentSegmentPdfBuilder
import traceback

app = Flask(__name__)

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
ALLOWED_EXTENSIONS = {'mp4', 'mov', 'avi'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 1024

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_video(video_path, output_path):
    try:
        print(f"Processing video: {video_path}")
        # Get the selected frames
        selected_frames_data = VideoSegmentFinder(threshold=30, min_change=20000).get_best_segment_frames(video_path)
        print(f"Found {len(selected_frames_data)} frames")
        
        frame_nums = sorted(selected_frames_data.keys())
        selected_frames = [selected_frames_data[i]["frame"] for i in frame_nums]
        
        # Create PDF pages
        video_pages = []
        for frame in selected_frames:
            video_pages.append(ContentSegment(frame, None))
        
        # Generate PDF
        printer = ContentSegmentPdfBuilder()
        printer.generate_pdf(video_pages, output_path)
        print(f"PDF generated at: {output_path}")
        return True
    except Exception as e:
        print(f"Error in process_video: {str(e)}")
        raise e

@app.route('/upload', methods=['POST'])
def upload_file():
    video_path = None
    pdf_path = None
    try:
        print("\n=== Starting new upload ===")
        print("Upload request received")
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'})
        
        file = request.files['file']
        print(f"File received: {file.filename}")
        
        if file.filename == '':
            return jsonify({'error': 'No selected file'})
        
        if file and allowed_file(file.filename):
            # Save uploaded video
            filename = secure_filename(file.filename)
            video_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(video_path)
            print(f"File saved to: {video_path}")
            
            # Create output filename
            pdf_filename = f"{os.path.splitext(filename)[0]}_slides_{int(time.time())}.pdf"
            pdf_path = os.path.join(app.config['OUTPUT_FOLDER'], pdf_filename)
            print(f"Will save PDF to: {pdf_path}")
            
            # Process video and create PDF
            process_video(video_path, pdf_path)
            
            print(f"Checking if PDF exists at: {pdf_path}")
            if os.path.exists(pdf_path):
                print("PDF file exists, sending...")
                try:
                    # Also save a copy to Downloads
                    downloads_path = os.path.expanduser(f"~/Downloads/{pdf_filename}")
                    print(f"Copying to Downloads: {downloads_path}")
                    os.system(f"cp '{pdf_path}' '{downloads_path}'")
                    
                    response = send_file(
                        pdf_path,
                        as_attachment=True,
                        download_name=pdf_filename,
                        mimetype='application/pdf'
                    )
                    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
                    response.headers["Pragma"] = "no-cache"
                    response.headers["Expires"] = "0"
                    response.headers["Content-Disposition"] = f"attachment; filename={pdf_filename}"
                    return response
                except Exception as e:
                    print(f"Error sending file: {str(e)}")
                    return jsonify({'error': 'Error sending PDF'})
            else:
                print("PDF file not found after generation!")
                return jsonify({'error': 'PDF generation failed'})
            
    except Exception as e:
        print(f"Error during processing: {str(e)}")
        print("Full traceback:")
        traceback.print_exc()
        return jsonify({'error': str(e)})
    finally:
        # Clean up uploaded video file
        if video_path and os.path.exists(video_path):
            os.remove(video_path)
            print("Cleaned up video file")

@app.route('/')
def home():
    return render_template('upload.html')

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    app.run(debug=True)
