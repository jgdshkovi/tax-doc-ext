import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { API_BASE_URL } from './config';



function AdvancedResults() {
  const location = useLocation();
  const navigate = useNavigate();
  const processingResults = location.state?.processingResults;
  const [expandedResults, setExpandedResults] = useState({});
  const [filledPdf, setFilledPdf] = useState(null);
  const [isGeneratingPdf, setIsGeneratingPdf] = useState(false);
  const [pdfError, setPdfError] = useState(null);



  // Generate PDF automatically when component loads (if we have calculated data)
  useEffect(() => {
    const generatePdf = async () => {
      // Prevent multiple PDF generation attempts
      if (filledPdf || isGeneratingPdf) {
        return;
      }
      
      if (processingResults?.calculated_tax_data && !processingResults.calculated_tax_data.error) {
        setIsGeneratingPdf(true);
        setPdfError(null);
        
        try {
          const response = await fetch(`${API_BASE_URL}/api/generate-filled-pdf`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              calculated_data: processingResults.calculated_tax_data
            })
          });

          if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`HTTP error! status: ${response.status} - ${errorText}`);
          }

          // Get the PDF as a blob
          const pdfBlob = await response.blob();
          
          // Verify we got a valid PDF
          if (pdfBlob.size === 0 || pdfBlob.type !== 'application/pdf') {
            throw new Error('Received invalid PDF response');
          }
          
          // Create object URL for the PDF
          const pdfUrl = URL.createObjectURL(pdfBlob);
          
          setFilledPdf({
            pdf_url: pdfUrl,
            pdf_blob: pdfBlob,
            filled_fields_count: 'Generated',
            missing_fields_count: 0
          });
          
        } catch (error) {
          console.error('❌ Error generating PDF:', error);
          setPdfError(error.message);
        } finally {
          setIsGeneratingPdf(false);
        }
      }
    };

    // Only generate PDF if we have calculated data and haven't generated one yet
    if (processingResults?.calculated_tax_data && !filledPdf && !isGeneratingPdf) {
      generatePdf();
    }
  }, [processingResults, filledPdf, isGeneratingPdf]);

  // Separate useEffect for cleanup
  useEffect(() => {
    return () => {
      if (filledPdf && filledPdf.pdf_url) {
        URL.revokeObjectURL(filledPdf.pdf_url);
      }
    };
  }, [filledPdf]);

  const toggleExpanded = (index) => {
    setExpandedResults(prev => ({
      ...prev,
      [index]: !prev[index]
    }));
  };

  if (!processingResults) {
    return (
      <div style={{ 
        padding: '20px', 
        fontFamily: 'Arial, sans-serif',
        backgroundColor: '#f0f8ff',
        minHeight: '100vh'
      }}>
        <h1>No Results Found</h1>
        <p>No processing results were found. Please go back and process some documents first.</p>
        <button 
          onClick={() => navigate('/')}
          style={{
            padding: '10px 20px',
            backgroundColor: '#007bff',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer'
          }}
        >
          Back to Upload
        </button>
      </div>
    );
  }

  const formatConfidence = (confidence) => {
    const percentage = (confidence * 100).toFixed(1);
    const color = confidence >= 0.8 ? '#28a745' : confidence >= 0.6 ? '#ffc107' : '#dc3545';
    return (
      <span style={{ color, fontWeight: 'bold' }}>
        {percentage}%
      </span>
    );
  };

  return (
    <div style={{ 
      padding: '20px', 
      fontFamily: 'Arial, sans-serif',
      backgroundColor: '#f0f8ff',
      minHeight: '100vh'
    }}>
      <div style={{ maxWidth: '1400px', margin: '0 auto' }}>
        {/* Header */}
        <div style={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center',
          marginBottom: '30px',
          padding: '20px',
          backgroundColor: '#fff',
          borderRadius: '8px',
          boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
        }}>
          <div>
            <h1 style={{ margin: 0, color: '#2c5aa0' }}>
              🤖 Document AI Processing Results
            </h1>
            <p style={{ margin: '5px 0 0 0', color: '#666' }}>
              Tax document analysis complete
            </p>
          </div>
          <button 
            onClick={() => navigate('/')}
            style={{
              padding: '12px 20px',
              backgroundColor: '#007bff',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              fontWeight: 'bold'
            }}
          >
            🔄 Start Over Again
          </button>
        </div>





        {/* Individual Document Results */}
        <div style={{
          backgroundColor: '#fff',
          border: '1px solid #dee2e6',
          borderRadius: '8px',
          padding: '25px',
          marginBottom: '30px',
          boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
        }}>
          <p style={{ margin: '0 0 4px 0' }}>Extracting and displaying below only the necessary fields for Form 1040 tax calculation.</p>
          <p style={{ margin: '0 0 15px 0' }}>We can always add more fields if needed.</p>
          <h2 style={{ margin: '0 0 20px 0' }}>📋 Individual Document Analysis</h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            {processingResults.results.map((result, index) => (
              <div key={index} style={{
                backgroundColor: result.status === 'success' ? '#d4edda' : 
                              result.status === 'warning' ? '#fff3cd' : '#f8d7da',
                border: `2px solid ${result.status === 'success' ? '#c3e6cb' : 
                                   result.status === 'warning' ? '#ffeaa7' : '#f5c6cb'}`,
                borderRadius: '8px',
                padding: '20px'
              }}>
                <div style={{ 
                  display: 'flex', 
                  justifyContent: 'space-between', 
                  alignItems: 'flex-start',
                  marginBottom: '15px'
                }}>
                  <div style={{ flex: 1 }}>
                    <h3 style={{ margin: 0, fontSize: '1.3em' }}>
                      {result.status === 'success' ? '✅' : 
                       result.status === 'warning' ? '⚠️' : '❌'} {result.filename}
                    </h3>
                    {result.identified_form && (
                      <div style={{ marginTop: '8px' }}>
                        <span style={{
                          padding: '4px 12px',
                          borderRadius: '20px',
                          fontSize: '0.9em',
                          fontWeight: 'bold',
                          backgroundColor: '#e3f2fd',
                          color: '#1976d2',
                          border: '1px solid #bbdefb'
                        }}>
                          📄 {result.identified_form.replace('_', ' ').toUpperCase()}
                        </span>
                        {result.similarity_score && (
                          <span style={{ marginLeft: '10px', color: '#666', fontSize: '0.9em' }}>
                            (Similarity: {(result.similarity_score * 100).toFixed(1)}%)
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                  
                  <div style={{ textAlign: 'right' }}>
                    <span style={{
                      padding: '6px 15px',
                      borderRadius: '20px',
                      fontSize: '0.9em',
                      fontWeight: 'bold',
                      backgroundColor: result.status === 'success' ? '#28a745' : 
                                     result.status === 'warning' ? '#ffc107' : '#dc3545',
                      color: 'white'
                    }}>
                      {result.status.toUpperCase()}
                    </span>
                  </div>
                </div>
                
                {result.status === 'success' && result.form_data && (
                  <div>
                    <div style={{ 
                      display: 'grid', 
                      gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', 
                      gap: '15px',
                      marginBottom: '15px'
                    }}>
                      <div>
                        <strong>📊 Necessary Fields :</strong> {result.extracted_fields}
                      </div>
                      <div>
                        <strong>🎯 Avg Confidence:</strong> {formatConfidence(result.average_confidence)}
                      </div>
                    </div>

                    <button
                      onClick={() => toggleExpanded(index)}
                      style={{
                        padding: '8px 15px',
                        backgroundColor: '#007bff',
                        color: 'white',
                        border: 'none',
                        borderRadius: '4px',
                        cursor: 'pointer',
                        fontSize: '14px',
                        marginBottom: '15px'
                      }}
                    >
                      {expandedResults[index] ? '🔼 Hide Details' : '🔽 Show Extracted Data'}
                    </button>

                    {expandedResults[index] && (
                      <div style={{
                        backgroundColor: '#f8f9fa',
                        border: '1px solid #dee2e6',
                        borderRadius: '6px',
                        padding: '15px',
                        maxHeight: '400px',
                        overflowY: 'auto'
                      }}>
                        <h4 style={{ margin: '0 0 15px 0' }}>📝 Extracted Form Data:</h4>
                        <div style={{
                          display: 'grid',
                          gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
                          gap: '10px'
                        }}>
                          {Object.entries(result.form_data).map(([field, value], fieldIndex) => (
                            <div key={fieldIndex} style={{
                              backgroundColor: '#fff',
                              border: '1px solid #e9ecef',
                              borderRadius: '4px',
                              padding: '10px',
                              fontSize: '0.9em'
                            }}>
                              <div style={{ 
                                fontWeight: 'bold', 
                                color: '#495057',
                                marginBottom: '5px',
                                fontSize: '0.85em'
                              }}>
                                {field}
                              </div>
                              <div style={{ color: '#007bff', fontWeight: 'bold' }}>
                                {value || 'N/A'}
                              </div>
                              {result.confidence_data && result.confidence_data[field] && (
                                <div style={{ fontSize: '0.8em', marginTop: '3px' }}>
                                  Confidence: {formatConfidence(result.confidence_data[field])}
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {result.status === 'warning' && result.message && (
                  <div style={{ color: '#856404' }}>
                    <strong>⚠️ Warning:</strong> {result.message}
                  </div>
                )}

                {result.status === 'error' && result.error && (
                  <div style={{ color: '#721c24' }}>
                    <strong>❌ Error:</strong> {result.error}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* PDF Generation Status */}
        {isGeneratingPdf && (
          <div style={{
            backgroundColor: '#e3f2fd',
            border: '1px solid #bbdefb',
            borderRadius: '8px',
            padding: '15px',
            marginBottom: '20px',
            textAlign: 'center'
          }}>
            🔄 <strong>Generating completed Form 1040...</strong> This may take a few seconds.
          </div>
        )}

        {pdfError && (
          <div style={{
            backgroundColor: '#f8d7da',
            border: '1px solid #f5c6cb',
            borderRadius: '8px',
            padding: '15px',
            marginBottom: '20px'
          }}>
            ❌ <strong>Error generating PDF:</strong> {pdfError}
          </div>
        )}

        {/* Filled Form 1040 PDF Display */}
        {filledPdf && filledPdf.pdf_url && (
          <div style={{
            backgroundColor: '#fff',
            border: '1px solid #dee2e6',
            borderRadius: '8px',
            padding: '25px',
            marginBottom: '30px',
            boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
          }}>
            <div style={{ 
              display: 'flex', 
              justifyContent: 'space-between', 
              alignItems: 'center',
              marginBottom: '20px'
            }}>
              <h2 style={{ margin: 0, color: '#28a745' }}>
                📄 Completed Form 1040 (with the available fields from the uploaded documents)
              </h2>
              <button 
                onClick={() => {
                  // Download the PDF blob directly
                  const url = filledPdf.pdf_url;
                  const a = document.createElement('a');
                  a.style.display = 'none';
                  a.href = url;
                  a.download = `completed_form_1040_${new Date().getTime()}.pdf`;
                  document.body.appendChild(a);
                  a.click();
                  document.body.removeChild(a);
                }}
                style={{
                  padding: '10px 20px',
                  backgroundColor: '#007bff',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  fontWeight: 'bold'
                }}
              >
                💾 Download PDF
              </button>
            </div>
            
            <div style={{
              border: '2px solid #28a745',
              borderRadius: '8px',
              overflow: 'hidden',
              backgroundColor: '#f8f9fa'
            }}>
              <iframe
                src={filledPdf.pdf_url}
                width="100%"
                height="800px"
                style={{
                  border: 'none',
                  display: 'block'
                }}
                title="Completed Form 1040"
              />
            </div>
            
            <div style={{
              marginTop: '10px',
              padding: '10px',
              backgroundColor: '#e3f2fd',
              border: '1px solid #bbdefb',
              borderRadius: '6px',
              fontSize: '14px',
              color: '#1976d2'
            }}>
              💡 <strong>Note:</strong> If the PDF doesn't display above, use the "💾 Download PDF" button to view the completed form.
            </div>
            
            <div style={{
              marginTop: '15px',
              padding: '10px',
              backgroundColor: '#d4edda',
              border: '1px solid #c3e6cb',
              borderRadius: '6px',
              fontSize: '14px',
              color: '#155724'
            }}>
              ✅ <strong>Form automatically completed</strong> with your tax data. 
              <br/>
              Generated fields are filled successfully. Review all fields.
              {filledPdf.missing_fields_count > 0 && (
                <>
                  <br/>
                  ⚠️ <strong>{filledPdf.missing_fields_count}</strong> fields could not be mapped
                </>
              )}
              <br/>
              
            </div>
          </div>
        )}

        {/* Footer Note */}
        <div style={{
          marginTop: '30px',
          padding: '20px',
          backgroundColor: '#f0f8ff',
          border: '1px solid #f0f8ff',
          borderRadius: '8px',
          textAlign: 'center'
        }}>
          <p style={{ margin: 0 }}> 🤖 <strong>Powered by Google Cloud Document AI</strong></p>
          {/* <p>This processing pipeline uses machine learning to extract structured data from tax documents, </p>
          <p>identify form types, and perform automated calculations with high accuracy.</p> */}
        </div>
      </div>
    </div>
  );
}

export default AdvancedResults; 