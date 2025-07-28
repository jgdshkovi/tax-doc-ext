import pandas as pd
import pymupdf
import io
import os
import tempfile
import time
import gc  # Add garbage collection import
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from google.cloud import documentai_v1 as documentai
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Import your existing modules
from schemas_ import map_forms_to_processor_ids, FILE_TEXT, field_mapping, file_paths
from tac_calc import calculate_form_1040_values

app = Flask(__name__)
CORS(app, origins=[
    # "https://app11-bw3qdffff-jagadeesh-ks-projects-b6d83340.vercel.app",
    # "https://app11-bw3qdffff-jagadeesh-ks-projects-b6d83340.vercel.app/",
    "https://app2-rgc3ps9ko-jagadeesh-ks-projects-b6d83340.vercel.app/",
    "https://app2-rgc3ps9ko-jagadeesh-ks-projects-b6d83340.vercel.app",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://34.27.144.213:5000",
    "*"  # Allow all origins for testing - remove in production
])  # Enable CORS for specific origins

# Configuration
PROJECT_ID = "tax-docs-ext"
LOCATION = "us"  # Format is 'us' or 'eu'
MIME_TYPE = "application/pdf"

brackets_2024 = [11_600, 47_150, 100_525, 191_950, 243_725, 609_350, -1]
tax_rates_2024 = [0.10, 0.12, 0.22, 0.24, 0.32, 0.35, 0.37]

def cleanup_memory():
    """Force garbage collection to free up memory"""
    gc.collect()

def online_process(project_id: str, location: str, processor_id: str, file_content: bytes, mime_type: str) -> documentai.Document:
    """
    Processes a document using the Document AI Online Processing API.
    Modified to work with file content instead of file path.
    """
    opts = {"api_endpoint": f"{location}-documentai.googleapis.com"}
    
    # Instantiates a client
    documentai_client = documentai.DocumentProcessorServiceClient(client_options=opts)
    
    # The full resource name of the processor
    resource_name = documentai_client.processor_path(project_id, location, processor_id)
    
    # Load Binary Data into Document AI RawDocument Object
    raw_document = documentai.RawDocument(content=file_content, mime_type=mime_type)
    
    # Configure the process request
    request = documentai.ProcessRequest(name=resource_name, raw_document=raw_document)
    
    # Use the Document AI client to process the document
    result = documentai_client.process_document(request=request)
    
    return result.document

def trim_text(text: str):
    """Remove extra space characters from text"""
    return text.strip().replace("\n", " ")

def get_text_from_pdf(pdf_file_data):
    """Extract text from PDF file data for form identification"""
    try:
        if hasattr(pdf_file_data, 'read'):
            pdf_bytes = pdf_file_data.read()
        else:
            pdf_bytes = pdf_file_data
        
        doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
        res_text = ""
        
        for page in doc:
            text = page.get_text()
            res_text += text + "\n"
        
        doc.close()
        res_text = res_text.replace(".\n", " ").replace("\n", " ")
        return res_text
    except Exception as e:
        return f"Error reading PDF: {str(e)}"

def identify_form(filled_doc_txt):
    """Identify which tax form this document represents using cosine similarity"""
    highest_cosine_similarity = 0
    highest_cosine_similarity_form = None
    
    filled_doc_txt = filled_doc_txt.replace("\n", " ")

    # Compare against each form template
    for form_name, form_txt in FILE_TEXT.items():
        try:
            vectorizer = TfidfVectorizer()
            tfidf_matrix = vectorizer.fit_transform([filled_doc_txt, form_txt])
            cosine_sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            
            if cosine_sim > highest_cosine_similarity:
                highest_cosine_similarity = cosine_sim
                highest_cosine_similarity_form = form_name
        except Exception as e:
            print(f"Error comparing with {form_name}: {e}")
            continue

    # Return the best matching form if similarity threshold met
    if highest_cosine_similarity >= 0.8:
        return highest_cosine_similarity_form, highest_cosine_similarity
    return None, highest_cosine_similarity

def fill_pdf_form(input_pdf_bytes, data_to_fill, field_mapping):
    """
    Fill PDF form fields with provided data and return filled PDF bytes.
    """
    try:
        # Create temporary file for processing
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_input:
            temp_input.write(input_pdf_bytes)
            temp_input_path = temp_input.name
        
        # Open the PDF document
        doc = pymupdf.open(temp_input_path)
        
        filled_fields = []
        not_found_fields = []
        
        # Iterate through the data to fill
        for user_field_name, value in data_to_fill.items():
            pdf_field_name = field_mapping.get(user_field_name)
            
            if not pdf_field_name:
                not_found_fields.append(user_field_name)
                continue
            
            # Find and update the field in the PDF
            field_found = False
            for page_num in range(len(doc)):
                page = doc[page_num]
                widgets = page.widgets()
                
                for widget in widgets:
                    if widget.field_name == pdf_field_name:
                        widget.field_value = str(value)
                        widget.update()
                        filled_fields.append(f"{user_field_name} -> {pdf_field_name}: {value}")
                        field_found = True
                        break
                
                if field_found:
                    break
            
            if not field_found:
                not_found_fields.append(f"{user_field_name} (PDF field: {pdf_field_name})")
        
        # Save to bytes
        pdf_bytes = doc.tobytes()
        doc.close()
        
        # Clean up temporary file
        os.unlink(temp_input_path)
        
        return pdf_bytes, filled_fields, not_found_fields
        
    except Exception as e:
        print(f"Error filling PDF: {e}")
        import traceback
        traceback.print_exc()
        return None, [], [str(e)]

@app.route('/api/process-tax-documents', methods=['POST'])
def process_tax_documents():
    """Advanced processing of tax documents with Document AI and form filling"""
    try:
        # Check if files were uploaded
        if 'pdfs' not in request.files:
            return jsonify({"error": "No PDF files provided"}), 400
        
        files = request.files.getlist('pdfs')
        
        if not files or files[0].filename == '':
            return jsonify({"error": "No PDF files selected"}), 400
        
        results = []
        processed_forms_data = {}
        
        for file in files:
            if file and file.filename.lower().endswith('.pdf'):
                try:
                    file.seek(0)
                    file_content = file.read()
                    
                    # Step 1: Extract text for form identification
                    file.seek(0)
                    extracted_text = get_text_from_pdf(file)
                    
                    if extracted_text.startswith("Error"):
                        results.append({
                            "filename": file.filename,
                            "error": extracted_text,
                            "status": "error"
                        })
                        continue
                    
                    # Step 2: Identify form type
                    identified_form, similarity_score = identify_form(extracted_text)
                    
                    if not identified_form:
                        results.append({
                            "filename": file.filename,
                            "status": "warning",
                            "message": f"Could not identify form type (similarity: {similarity_score:.3f})",
                            "extracted_text_preview": extracted_text[:500] + "..." if len(extracted_text) > 500 else extracted_text
                        })
                        continue
                    
                    print(f"Processing {file.filename} as {identified_form}")
                    
                    # Step 3: Get processor ID for this form type
                    processor_id = map_forms_to_processor_ids.get(identified_form)
                    
                    if not processor_id:
                        results.append({
                            "filename": file.filename,
                            "status": "error",
                            "error": f"No processor configured for form type: {identified_form}"
                        })
                        continue
                    
                    # Step 4: Process with Document AI
                    document = online_process(
                        project_id=PROJECT_ID,
                        location=LOCATION,
                        processor_id=processor_id,
                        file_content=file_content,
                        mime_type=MIME_TYPE,
                    )
                    
                    # Step 5: Extract structured data
                    form_data = {}
                    confidence_data = {}
                    
                    for entity in document.entities:
                        field_name = trim_text(entity.type_)
                        field_value = trim_text(entity.mention_text)
                        form_data[field_name] = field_value
                        confidence_data[field_name] = entity.confidence
                    
                    processed_forms_data[identified_form] = form_data
                    
                    results.append({
                        "filename": file.filename,
                        "status": "success",
                        "identified_form": identified_form,
                        "similarity_score": similarity_score,
                        "extracted_fields": len(form_data),
                        "form_data": form_data,
                        "confidence_data": confidence_data,
                        "average_confidence": sum(confidence_data.values()) / len(confidence_data) if confidence_data else 0
                    })
                    
                    print(f"✅ Successfully processed {file.filename} as {identified_form}")
                    
                except Exception as e:
                    print(f"Error processing {file.filename}: {e}")
                    import traceback
                    traceback.print_exc()
                    results.append({
                        "filename": file.filename,
                        "error": str(e),
                        "status": "error"
                    })
                finally:
                    # Clear file content from memory after processing each file
                    file_content = None
                    extracted_text = None
                    document = None
                    form_data = None
                    confidence_data = None
            else:
                results.append({
                    "filename": file.filename if file else "Unknown",
                    "error": "File is not a PDF",
                    "status": "error"
                })
        
        # Step 6: Perform tax calculations with available forms (handles missing data)
        calculated_data = None
        
        if processed_forms_data:  # If we have any forms at all
            try:
                print(f"🧮 Attempting tax calculations with available forms: {list(processed_forms_data.keys())}")
                calculated_data = calculate_form_1040_values(processed_forms_data)
                print("✅ Tax calculations completed (missing data assumed as zeros)")
            except Exception as e:
                print(f"❌ Error in tax calculations: {e}")
                import traceback
                traceback.print_exc()
                calculated_data = {"error": str(e)}
        
        response_data = {
            "results": results,
            "total_files": len(results),
            "successful_extractions": len([r for r in results if r.get("status") == "success"]),
            "processed_forms": list(processed_forms_data.keys()),
            "calculated_tax_data": calculated_data,
            "forms_data": processed_forms_data
        }
        
        # Clear large variables and force garbage collection
        results = None
        processed_forms_data = None
        calculated_data = None
        cleanup_memory()
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"General error: {e}")
        import traceback
        traceback.print_exc()
        # Clear memory even on error
        cleanup_memory()
        return jsonify({"error": str(e)}), 500

@app.route('/api/generate-filled-pdf', methods=['POST'])
def generate_filled_pdf():
    """Generate a filled PDF from calculated tax data and return the file directly"""
    try:
        data = request.get_json()
        
        if not data or 'calculated_data' not in data:
            return jsonify({"error": "No calculated data provided"}), 400
        
        calculated_data = data['calculated_data']
        
        print("🔄 Generating filled PDF using f1040.pdf template...")
        
        # Use the f1040.pdf from pdfs directory
        template_path = "./f1040.pdf"
        
        if not os.path.exists(template_path):
            return jsonify({"error": f"Template file not found: {template_path}"}), 400
        
        # Read template PDF
        with open(template_path, 'rb') as f:
            template_bytes = f.read()
        
        # Fill the form
        filled_pdf_bytes, filled_fields, not_found_fields = fill_pdf_form(
            template_bytes, calculated_data, field_mapping
        )
        
        if filled_pdf_bytes is None:
            return jsonify({
                "error": "Failed to fill PDF form",
                "not_found_fields": not_found_fields
            }), 500
        
        print(f"✅ Filled PDF generated successfully")
        print(f"📝 Filled {len(filled_fields)} fields")
        if not_found_fields:
            print(f"⚠️ Could not find {len(not_found_fields)} fields: {not_found_fields}")
        
        # Return the file directly from memory using BytesIO
        output_filename = f"completed_f1040_{int(time.time())}.pdf"
        pdf_stream = io.BytesIO(filled_pdf_bytes)
        
        # Clear large variables from memory
        filled_pdf_bytes = None
        template_bytes = None
        calculated_data = None
        cleanup_memory()
        
        return send_file(
            pdf_stream,
            mimetype='application/pdf',
            as_attachment=False,  # Display in browser
            download_name=output_filename
        )
        
    except Exception as e:
        print(f"❌ Error generating filled PDF: {e}")
        import traceback
        traceback.print_exc()
        # Clear memory even on error
        cleanup_memory()
        return jsonify({"error": str(e)}), 500



@app.route('/api/available-forms', methods=['GET'])
def get_available_forms():
    """Get list of available tax forms and their processors"""
    return jsonify({
        "available_forms": list(map_forms_to_processor_ids.keys()),
        "form_processors": map_forms_to_processor_ids,
        "template_files": file_paths
    })

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy", 
        "message": "Advanced Tax Document Processing Service is running",
        "features": [
            "Document AI integration",
            "Form identification",
            "Tax calculations", 
            "PDF form filling"
        ]
    })

@app.route('/', methods=['GET'])
def home():
    """Home endpoint with API documentation"""
    return jsonify({
        "message": "Advanced Tax Document Processing API",
        "endpoints": {
            "/api/health": "Health check",
            "/api/available-forms": "Get available tax forms",
            "/api/process-tax-documents": "POST - Upload and process tax documents with Document AI",
            "/api/generate-filled-pdf": "POST - Generate filled PDF from calculated data (returns PDF file directly)"
        },
        "features": [
            "🤖 Google Cloud Document AI integration",
            "🔍 Intelligent form type identification", 
            "📊 Automated tax calculations",
            "📝 PDF form filling",
            "📄 Multiple tax form support"
        ]
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))  # Use Render's PORT or default to 5000
    app.run(host='0.0.0.0', port=port, debug=False)  # Listen on all interfaces 