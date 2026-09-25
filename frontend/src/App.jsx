import React, { useState } from 'react';
import { AlertCircle, X } from 'lucide-react';
import UploadScreen from './components/UploadScreen';
import ProcessingState from './components/ProcessingState';
import DocumentViewer from './components/DocumentViewer';
import SummaryView from './components/SummaryView';
import { getLanguage } from './utils/session';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

function App() {
  const [appState, setAppState] = useState('upload'); // 'upload' | 'processing' | 'viewer' | 'summary'
  const [documentName, setDocumentName] = useState('');
  const [documentId, setDocumentId] = useState(null);
  const [documentData, setDocumentData] = useState(null);
  const [summaryData, setSummaryData] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);
  
  // Use a simple session ID
  const [sessionId] = useState(() => {
    let id = localStorage.getItem('session_id');
    if (!id) {
      id = crypto.randomUUID();
      localStorage.setItem('session_id', id);
    }
    return id;
  });

  const handleUploadStart = async (file, language = 'en') => {
    if (!file) return;
    
    setErrorMessage(null);
    setDocumentName(file.name);
    setAppState('processing');

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('session_id', sessionId);
      formData.append('target_language', language);

      // 1. Upload the file
      const uploadRes = await fetch(`${API_BASE_URL}/upload`, {
        method: 'POST',
        body: formData,
      });
      
      if (!uploadRes.ok) {
        let errJson = null;
        try { errJson = await uploadRes.json(); } catch(e) {}
        const msg = errJson?.detail?.message || 'Something went wrong on our end, please try again.';
        throw new Error(msg);
      }
      
      const uploadData = await uploadRes.json();
      const newDocId = uploadData.document_id;
      setDocumentId(newDocId);
      
      // 2. Fetch the full document state (clauses, risk tags)
      const docRes = await fetch(`${API_BASE_URL}/documents/${newDocId}`);
      if (!docRes.ok) {
        throw new Error('Failed to fetch processed document. Please try again.');
      }
      
      const docData = await docRes.json();
      setDocumentData(docData);
      
      // Complete processing and show viewer
      setAppState('viewer');
    } catch (error) {
      console.error('Error during upload/processing:', error);
      setErrorMessage(error.message || 'Something went wrong on our end, please try again.');
      setAppState('upload');
    }
  };

  const handleBackToUpload = () => {
    setErrorMessage(null);
    setAppState('upload');
  };

  const handleGoToSummary = async () => {
    if (!documentId) return;
    setErrorMessage(null);
    
    try {
      const res = await fetch(`${API_BASE_URL}/documents/${documentId}/summary`);
      if (!res.ok) {
        throw new Error('Something went wrong on our end, please try again.');
      }
      const data = await res.json();
      setSummaryData(data);
      setAppState('summary');
    } catch (error) {
      console.error('Error fetching summary:', error);
      setErrorMessage('Something went wrong on our end, please try again.');
    }
  };

  const handleBackToViewer = () => {
    setErrorMessage(null);
    setAppState('viewer');
  };

  return (
    <>
      {errorMessage && (
        <div className="fixed top-4 left-1/2 -translate-x-1/2 z-50 w-full max-w-lg px-4 animate-slide-down">
          <div className="bg-[#FAF7FF] border-2 border-ink p-4 shadow-hard-sm flex items-center justify-between gap-3 rounded-lg">
            <div className="flex items-center gap-2">
              <AlertCircle className="w-5 h-5 text-accent flex-shrink-0" />
              <p className="font-sans text-sm font-medium text-ink">{errorMessage}</p>
            </div>
            <button 
              onClick={() => setErrorMessage(null)}
              className="text-muted hover:text-ink font-bold p-1 rounded hover:bg-gray-100 transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {appState === 'upload' && (
        <UploadScreen onUploadStart={handleUploadStart} />
      )}
      {appState === 'processing' && (
        <ProcessingState onComplete={() => {}} />
      )}
      {appState === 'viewer' && documentData && (
        <DocumentViewer 
          onBack={handleBackToUpload} 
          onSummary={handleGoToSummary}
          documentName={documentName} 
          documentId={documentId}
          documentData={documentData}
        />
      )}
      {appState === 'summary' && summaryData && (
        <SummaryView 
          onBack={handleBackToViewer} 
          documentName={documentName} 
          summaryData={summaryData}
        />
      )}
    </>
  );
}

export default App;
