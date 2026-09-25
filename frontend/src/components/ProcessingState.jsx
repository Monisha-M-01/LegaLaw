import React, { useState, useEffect } from 'react';

const statuses = [
  "Uploading document...",
  "Reading clauses...",
  "Translating legalese to plain English...",
  "Flagging risks and hidden catches...",
  "Preparing your summary..."
];

export default function ProcessingState({ onComplete }) {
  const [statusIndex, setStatusIndex] = useState(0);

  useEffect(() => {
    // Simulate processing steps
    const interval = setInterval(() => {
      setStatusIndex((prev) => {
        if (prev < statuses.length - 1) {
          return prev + 1;
        }
        clearInterval(interval);
        setTimeout(onComplete, 800); // Wait a beat before completing
        return prev;
      });
    }, 1500);
    
    return () => clearInterval(interval);
  }, [onComplete]);

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-6 bg-bg">
      <div className="w-full max-w-[680px] flex flex-col items-center text-center">
        
        {/* Custom calm loading indicator: a pulsing flat block */}
        <div className="relative w-16 h-16 mb-8">
          <div className="absolute inset-0 bg-accent border-2 border-ink shadow-hard-sm animate-pulse"></div>
          {/* Inner block just for style */}
          <div className="absolute inset-2 bg-white/20 border border-ink/20"></div>
        </div>
        
        <h2 className="text-3xl font-bold mb-4 font-display min-h-[40px]">
          {statuses[statusIndex]}
        </h2>
        <p className="text-muted font-sans">
          This usually takes just a moment.
        </p>
      </div>
      
      {/* Persistent disclaimer */}
      <div className="fixed bottom-6 text-sm text-muted text-center w-full px-4">
        This explains what the document likely means under Indian law — it is not a substitute for advice from a licensed advocate.
      </div>
    </div>
  );
}
