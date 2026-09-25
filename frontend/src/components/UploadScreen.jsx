import React, { useState } from 'react';
import { UploadCloud, FileText, Lock, Scale, Globe, AlertCircle, Sparkles, X } from 'lucide-react';

export default function UploadScreen({ onUploadStart }) {
  const [isDragging, setIsDragging] = useState(false);
  const [showHowItWorks, setShowHowItWorks] = useState(false);

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    // Only set to false if we are leaving the actual window
    if (!e.currentTarget.contains(e.relatedTarget)) {
      setIsDragging(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      onUploadStart(e.dataTransfer.files[0]);
    }
  };

  const handleFileInput = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      onUploadStart(e.target.files[0]);
    }
  };

  const handleSampleClick = async (samplePath, filename) => {
    try {
      const res = await fetch(samplePath);
      if (!res.ok) throw new Error("Could not load sample document");
      const blob = await res.blob();
      const file = new File([blob], filename, {
        type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
      });
      onUploadStart(file);
    } catch (err) {
      console.error("Error loading sample:", err);
    }
  };

  return (
    <div 
      className={`min-h-screen flex flex-col items-center justify-center p-6 relative overflow-hidden pb-48 transition-colors duration-300 ${isDragging ? 'bg-[#F4F0FF]' : 'bg-bg'}`}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      {/* Dynamic Background Elements */}
      <div className="absolute top-[-10%] left-[-10%] w-[40vw] h-[40vw] bg-accent/5 rounded-full blur-3xl pointer-events-none"></div>
      <div className="absolute bottom-[-10%] right-[-10%] w-[30vw] h-[30vw] bg-safe/10 rounded-full blur-3xl pointer-events-none"></div>

      {/* How it works Modal */}
      {showHowItWorks && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-ink/20 backdrop-blur-sm pointer-events-auto">
          <div className="bg-bg rounded-2xl shadow-2xl max-w-md w-full p-6 relative border-2 border-ink animate-slide-down">
            <button 
              onClick={() => setShowHowItWorks(false)}
              className="absolute top-4 right-4 text-muted hover:text-ink transition-colors p-1"
            >
              <X className="w-5 h-5" />
            </button>
            <h2 className="text-2xl font-display font-bold text-ink mb-4 flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-accent" />
              How it works
            </h2>
            <div className="space-y-4 font-sans text-muted text-sm">
              <div className="flex gap-3 items-start">
                <div className="w-6 h-6 rounded-full bg-accent text-white flex items-center justify-center font-bold shrink-0 mt-0.5 text-xs">1</div>
                <div><strong className="text-ink text-base">Upload your document.</strong><br/>We accept PDF and Word files containing legal text like leases or contracts.</div>
              </div>
              <div className="flex gap-3 items-start">
                <div className="w-6 h-6 rounded-full bg-accent text-white flex items-center justify-center font-bold shrink-0 mt-0.5 text-xs">2</div>
                <div><strong className="text-ink text-base">AI Decoding.</strong><br/>Our engine breaks down complex legal jargon into plain language and visually flags potential risks.</div>
              </div>
              <div className="flex gap-3 items-start">
                <div className="w-6 h-6 rounded-full bg-accent text-white flex items-center justify-center font-bold shrink-0 mt-0.5 text-xs">3</div>
                <div><strong className="text-ink text-base">Ask Questions.</strong><br/>Use the chat panel to ask specific questions. The answers are safely grounded in your document.</div>
              </div>
              <div className="flex gap-3 items-start">
                <div className="w-6 h-6 rounded-full bg-accent text-white flex items-center justify-center font-bold shrink-0 mt-0.5 text-xs">4</div>
                <div><strong className="text-ink text-base">Final Verdict.</strong><br/>Generate a summary checklist of negotiation points before you sign.</div>
              </div>
            </div>
            <button 
              onClick={() => setShowHowItWorks(false)}
              className="mt-6 w-full py-3 bg-accent text-white rounded-xl font-sans font-bold hover:brightness-110 active:scale-95 transition-all shadow-md"
            >
              Got it!
            </button>
          </div>
        </div>
      )}

      {/* Top Bar */}
      <div className="absolute top-0 left-0 w-full p-6 flex justify-between items-center z-10 pointer-events-none">
        <div className="font-display font-bold text-xl tracking-tight text-ink flex items-center gap-2 pointer-events-auto">
          <Sparkles className="w-5 h-5 text-accent" />
          AI Legal Assistant
        </div>
        <button 
          onClick={() => setShowHowItWorks(true)}
          className="text-sm font-sans font-medium hover:underline text-muted pointer-events-auto"
        >
          How it works
        </button>
      </div>

      <div className="w-full max-w-4xl mt-12 mb-12 z-10 text-center flex flex-col items-center pointer-events-none">
        
        {/* Progress Indicator */}
        <div className="flex justify-center items-center gap-3 text-xs font-bold font-sans uppercase tracking-wider mb-8 bg-white/50 backdrop-blur-sm px-5 py-2.5 rounded-full border border-ink/5">
          <span className="text-accent">1. Upload</span>
          <span className="text-muted/40">→</span>
          <span className="text-muted/60">2. Decode</span>
          <span className="text-muted/40">→</span>
          <span className="text-muted/60">3. Ask</span>
          <span className="text-muted/40">→</span>
          <span className="text-muted/60">4. Summary</span>
        </div>

        {/* Hero Section */}
        <h1 className="text-5xl md:text-6xl font-display font-bold mb-6 leading-tight tracking-tight max-w-3xl text-ink">
          Legal Document Analysis
        </h1>
        <p className="text-xl md:text-2xl text-muted font-sans max-w-2xl leading-relaxed mb-10">
          Upload a rental agreement, terms of service, or loan contract. This system translates complex legal text into clear, plain language.
        </p>

        {/* Trust Row */}
        <div className="flex flex-wrap justify-center gap-8 bg-white/50 backdrop-blur-sm px-8 py-5 rounded-2xl border border-ink/5 shadow-sm">
          <div className="flex items-center gap-2 text-base text-ink/80 font-sans font-medium">
            <Lock className="w-5 h-5 text-accent" /> Not stored without consent
          </div>
          <div className="flex items-center gap-2 text-base text-ink/80 font-sans font-medium">
            <Scale className="w-5 h-5 text-accent" /> Grounded in Indian law
          </div>
          <div className="flex items-center gap-2 text-base text-ink/80 font-sans font-medium">
            <Globe className="w-5 h-5 text-accent" /> Multiple languages
          </div>
        </div>

      </div>

      {/* Floating Bottom Upload Bar Container */}
      <div className="fixed bottom-14 left-0 w-full px-6 flex flex-col items-center z-20 pointer-events-none">
        
        {/* Example Documents (Above the bar) */}
        <div className="flex flex-wrap justify-center gap-3 mb-5 pointer-events-auto">
          <button 
            onClick={() => handleSampleClick("/sample-lease.docx", "sample-lease.docx")} 
            className="px-4 py-2 bg-safe border border-ink/10 shadow-sm rounded-full font-sans font-medium text-xs hover:brightness-95 transition-all text-ink flex items-center gap-2 active:scale-95"
          >
            <FileText className="w-3 h-3" />
            Evaluate Sample Lease
          </button>
          <button 
            onClick={() => handleSampleClick("/sample-tos.docx", "sample-tos.docx")} 
            className="px-4 py-2 bg-caution border border-ink/10 shadow-sm rounded-full font-sans font-medium text-xs hover:brightness-95 transition-all text-ink flex items-center gap-2 active:scale-95"
          >
            <FileText className="w-3 h-3" />
            Evaluate Sample ToS
          </button>
        </div>

        {/* The Upload Bar */}
        <div 
          className={`w-full max-w-3xl bg-white/90 backdrop-blur-md border-2 rounded-2xl flex items-center justify-between p-3 pl-6 transition-all duration-300 pointer-events-auto shadow-2xl
            ${isDragging ? 'border-accent scale-105 shadow-accent/20' : 'border-ink/10 hover:border-accent/30'}`}
        >
          <div className="flex items-center gap-4">
            <div className={`w-12 h-12 rounded-xl flex items-center justify-center transition-colors duration-300 ${isDragging ? 'bg-accent text-white' : 'bg-[#F0EBFF] text-accent'}`}>
              <UploadCloud className="w-6 h-6" />
            </div>
            <div className="text-left">
              <h2 className="text-base font-bold text-ink font-sans">Upload document for analysis</h2>
              <p className="text-sm text-muted font-sans">Supported formats: PDF, DOCX (Drag & drop anywhere)</p>
            </div>
          </div>
          
          <label className="bg-accent text-white font-sans font-medium px-6 py-3 rounded-xl shadow-md transition-transform active:scale-95 hover:brightness-110 cursor-pointer inline-flex items-center gap-2 text-sm whitespace-nowrap shrink-0 ml-4 border border-ink/10">
            <FileText className="w-4 h-4" />
            <span>Browse files</span>
            <input 
              type="file" 
              className="hidden" 
              accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
              onChange={handleFileInput}
            />
          </label>
        </div>
      </div>
      
      {/* Persistent disclaimer */}
      <div className="fixed bottom-0 left-0 w-full bg-[#F0EBFF]/90 backdrop-blur-md border-t border-ink/5 py-2 px-4 flex justify-center items-center gap-2 text-xs text-ink/70 font-sans z-10 pointer-events-none">
        <AlertCircle className="w-3 h-3 text-accent flex-shrink-0" />
        <span>This analysis provides an overview of likely legal implications under Indian law. It does not constitute formal legal advice from a licensed advocate.</span>
      </div>
    </div>
  );
}
