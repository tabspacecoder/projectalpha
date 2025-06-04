import React from 'react';
import { createRoot } from 'react-dom/client';
import ChatWidget from './ChatWidget';
import '../index.css'; // Tailwind CSS and any global styles

createRoot(document.getElementById('root')).render(
  <div style={{ background: 'transparent' }}>
  <ChatWidget />
  </div>
);
