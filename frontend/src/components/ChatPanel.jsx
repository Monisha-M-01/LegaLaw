import React, { useState, useEffect, useRef } from 'react';
import { Send, X, HelpCircle, FileText, BookOpen } from 'lucide-react';
import { API_BASE_URL } from '../config';

export default function ChatPanel({ isOpen, onClose, onClauseClick, initialInput = "", documentId, initialConversation = [], targetLanguage = 'en' }) {
  const [inputValue, setInputValue] = useState("");
  const [conversation, setConversation] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    if (initialConversation && initialConversation.length > 0) {
      // Map backend conversation to frontend format
      const mapped = initialConversation.map((msg, idx) => {
        let type = msg.role === 'user' ? null : (msg.is_clarifying ? 'clarification' : 'answer');
        
        let cited_clauses = [];
        if (msg.cited_clause && msg.cited_clause !== "[]") {
          try {
            cited_clauses = JSON.parse(msg.cited_clause.replace(/'/g, '"'));
          } catch(e) {}
        }
        
        return {
          id: idx,
          role: msg.role,
          type: type,
          content: msg.content,
          cited_clauses: cited_clauses,
          cited_statutes: [] // We don't save statutes in DB currently
        };
      });
      setConversation(mapped);
    }
  }, [initialConversation]);

  useEffect(() => {
    if (initialInput) {
      setInputValue(initialInput);
    }
  }, [initialInput]);

  useEffect(() => {
    // Scroll to bottom when opened
    if (isOpen) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="flex flex-col w-full h-full bg-white border-l-2 border-ink z-20 absolute md:relative right-0 top-0 bottom-0 shadow-[-4px_0_0_0_rgba(30,27,41,1)] md:shadow-none animate-slide-left">
      
      {/* Header */}
      <div className="flex-none h-16 border-b-2 border-ink px-4 flex items-center justify-between bg-[#FAF7FF]">
        <h2 className="font-display font-bold text-lg text-ink">Ask AI Assistant</h2>
        <button 
          onClick={onClose} 
          className="p-1 hover:bg-gray-100 border-2 border-transparent hover:border-ink rounded transition-colors"
        >
          <X className="w-5 h-5 text-ink" />
        </button>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-6 bg-white font-sans">
        
        {/* Intro Message */}
        <div className="text-center text-sm font-bold text-muted uppercase tracking-wider my-4 border-b-2 border-gray-100 pb-2">
          Conversation Started
        </div>

        {conversation.map((msg) => {
          if (msg.role === 'user') {
            return (
              <div key={msg.id} className="flex justify-end pl-12">
                <div className="bg-white border-2 border-ink p-3 shadow-hard-sm">
                  <p className="text-ink font-medium leading-snug">{msg.content}</p>
                </div>
              </div>
            );
          }

          if (msg.type === 'clarification') {
            return (
              <div key={msg.id} className="flex justify-start pr-12">
                <div className="bg-caution border-2 border-ink p-4 shadow-hard-sm w-full relative pt-6 mt-2">
                  <div className="absolute -top-3 left-3 bg-white border-2 border-ink px-2 py-0.5 text-xs font-bold uppercase flex items-center gap-1 shadow-hard-sm">
                    <HelpCircle className="w-3 h-3" /> Quick Question
                  </div>
                  <p className="text-ink font-medium leading-relaxed">{msg.content}</p>
                </div>
              </div>
            );
          }

          // Normal Answer
          return (
            <div key={msg.id} className="flex justify-start pr-12">
              <div className="bg-bg border-2 border-ink p-4 shadow-hard-sm w-full">
                <p className="text-ink font-medium leading-relaxed mb-4">{msg.content}</p>
                
                {/* Citations */}
                {(msg.cited_clauses?.length > 0 || msg.cited_statutes?.length > 0) && (
                  <div className="pt-3 border-t-2 border-ink/20 flex flex-wrap gap-2">
                    {msg.cited_clauses?.map((clauseId, idx) => (
                      <button 
                        key={`c-${idx}`}
                        onClick={() => onClauseClick && onClauseClick(parseInt(clauseId))}
                        className="flex items-center gap-1 bg-white border-2 border-ink px-2 py-1 text-xs font-bold shadow-hard-sm hover:translate-y-px hover:shadow-none transition-all"
                      >
                        <FileText className="w-3 h-3" /> Clause {clauseId}
                      </button>
                    ))}
                    {msg.cited_statutes?.map((statute, idx) => (
                      <div 
                        key={`s-${idx}`}
                        className="flex items-center gap-1 bg-white border-2 border-ink px-2 py-1 text-xs font-bold text-muted shadow-hard-sm"
                      >
                        <BookOpen className="w-3 h-3" /> {statute.act}, Sec {statute.section}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          );
        })}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="flex-none p-4 bg-white border-t-2 border-ink">
        <form 
          className="flex gap-2"
          onSubmit={async (e) => {
            e.preventDefault();
            if (!inputValue.trim() || isLoading) return;
            
            const userText = inputValue;
            setInputValue("");
            
            // Add user message to local state immediately
            const newUserMsg = {
              id: Date.now(),
              role: 'user',
              content: userText
            };
            setConversation(prev => [...prev, newUserMsg]);
            setIsLoading(true);

            try {
              // Prepare history for API
              const apiHistory = [];
              for(let i=0; i<conversation.length; i+=2) {
                 if (i+1 < conversation.length) {
                   apiHistory.push({
                     question: conversation[i].content,
                     answer: conversation[i+1].content
                   });
                 }
              }

              const res = await fetch(`${API_BASE_URL}/documents/${documentId}/ask`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                  question: userText,
                  conversation_history: apiHistory,
                  target_language: targetLanguage
                })
              });
              
              if (!res.ok) throw new Error("API error");
              
              const data = await res.json();
              
              let content = data.type === 'clarification' ? data.question : data.answer;
              if (
                typeof content !== 'string' ||
                content.includes("404") ||
                content.includes("503") ||
                content.includes("ClientError") ||
                content.includes("APIError") ||
                content.includes("models/")
              ) {
                content = "Something went wrong on our end, please try again.";
              }
              
              const newBotMsg = {
                id: Date.now() + 1,
                role: 'assistant',
                type: data.type,
                content: content,
                cited_clauses: data.cited_clauses || [],
                cited_statutes: data.cited_statutes || []
              };
              
              setConversation(prev => [...prev, newBotMsg]);
              
            } catch (err) {
              console.error(err);
              setConversation(prev => [...prev, {
                id: Date.now() + 1,
                role: 'assistant',
                type: 'answer',
                content: 'Something went wrong on our end, please try again.'
              }]);
            } finally {
              setIsLoading(false);
            }
          }}
        >
          <input 
            type="text" 
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            disabled={isLoading}
            placeholder={isLoading ? "Thinking..." : "Ask about this document..."}
            className="flex-1 bg-white border-2 border-ink px-3 py-2 font-sans font-medium focus:outline-none focus:ring-2 focus:ring-accent focus:border-accent disabled:opacity-50"
          />
          <button 
            type="submit"
            disabled={isLoading}
            className="bg-accent text-white border-2 border-ink p-2 shadow-hard-sm hover:translate-y-px hover:shadow-none transition-all flex items-center justify-center disabled:opacity-50"
          >
            <Send className="w-5 h-5" />
          </button>
        </form>
      </div>

    </div>
  );
}
