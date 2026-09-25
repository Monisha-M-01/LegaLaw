import { v4 as uuidv4 } from 'uuid';

export const getSessionId = () => {
  let sessionId = localStorage.getItem('session_id');
  if (!sessionId) {
    sessionId = uuidv4();
    localStorage.setItem('session_id', sessionId);
  }
  return sessionId;
};

export const clearSessionId = () => {
  localStorage.removeItem('session_id');
  localStorage.removeItem('target_language');
};

export const getLanguage = () => {
  return localStorage.getItem('target_language') || 'en';
};

export const setLanguage = (lang) => {
  localStorage.setItem('target_language', lang);
};
