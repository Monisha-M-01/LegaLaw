import React, { useState, useRef, useEffect } from 'react';
import { getLanguage, setLanguage } from '../utils/session';
import { ChevronDown, Globe } from 'lucide-react';

const LANGUAGES = [
  { code: 'en', label: 'English' },
  { code: 'hi', label: 'हिन्दी' },
  { code: 'kn', label: 'ಕನ್ನಡ' },
  { code: 'ta', label: 'தமிழ்' },
  { code: 'te', label: 'తెలుగు' },
  { code: 'ml', label: 'മലയാളം' },
  { code: 'kok', label: 'कोंकणी' }
];

export default function LanguageSelector({ currentLang, onSelect, disabled }) {
  const [isOpen, setIsOpen] = useState(false);
  const activeLangCode = currentLang || getLanguage() || 'en';
  const activeLang = LANGUAGES.find(l => l.code === activeLangCode) || LANGUAGES[0];
  const dropdownRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSelect = (code) => {
    setLanguage(code);
    setIsOpen(false);
    if (onSelect && code !== activeLangCode) {
      onSelect(code);
    }
  };

  return (
    <div className="relative" ref={dropdownRef}>
      <button 
        onClick={() => !disabled && setIsOpen(!isOpen)}
        disabled={disabled}
        className={`flex items-center gap-2 px-3 py-1.5 border-2 border-ink bg-white font-sans font-medium text-sm transition-colors shadow-hard-sm hover:translate-y-px hover:shadow-none ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
      >
        <Globe className="w-4 h-4 text-ink" />
        {activeLang.label}
        <ChevronDown className="w-4 h-4 text-ink ml-1" />
      </button>

      {isOpen && (
        <div className="absolute right-0 top-full mt-2 w-32 bg-white border-2 border-ink shadow-hard z-50 overflow-hidden">
          {LANGUAGES.map((lang) => (
            <button
              key={lang.code}
              onClick={() => handleSelect(lang.code)}
              className={`w-full text-left px-4 py-2 font-sans font-medium text-sm transition-colors
                ${activeLangCode === lang.code ? 'bg-ink text-white' : 'text-ink hover:bg-gray-100'}`}
            >
              {lang.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
