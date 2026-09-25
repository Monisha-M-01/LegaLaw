import React, { useState, useEffect } from 'react';
import { ArrowLeft, Info, ShieldAlert, ShieldCheck, AlertTriangle, MessageSquare, Scale, Loader2, X, AlertCircle } from 'lucide-react';
import ChatPanel from './ChatPanel';
import LanguageSelector from './LanguageSelector';

export default function DocumentViewer({ onBack, onSummary, documentName, documentId, documentData }) {
  const [activeTab, setActiveTab] = useState('simplified'); // for mobile
  const [selectedClause, setSelectedClause] = useState(null);
  const [isVisible, setIsVisible] = useState(false);
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [chatPrefill, setChatPrefill] = useState("");
  const [showVerdict, setShowVerdict] = useState(false);
  const [verdictData, setVerdictData] = useState(null);
  const [verdictLoading, setVerdictLoading] = useState(false);
  const [localData, setLocalData] = useState(documentData);
  const [isTranslating, setIsTranslating] = useState(false);
  const [selectedLang, setSelectedLang] = useState(documentData?.target_language || 'en');
  const [errorMsg, setErrorMsg] = useState(null);

  useEffect(() => {
    setLocalData(documentData);
    if (documentData?.target_language) {
      setSelectedLang(documentData.target_language);
    }
  }, [documentData]);

  const showError = (msg) => {
    setErrorMsg(msg);
    // Auto-dismiss after 5s
    setTimeout(() => setErrorMsg(null), 5000);
  };

  const handleLanguageChange = async (langCode) => {
    const prevLang = selectedLang;
    setIsTranslating(true);
    setSelectedLang(langCode);
    try {
      const response = await fetch(`http://127.0.0.1:8000/api/documents/${documentId}/translate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ target_language: langCode })
      });
      if (!response.ok) {
        let detail = 'Translation failed. Please try again.';
        try {
          const errJson = await response.json();
          if (errJson?.detail?.message) detail = errJson.detail.message;
        } catch (_) {}
        throw new Error(detail);
      }
      const data = await response.json();
      setLocalData(prev => ({
        ...prev,
        clauses: data.clauses
      }));
    } catch (e) {
      console.error(e);
      setSelectedLang(prevLang); // Revert to previous language on failure
      showError(e.message || 'Something went wrong on our end, please try again.');
    } finally {
      setIsTranslating(false);
    }
  };

  const handleShowVerdict = async () => {
    setShowVerdict(true);
    if (verdictData) return;
    setVerdictLoading(true);
    try {
      const response = await fetch(`http://127.0.0.1:8000/api/documents/${documentId}/verdict`);
      if (!response.ok) {
        let detail = 'Failed to generate verdict. Please try again.';
        try {
          const errJson = await response.json();
          if (errJson?.detail?.message) detail = errJson.detail.message;
        } catch (_) {}
        throw new Error(detail);
      }
      const data = await response.json();
      setVerdictData(data.verdict);
    } catch (e) {
      console.error(e);
      setVerdictData(e.message || 'Something went wrong on our end, please try again.');
    } finally {
      setVerdictLoading(false);
    }
  };

  const getSanitizedExplanation = (rawExplanation) => {
    if (!rawExplanation) return "No explanation provided.";
    if (
      typeof rawExplanation !== 'string' ||
      rawExplanation.includes("404") ||
      rawExplanation.includes("503") ||
      rawExplanation.includes("models/") ||
      rawExplanation.includes("Traceback") ||
      rawExplanation.includes("ClientError") ||
      rawExplanation.includes("APIError") ||
      rawExplanation.includes("Error processing document") ||
      rawExplanation.includes("error_code")
    ) {
      return "Something went wrong on our end, please try again.";
    }
    return rawExplanation;
  };

  // Clean reveal animation trigger
  useEffect(() => {
    setIsVisible(true);
  }, []);

  const getRiskColor = (risk) => {
    switch (risk) {
      case 'safe': return 'bg-safe';
      case 'caution': return 'bg-caution';
      case 'flag': return 'bg-flag';
      default: return 'bg-white';
    }
  };

  const getRiskIcon = (risk) => {
    switch (risk) {
      case 'safe': return <ShieldCheck className="w-5 h-5 text-ink" />;
      case 'caution': return <AlertTriangle className="w-5 h-5 text-ink" />;
      case 'flag': return <ShieldAlert className="w-5 h-5 text-ink" />;
      default: return null;
    }
  };

  return (
    <div className={`h-screen flex flex-col overflow-hidden bg-bg transition-opacity duration-700 ${isVisible ? 'opacity-100' : 'opacity-0'}`}>
      
      {/* Top Navigation Bar */}
      <header className="flex-none h-16 bg-white border-b-2 border-ink px-4 flex items-center justify-between z-10 relative shadow-sm">
        <div className="flex items-center gap-4">
          <button onClick={onBack} className="p-2 hover:bg-bg border-2 border-transparent hover:border-ink rounded-md transition-colors">
            <ArrowLeft className="w-5 h-5" />
          </button>
          <h1 className="font-bold text-lg font-display truncate">{documentName || 'Document'}</h1>
        </div>
        
        {/* Mobile Tabs */}
        <div className="md:hidden flex border-2 border-ink rounded-md overflow-hidden font-sans font-medium text-sm">
          <button 
            className={`px-4 py-1.5 ${activeTab === 'original' ? 'bg-ink text-white' : 'bg-white text-ink'}`}
            onClick={() => setActiveTab('original')}
          >
            Original
          </button>
          <button 
            className={`px-4 py-1.5 border-l-2 border-ink ${activeTab === 'simplified' ? 'bg-ink text-white' : 'bg-white text-ink'}`}
            onClick={() => setActiveTab('simplified')}
          >
            Simplified
          </button>
        </div>
        
        {/* Actions (Desktop) */}
        <div className="hidden md:flex gap-3 items-center">
          <button 
            onClick={handleShowVerdict}
            className="flex items-center gap-2 bg-flag text-white border-2 border-ink px-4 py-1.5 font-bold shadow-hard-sm hover:translate-y-px hover:shadow-none transition-all"
          >
            <Scale className="w-4 h-4" /> Final Verdict
          </button>
          <button 
            onClick={() => setIsChatOpen(!isChatOpen)}
            className="flex items-center gap-2 bg-white border-2 border-ink px-4 py-1.5 font-bold shadow-hard-sm hover:translate-y-px hover:shadow-none transition-all"
          >
            <MessageSquare className="w-4 h-4" /> Ask AI
          </button>
          <button onClick={onSummary} className="btn-secondary py-1.5 px-4 text-sm font-bold">View Final Summary</button>
        </div>
        
        {/* Mobile Ask AI and Verdict */}
        <div className="md:hidden flex gap-2">
          <button 
            onClick={handleShowVerdict}
            className="p-2 border-2 border-transparent hover:border-ink rounded-md transition-colors"
          >
            <Scale className="w-5 h-5 text-flag" />
          </button>
          <button 
            onClick={() => setIsChatOpen(!isChatOpen)}
            className="p-2 border-2 border-transparent hover:border-ink rounded-md transition-colors"
          >
            <MessageSquare className="w-5 h-5 text-ink" />
          </button>
        </div>
      </header>

      {/* Split Pane Content */}
      <div className="flex-1 flex overflow-hidden relative">
        
        {/* Left Pane: Original Text */}
        <div className={`${activeTab === 'original' ? 'block' : 'hidden'} md:block w-full flex-1 bg-white border-r-2 border-ink overflow-y-auto p-6 lg:p-10`}>
          <div className="flex justify-between items-end mb-8 border-b-2 border-gray-100 pb-2 h-[40px]">
            <h2 className="text-sm font-bold uppercase tracking-wider text-muted font-sans">Original Legal Text</h2>
          </div>
          <div className="space-y-6">
            {localData?.clauses?.map((clause) => (
              <p 
                key={clause.id} 
                className={`text-base leading-relaxed p-3 rounded transition-colors cursor-pointer ${selectedClause === clause.id ? 'bg-gray-100 ring-2 ring-ink ring-offset-2' : 'text-[#8A8594] hover:bg-gray-50'}`}
                onClick={() => setSelectedClause(clause.id)}
              >
                {clause.original}
              </p>
            ))}
          </div>
        </div>

        {/* Right Pane: Simplified Text */}
        <div className={`${activeTab === 'simplified' ? 'flex' : 'hidden'} md:flex flex-col w-full flex-1 h-full bg-bg overflow-hidden relative`}>
          
          <div className="flex-1 overflow-y-auto p-6 lg:p-10 relative z-0">
            <div className="flex justify-between items-end mb-8 border-b-2 border-ink pb-2 h-[40px]">
              <h2 className="text-sm font-bold uppercase tracking-wider text-ink font-sans">Change Language</h2>
              <LanguageSelector currentLang={selectedLang} onSelect={handleLanguageChange} disabled={isTranslating} />
            </div>

            {isTranslating ? (
              <div className="flex flex-col items-center justify-center h-64 opacity-50">
                <Loader2 className="w-8 h-8 animate-spin text-ink mb-4" />
                <p className="font-sans font-bold text-ink">Translating clauses...</p>
              </div>
            ) : (
              <div className="space-y-6">
                {localData?.clauses?.map((clause) => (
                <div 
                  key={clause.id}
                  onClick={() => setSelectedClause(selectedClause === clause.id ? null : clause.id)}
                  className={`
                    p-5 border-2 border-ink shadow-hard-sm cursor-pointer transition-transform relative
                    ${getRiskColor(clause.risk)} 
                    ${selectedClause === clause.id ? 'translate-x-1 translate-y-1 shadow-none' : 'hover:-translate-y-1 hover:shadow-hard'}
                  `}
                >
                  <div className="flex items-start gap-3">
                    <div className="mt-0.5">{getRiskIcon(clause.risk)}</div>
                    <div className="flex-1">
                      <p className="font-sans font-medium text-lg leading-snug">{clause.simplified}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
            )}
            
            <div className="mt-16 mb-20 text-center">
              <p className="text-muted italic text-sm">End of document summary.</p>
            </div>
          </div>

          {/* Explanation Popover (Bottom sheet style) */}
          {selectedClause && (
            <div className="absolute bottom-0 left-0 right-0 bg-white border-t-2 border-ink shadow-[0_-4px_0_0_rgba(30,27,41,1)] p-6 z-20 animate-slide-up">
              <div className="flex justify-between items-start mb-2">
                <h3 className="font-display font-bold text-lg flex items-center gap-2">
                  <Info className="w-5 h-5 text-accent" />
                  Why is this flagged?
                </h3>
                <button onClick={() => setSelectedClause(null)} className="text-muted hover:text-ink font-bold px-2 py-1 bg-gray-100 border-2 border-transparent hover:border-ink rounded">
                  Close
                </button>
              </div>
              <p className="font-sans text-ink leading-relaxed mb-4">
                {getSanitizedExplanation(localData?.clauses?.find(c => c.id === selectedClause)?.explanation)}
              </p>
              <button  
                onClick={() => {
                  setChatPrefill(`Can you explain Clause ${selectedClause} in more detail?`);
                  setIsChatOpen(true);
                }}
                className="flex items-center gap-2 bg-accent text-white font-bold border-2 border-ink px-4 py-2 shadow-hard-sm hover:translate-y-px hover:shadow-none transition-all text-sm"
              >
                <MessageSquare className="w-4 h-4" /> Ask about this clause
              </button>
            </div>
          )}

        </div>

        {/* Chat Panel */}
        <div className={`${isChatOpen ? 'block' : 'hidden'} absolute md:relative inset-0 md:inset-auto z-30 md:z-10 w-full md:w-80 lg:w-96 flex-none bg-white`}>
          <ChatPanel 
            isOpen={isChatOpen} 
            onClose={() => setIsChatOpen(false)} 
            initialInput={chatPrefill}
            documentId={documentId}
            initialConversation={localData?.conversation}
            targetLanguage={selectedLang}
            onClauseClick={(id) => {
              setActiveTab('original');
              setSelectedClause(id);
            }}
          />
        </div>

      </div>
      
      {/* Persistent Disclaimer */}
      <div className="h-8 bg-ink text-white flex items-center justify-center text-xs font-sans">
        This explains what the document likely means under Indian law — it is not a substitute for advice from a licensed advocate.
      </div>

      {/* Final Verdict Modal */}
      {showVerdict && (
        <div className="absolute inset-0 z-50 flex items-center justify-center bg-ink/50 backdrop-blur-sm p-4">
          <div className="bg-white border-4 border-ink p-6 md:p-8 max-w-lg w-full shadow-hard relative">
            <h2 className="font-display font-bold text-2xl flex items-center gap-2 mb-4">
              <Scale className="w-6 h-6 text-flag" /> Final Verdict
            </h2>
            <div className="bg-gray-50 border-2 border-ink p-4 min-h-[150px] max-h-[60vh] overflow-y-auto">
              {verdictLoading ? (
                <div className="flex items-center justify-center h-full">
                  <p className="font-sans font-bold text-ink animate-pulse">The AI is reviewing the entire agreement...</p>
                </div>
              ) : (
                <p className="font-sans leading-relaxed text-ink whitespace-pre-wrap">{verdictData}</p>
              )}
            </div>
            <div className="mt-6 flex items-center justify-between gap-4">
              <p className="text-xs text-muted font-sans italic flex items-center gap-1">
                <AlertTriangle className="w-3 h-3 flex-none" /> Note: This is an AI-generated verdict.
              </p>
              <button 
                onClick={() => setShowVerdict(false)} 
                className="bg-ink text-white font-bold py-2 px-6 border-2 border-ink shadow-hard-sm hover:translate-y-px hover:shadow-none transition-all flex-none"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
