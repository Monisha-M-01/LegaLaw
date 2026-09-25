import React, { useState, useEffect } from 'react';
import { FileText, Clock, Trash2, ChevronLeft, ChevronRight, Menu } from 'lucide-react';
import { clearSessionId } from '../utils/session';

export default function Sidebar({ documents, onSelectDocument, onClearHistory, isOpen, setIsOpen }) {
  // Mobile layout responsiveness is handled via parent App layout mostly, 
  // but we provide a toggle button here for desktop/mobile toggle.

  return (
    <>
      {/* Mobile toggle button (visible when sidebar is closed) */}
      {!isOpen && (
        <button 
          onClick={() => setIsOpen(true)}
          className="fixed top-4 left-4 z-50 p-2 bg-white border-2 border-ink shadow-hard-sm hover:bg-bg transition-colors md:hidden"
        >
          <Menu className="w-5 h-5 text-ink" />
        </button>
      )}

      {/* Sidebar Container */}
      <div className={`
        fixed md:static inset-y-0 left-0 z-40
        w-72 bg-white border-r-2 border-ink flex flex-col
        transition-transform duration-300 ease-in-out
        ${isOpen ? 'translate-x-0' : '-translate-x-full md:-translate-x-full hidden'}
      `}>
        
        {/* Header */}
        <div className="h-16 flex items-center justify-between px-4 border-b-2 border-ink bg-bg">
          <h2 className="font-display font-bold text-lg">History</h2>
          <button 
            onClick={() => setIsOpen(false)}
            className="p-1 hover:bg-white border-2 border-transparent hover:border-ink rounded-md transition-colors"
          >
            <ChevronLeft className="w-5 h-5 text-ink" />
          </button>
        </div>

        {/* Document List */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {documents.length === 0 ? (
            <div className="text-center mt-10 text-muted font-sans text-sm">
              <Clock className="w-8 h-8 mx-auto mb-3 opacity-50" />
              <p>No past documents found.</p>
            </div>
          ) : (
            documents.map((doc) => (
              <button
                key={doc.document_id}
                onClick={() => onSelectDocument(doc.document_id)}
                className="w-full text-left p-3 bg-white border-2 border-ink hover:bg-bg transition-colors shadow-hard-sm group"
              >
                <div className="flex items-start gap-2">
                  <FileText className="w-4 h-4 text-accent mt-1 flex-shrink-0" />
                  <div className="overflow-hidden">
                    <p className="font-sans font-medium text-sm truncate text-ink group-hover:text-accent transition-colors">
                      {doc.filename}
                    </p>
                    <p className="text-xs text-muted mt-1">
                      {new Date(doc.upload_timestamp).toLocaleDateString()}
                    </p>
                  </div>
                </div>
              </button>
            ))
          )}
        </div>

        {/* Footer / Clear History */}
        <div className="p-4 border-t-2 border-ink bg-gray-50">
          <button 
            onClick={() => {
              if (window.confirm('Are you sure you want to clear your history? This cannot be undone.')) {
                clearSessionId();
                onClearHistory();
              }
            }}
            className="w-full flex items-center justify-center gap-2 py-2 text-sm font-sans font-medium text-muted hover:text-red-600 transition-colors"
          >
            <Trash2 className="w-4 h-4" />
            Clear history
          </button>
        </div>
      </div>
      
      {/* Overlay for mobile when sidebar is open */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-ink/20 z-30 md:hidden"
          onClick={() => setIsOpen(false)}
        />
      )}
    </>
  );
}
