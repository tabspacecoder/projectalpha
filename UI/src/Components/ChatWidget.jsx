import { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown'
const ChatWidget = () => {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([{ sender: 'bot', text: 'Hi! How can I help you?' }]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [showWelcome, setShowWelcome] = useState(true);
  const messageEndRef = useRef(null);

  const scrollToBottom = () => {
    messageEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

//   const loginPattern = /\\login\s+\\usr<([^>]+)>\s+\\pw<([^>]+)>/;
  const sendMessage = async () => {
    if (!input.trim()) return;
//     const match = input.match(loginPattern);
    if (input == "\\clear"){
        setMessages([{ sender: 'bot', text: 'Hi! How can I help you?' }])
        setInput('');
        setLoading(true);
    }
//     else if(match){
//         setMessages([])
//         setInput('');
//         setLoading(true);
//     }
    else{
        setMessages((prev) => [...prev, { sender: 'user', text: input }]);
        setInput('');
        setLoading(true);
    }


    try {
      const res = await fetch('http://localhost:8000/message', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: input }),
      });
      const { response } = await res.json();
      setMessages((prev) => [...prev, { sender: 'bot', text: response }]);
    } catch {
      setMessages((prev) => [...prev, { sender: 'bot', text: 'Something went wrong.' }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed bottom-10 right-10 z-50 flex flex-col items-end space-y-2">
      {/* Welcome Message */}
      {showWelcome && !open && (
        <div className="relative max-w-xs bg-white text-gray-800 text-sm shadow-xl border border-gray-200 rounded-full px-4 py-2 flex items-center space-x-2 animate-fade-in-down">
          <span className="font-medium">Hello <span className="animate-waving-hand">👋</span></span>
          <button
            onClick={() => setShowWelcome(false)}
            className="text-gray-400 hover:text-gray-600 text-xs"
            aria-label="Close welcome message"
          >
            ✖
          </button>
          {/* Bubble tail */}
          <div className="absolute -bottom-2 right-5 w-3 h-3 bg-white border-r border-b border-gray-200 transform rotate-45 z-0" />
        </div>
      )}


      {/* Chat Icon or Widget */}
      {!open ? (
        <button
          onClick={() => setOpen(true)}
          className="bg-violet-600 hover:bg-violet-700 text-white px-6 py-4 rounded-full shadow-xl transition duration-300 ease-in-out"
          aria-label="Open chat"
        >
          💬
        </button>
      ) : (
        <div className="w-80 h-[520px] bg-white shadow-2xl rounded-2xl flex flex-col border border-gray-300 overflow-hidden animate-fade-in-up">
          {/* Header */}
          <div className="p-4 border-b bg-violet-600 text-white flex justify-between items-center">
            <h4 className="font-bold text-sm">Team Hello World Assistant</h4>
            <button
              onClick={() => setOpen(false)}
              className="hover:text-gray-300 text-lg transition"
              aria-label="Close chat"
            >
              ✖
            </button>
          </div>

          {/* Messages */}
          <div className="flex-1 p-3 overflow-y-auto bg-gray-50 flex flex-col gap-3">
            {messages.map((msg, i) => (
              <div
                key={i}
                className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`rounded-2xl px-4 py-2 max-w-[75%] text-sm shadow-md ${msg.sender === 'user'
                      ? 'bg-blue-100'
                      : 'bg-gray-200'
                    }`}
                >
                <ReactMarkdown>{msg.text}</ReactMarkdown>
                </div>
              </div>
            ))}

            {loading && (
              <div className="flex gap-1 items-center self-start px-3 py-1">
                <span className="w-2 h-2 bg-gray-500 rounded-full animate-[bounceDelay_1.4s_infinite] [animation-delay:-0.32s]"></span>
                <span className="w-2 h-2 bg-gray-500 rounded-full animate-[bounceDelay_1.4s_infinite] [animation-delay:-0.16s]"></span>
                <span className="w-2 h-2 bg-gray-500 rounded-full animate-[bounceDelay_1.4s_infinite]"></span>
              </div>
            )}

            <div ref={messageEndRef} />
          </div>

          {/* Input */}
          <div className="p-3 border-t flex items-center gap-2 bg-white">
            <input
              type="text"
              className="flex-1 border border-gray-300 rounded-full px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500"
              placeholder="Type a message..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
            />
            <button
              onClick={sendMessage}
              className="bg-violet-600 hover:bg-violet-700 text-white px-4 py-2 rounded-full text-sm transition"
            >
              Send
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default ChatWidget;
