import React, { useState, useEffect } from 'react';
import { ArrowLeft, CheckSquare, Download, Copy, AlertTriangle, ShieldAlert } from 'lucide-react';

export default function SummaryView({ onBack, documentName, summaryData }) {
  const [checkedItems, setCheckedItems] = useState({});
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    setIsVisible(true);
  }, []);

  const toggleCheck = (id) => {
    setCheckedItems(prev => ({ ...prev, [id]: !prev[id] }));
  };

  return (
    <div className={`h-screen flex flex-col bg-bg overflow-hidden transition-opacity duration-700 ${isVisible ? 'opacity-100' : 'opacity-0'} print:h-auto print:overflow-visible`}>
      
      {/* Header */}
      <header className="flex-none h-16 bg-white border-b-2 border-ink px-4 flex items-center justify-between z-10 relative shadow-sm print:hidden">
        <div className="flex items-center gap-4">
          <button onClick={onBack} className="p-2 hover:bg-bg border-2 border-transparent hover:border-ink rounded-md transition-colors flex items-center gap-2 font-bold font-sans">
            <ArrowLeft className="w-5 h-5" />
            <span className="hidden md:inline">Back to Viewer</span>
          </button>
          <h1 className="font-bold text-lg font-display truncate">Final Summary: {documentName || 'Document'}</h1>
        </div>
        <div className="flex gap-3">
          <button 
            onClick={() => {
              const textToCopy = `Overview:\n${summaryData?.overview || ''}\n\nQuestions to Ask:\n${(summaryData?.checklist || []).map(i => '- ' + i.question).join('\n')}\n\nClauses Worth Negotiating:\n${(summaryData?.negotiate || []).map(i => '- ' + i.clause_summary + ': ' + i.reason).join('\n')}`;
              navigator.clipboard.writeText(textToCopy);
              alert("Summary copied to clipboard!");
            }}
            className="flex items-center gap-2 btn-secondary py-1.5 px-4 text-sm bg-white hover:bg-gray-50 font-bold border-2 border-ink shadow-hard-sm hover:translate-y-px hover:shadow-none transition-all"
          >
            <Copy className="w-4 h-4" /> Copy
          </button>
          <button 
            onClick={() => window.print()}
            className="flex items-center gap-2 bg-accent text-white py-1.5 px-4 text-sm font-bold border-2 border-ink shadow-hard-sm hover:translate-y-px hover:shadow-none transition-all"
          >
            <Download className="w-4 h-4" /> PDF
          </button>
        </div>
      </header>

      {/* Main Content Area */}
      <div className="flex-1 overflow-y-auto p-6 lg:p-10 print:overflow-visible print:h-auto">
        <div className="max-w-4xl mx-auto space-y-12 pb-20">
          
          {/* Overview Block */}
          <section className="animate-slide-up" style={{ animationDelay: '100ms' }}>
            <h2 className="text-sm font-bold uppercase tracking-wider text-ink mb-4 font-sans flex items-center gap-2">
              <span className="w-2 h-2 bg-accent rounded-full inline-block"></span>
              Document Overview
            </h2>
            <div className="bg-[#FAF7FF] border-2 border-ink p-6 md:p-8 shadow-hard-sm">
              <p className="font-sans text-ink text-lg leading-relaxed font-medium">
                {summaryData?.overview}
              </p>
            </div>
          </section>

          {/* Checklist */}
          <section className="animate-slide-up" style={{ animationDelay: '200ms' }}>
            <h2 className="text-sm font-bold uppercase tracking-wider text-ink mb-4 font-sans flex items-center gap-2">
              <span className="w-2 h-2 bg-caution rounded-full inline-block"></span>
              Questions to Ask
            </h2>
            <div className="space-y-4">
              {summaryData?.checklist?.map((item, idx) => {
                const id = `chk-${idx}`;
                return (
                <div 
                  key={id} 
                  className={`bg-caution border-2 border-ink p-5 shadow-hard-sm flex gap-4 transition-colors cursor-pointer ${checkedItems[id] ? 'opacity-60 grayscale' : 'hover:bg-[#fcebbf]'}`}
                  onClick={() => toggleCheck(id)}
                >
                  <div className="flex-none pt-1">
                    <div className={`w-6 h-6 border-2 border-ink flex items-center justify-center ${checkedItems[id] ? 'bg-ink' : 'bg-white'}`}>
                      {checkedItems[id] && <CheckSquare className="w-4 h-4 text-white" />}
                    </div>
                  </div>
                  <div className="flex-1">
                    <p className={`font-sans font-medium text-lg leading-snug ${checkedItems[id] ? 'line-through' : ''}`}>
                      {item.question}
                    </p>
                    <div className="mt-2">
                      <span className="inline-block bg-white border-2 border-ink px-2 py-0.5 text-xs font-bold text-ink">
                        Clause {item.cited_clause}
                      </span>
                    </div>
                  </div>
                </div>
              )})}
            </div>
          </section>

          {/* Negotiate */}
          <section className="animate-slide-up" style={{ animationDelay: '300ms' }}>
            <h2 className="text-sm font-bold uppercase tracking-wider text-ink mb-4 font-sans flex items-center gap-2">
              <span className="w-2 h-2 bg-flag rounded-full inline-block"></span>
              Clauses Worth Negotiating
            </h2>
            <div className="space-y-4">
              {summaryData?.negotiate?.map((item, idx) => (
                <div key={`neg-${idx}`} className="bg-flag border-2 border-ink p-5 shadow-hard-sm">
                  <div className="flex items-start gap-3">
                    <div className="mt-1"><ShieldAlert className="w-5 h-5 text-ink" /></div>
                    <div>
                      <h3 className="font-display font-bold text-xl mb-1">{item.clause_summary}</h3>
                      <p className="font-sans font-medium text-ink/80 leading-relaxed">
                        {item.reason}
                      </p>
                      <div className="mt-3">
                        <span className="inline-block bg-white border-2 border-ink px-2 py-0.5 text-xs font-bold text-ink">
                          Clause {item.cited_clause}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </section>

          {/* Closing */}
          <section className="animate-slide-up print:hidden" style={{ animationDelay: '400ms' }}>
            <div className="bg-ink border-2 border-ink text-white p-6 shadow-hard-sm text-center">
              <div className="flex justify-center mb-3">
                <AlertTriangle className="w-8 h-8 text-caution" />
              </div>
              <p className="font-sans font-bold text-lg">
                {summaryData?.closing}
              </p>
            </div>
          </section>

        </div>
      </div>
    </div>
  );
}
