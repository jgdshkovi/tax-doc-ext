import React, { useState } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import { useNavigate } from 'react-router-dom';
import { API_BASE_URL } from './config';
import 'react-pdf/dist/Page/AnnotationLayer.css';
import 'react-pdf/dist/Page/TextLayer.css';

// Configure PDF.js worker
pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.js`;

function AdvancedUpload() {
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [numPages, setNumPages] = useState(null);
  const [pageNumber, setPageNumber] = useState(1);
  const [isProcessing, setIsProcessing] = useState(false);
  const [availableForms, setAvailableForms] = useState([]);
  const navigate = useNavigate();

  // Load available forms on component mount
  React.useEffect(() => {
    fetchAvailableForms();
  }, []);

  const fetchAvailableForms = async () => {
    try {
      const headers = {};
      
      // Add basic auth if using ngrok with password
      // Replace 'username:password' with your ngrok credentials if needed
      // headers['Authorization'] = 'Basic ' + btoa('username:password');
      
      const response = await fetch(`${API_BASE_URL}/api/available-forms`, {
        headers
      });
      if (response.ok) {
        const data = await response.json();
        setAvailableForms(data.available_forms);
      }
    } catch (error) {
      console.error('Error fetching available forms:', error);
    }
  };

  const handleFileUpload = (event) => {
    const files = Array.from(event.target.files);
    const pdfFiles = files.filter(file => file.type === 'application/pdf');
    
    if (pdfFiles.length !== files.length) {
      alert('Please select only PDF files');
      return;
    }

    setUploadedFiles(prevFiles => [...prevFiles, ...pdfFiles]);
  };

  const handleFileSelect = (file) => {
    setSelectedFile(file);
    setPageNumber(1);
  };

  const onDocumentLoadSuccess = ({ numPages }) => {
    setNumPages(numPages);
  };

  const processWithDocumentAI = async () => {
    if (uploadedFiles.length === 0) {
      alert('No files to process');
      return;
    }

    setIsProcessing(true);

    try {
      const formData = new FormData();
      
      // Add all PDF files to the form data
      uploadedFiles.forEach((file) => {
        formData.append('pdfs', file);
      });

      console.log(`Processing ${uploadedFiles.length} files with Document AI...`);

      const response = await fetch(`${API_BASE_URL}/api/process-tax-documents`, {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      
      console.log('Document AI processing complete:', result);

              // Navigate to results page with the processing results
              navigate('/result', { 
        state: { processingResults: result } 
      });

    } catch (error) {
      console.error('Error processing files:', error);
      alert(`❌ Error processing files: ${error.message}`);
    } finally {
      setIsProcessing(false);
    }
  };

  const removeFile = (indexToRemove) => {
    setUploadedFiles(prevFiles => 
      prevFiles.filter((_, index) => index !== indexToRemove)
    );
    if (selectedFile && uploadedFiles[indexToRemove] === selectedFile) {
      setSelectedFile(null);
    }
  };

  return (
    <div style={{ 
      padding: '20px', 
      fontFamily: 'Arial, sans-serif', 
      backgroundColor: '#f0f8ff',
      minHeight: '100vh'
    }}>
      {/* Main Layout Container */}
      <div style={{ 
        display: 'flex', 
        gap: '20px', 
        alignItems: 'flex-start'
      }}>
        {/* Left Side - Header and Upload Sections */}
        <div style={{ 
          flex: '0 0 450px',
          display: 'flex',
          flexDirection: 'column',
          gap: '20px'
        }}>
          {/* Header */}
          <div style={{ 
            padding: '20px',
            backgroundColor: '#fff',
            borderRadius: '8px',
            boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
          }}>
            <div>
              <h1 style={{ margin: '0 0 10px 0', color: '#2c5aa0' }}>
                {/* Tax Document Processor */}
                Automated Personal Tax Return Preparation
              </h1>
              <p style={{ margin: '0 0 15px 0', color: '#666' }}>
                Upload tax documents for AI-powered processing, form identification, and automated calculations
              </p>
            </div>
            <div>
              <div style={{ fontSize: '0.9em', color: '#666', marginBottom: '10px' }}>
                Supported Forms: {availableForms.length}
              </div>
              <div style={{ 
                display: 'flex', 
                flexWrap: 'wrap', 
                gap: '5px'
              }}>
                {availableForms.slice(0, 7).map((form, index) => (
                  <span key={index} style={{
                    padding: '2px 8px',
                    backgroundColor: '#e3f2fd',
                    color: '#1976d2',
                    borderRadius: '12px',
                    fontSize: '0.8em',
                    border: '1px solid #bbdefb'
                  }}>
                    {form.replace('_', ' ').toUpperCase()}
                  </span>
                ))}
              </div>
            </div>
          </div>
          {/* Upload Section */}
          <div style={{ 
            backgroundColor: '#fff',
            border: '1px solid #ddd', 
            borderRadius: '8px',
            padding: '25px',
            boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
          }}>
            <h2 style={{ margin: '0 0 20px 0' }}>📄 Upload Tax Documents</h2>
            
            <input
              type="file"
              multiple
              accept=".pdf"
              onChange={handleFileUpload}
              style={{ 
                marginBottom: '20px',
                padding: '10px',
                border: '2px dashed #ccc',
                borderRadius: '4px',
                width: '100%',
                cursor: 'pointer'
              }}
            />
            
            <button 
              onClick={processWithDocumentAI}
              disabled={uploadedFiles.length === 0 || isProcessing}
              style={{
                padding: '15px 25px',
                backgroundColor: uploadedFiles.length > 0 && !isProcessing ? '#2c5aa0' : '#ccc',
                color: 'white',
                border: 'none',
                borderRadius: '6px',
                cursor: uploadedFiles.length > 0 && !isProcessing ? 'pointer' : 'not-allowed',
                fontSize: '16px',
                fontWeight: 'bold',
                width: '100%',
                marginBottom: '20px'
              }}
            >
              {isProcessing ? (
                <span>
                  🔄 Processing with Document AI... 
                  <br/>
                  <small style={{ fontSize: '12px', opacity: 0.8 }}>
                    This may take a few moments
                  </small>
                </span>
              ) : (
                `Process ${uploadedFiles.length} Document${uploadedFiles.length !== 1 ? 's' : ''}`
              )}
            </button>

            
          </div>
            
          {/* File List */}
          {uploadedFiles.length > 0 && (
            <div style={{ 
              backgroundColor: '#fff',
              border: '1px solid #ddd', 
              borderRadius: '8px',
              padding: '20px',
              boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
            }}>
              <h3 style={{ margin: '0 0 15px 0' }}>
                📁 Uploaded Files ({uploadedFiles.length})
              </h3>
              <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
                {uploadedFiles.map((file, index) => (
                  <li key={index} style={{ 
                    marginBottom: '15px', 
                    padding: '15px', 
                    border: '1px solid #e3f2fd',
                    borderRadius: '6px',
                    backgroundColor: '#fafafa',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '10px'
                  }}>
                    <div>
                      <strong style={{ color: '#2c5aa0' }}>{file.name}</strong>
                      <br />
                      <small style={{ color: '#666' }}>
                        📏 {(file.size / 1024 / 1024).toFixed(2)} MB
                      </small>
                    </div>
                    <div style={{ display: 'flex', gap: '10px' }}>
                      <button 
                        onClick={() => handleFileSelect(file)}
                        style={{
                          padding: '8px 15px',
                          backgroundColor: '#28a745',
                          color: 'white',
                          border: 'none',
                          borderRadius: '4px',
                          cursor: 'pointer',
                          fontSize: '14px'
                        }}
                      >
                        👁️ Preview
                      </button>
                      <button 
                        onClick={() => removeFile(index)}
                        style={{
                          padding: '8px 15px',
                          backgroundColor: '#dc3545',
                          color: 'white',
                          border: 'none',
                          borderRadius: '4px',
                          cursor: 'pointer',
                          fontSize: '14px'
                        }}
                      >
                        🗑️ Remove
                      </button>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>

        {/* Right Side - PDF Viewer */}
        <div style={{ flex: '1' }}>
          {selectedFile ? (
            <div style={{ 
              backgroundColor: '#fff',
              border: '1px solid #ddd', 
              borderRadius: '8px',
              padding: '25px',
              boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
            }}>
              {/* Header with Navigation Controls */}
              <div style={{ 
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: '20px'
              }}>
                <h2 style={{ margin: 0 }}>
                  <span style={{ color: '#666' }}>👁️ Previewing: </span>
                  <span style={{ color: '#2c5aa0' }}>{selectedFile.name}</span>
                </h2>
                
                {/* Navigation Controls */}
                <div style={{ 
                  display: 'flex',
                  alignItems: 'center',
                  gap: '10px',
                  padding: '8px 12px',
                  backgroundColor: '#f8f9fa',
                  borderRadius: '6px',
                  border: '1px solid #dee2e6'
                }}>
                  <button 
                    onClick={() => setPageNumber(prev => Math.max(prev - 1, 1))}
                    disabled={pageNumber <= 1}
                    style={{ 
                      padding: '6px 12px',
                      border: '1px solid #ccc',
                      borderRadius: '4px',
                      backgroundColor: pageNumber <= 1 ? '#f8f9fa' : '#fff',
                      cursor: pageNumber <= 1 ? 'not-allowed' : 'pointer',
                      fontSize: '14px'
                    }}
                  >
                    ⬅️ Prev
                  </button>
                  <span style={{ 
                    fontWeight: 'bold',
                    color: '#495057',
                    fontSize: '14px',
                    minWidth: '80px',
                    textAlign: 'center'
                  }}>
                    Page: {pageNumber} of {numPages}
                  </span>
                  <button 
                    onClick={() => setPageNumber(prev => Math.min(prev + 1, numPages))}
                    disabled={pageNumber >= numPages}
                    style={{ 
                      padding: '6px 12px',
                      border: '1px solid #ccc',
                      borderRadius: '4px',
                      backgroundColor: pageNumber >= numPages ? '#f8f9fa' : '#fff',
                      cursor: pageNumber >= numPages ? 'not-allowed' : 'pointer',
                      fontSize: '14px'
                    }}
                  >
                    Next ➡️
                  </button>
                </div>
              </div>

              {/* PDF Display */}
              <div style={{ 
                border: '2px solid #e3f2fd', 
                display: 'inline-block',
                backgroundColor: 'white',
                padding: '15px',
                borderRadius: '8px',
                boxShadow: '0 4px 8px rgba(0,0,0,0.1)'
              }}>
                <Document
                  file={selectedFile}
                  onLoadSuccess={onDocumentLoadSuccess}
                  onLoadError={(error) => console.error('Error loading PDF:', error)}
                >
                  <Page 
                    pageNumber={pageNumber} 
                    scale={1.4}
                    renderTextLayer={true}
                    renderAnnotationLayer={true}
                  />
                </Document>
              </div>
            </div>
          ) : (
            <div>
            <div style={{ 
              backgroundColor: '#fff',
              border: '2px dashed #ccc', 
              borderRadius: '8px',
              padding: '40px', 
              textAlign: 'center',
              color: '#666'
            }}>
              <h2 style={{ color: '#999' }}>📄 Document Preview</h2>
              <p>Select a file from the left to preview it here</p>
              <div style={{ 
                fontSize: '64px', 
                opacity: 0.3, 
                margin: '20px 0' 
              }}>
                📋
              </div>
            </div>
            {/* Processing Steps Info */}
            <div style={{
              backgroundColor: '#f8f9fa',
              border: '1px solid #dee2e6',
              borderRadius: '6px',
              padding: '15px',
              textAlign: 'center'
            }}>
              <h4 style={{ margin: '0 0 10px 0', color: '#495057' }}>Processing Pipeline</h4>
              <div style={{ margin: 0, paddingLeft: '20px', color: '#6c757d' }}>
                <p>📝 Extract text and identify form types automatically</p>
                <p>🤖 Process with Google Document AI</p>
                <p>📊 Extract structured field data</p>
                <p>🧮 Perform automated tax calculations</p>
                <p>📋 Generate results & downloadable PDF</p>
              </div>
            </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default AdvancedUpload; 