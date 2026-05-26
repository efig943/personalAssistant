import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { Send, User, MessageCircle, AlertCircle } from 'lucide-react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

// Simple utility to merge tailwind classes
export function cn(...inputs) {
  return twMerge(clsx(inputs));
}

const API_BASE = 'http://localhost:8000/api';

export default function CRMPanel({ contacts, onReopenProposal }) {
  const [selectedUsername, setSelectedUsername] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputText, setInputText] = useState("");
  const [manualChatId, setManualChatId] = useState("");
  const hasAutoSelected = useRef(false);

  // Only auto-select the first contact on initial load — never again.
  // Using a ref guard prevents the polling refresh of `contacts` (every 10s)
  // from racing with the user's manual selection and resetting it.
  useEffect(() => {
    if (!hasAutoSelected.current && contacts?.length > 0) {
      setSelectedUsername(contacts[0].username);
      hasAutoSelected.current = true;
    }
  }, [contacts]);

  const activeContact = contacts?.find(c => c.username === selectedUsername);
  const activeChatId = activeContact?.chat_id;

  // Fetch messages for selected contact
  useEffect(() => {
    if (!activeChatId) {
      setMessages([]);
      return;
    }
    const fetchMessages = async () => {
      try {
        const res = await axios.get(`${API_BASE}/crm/messages/${activeChatId}`);
        setMessages(res.data.messages || []);
      } catch (err) {
        console.error("Failed to fetch messages", err);
      }
    };
    fetchMessages();
    const interval = setInterval(fetchMessages, 10000);
    return () => clearInterval(interval);
  }, [activeChatId]);

  const handleSaveChatId = async () => {
    const newContacts = contacts.map(c => {
      if (c.username === activeContact.username) {
        return {
          ...c,
          chat_id: manualChatId.trim() === "" ? null : Number(manualChatId.trim())
        };
      }
      return c;
    });
    try {
      await axios.post(`${API_BASE}/contacts`, { contacts: newContacts });
      window.location.reload();
    } catch (e) {
      console.error(e);
      alert("Failed to save contact");
    }
  };

  return (
    <div className="flex h-full w-full bg-background border-l border-surface">
      {/* Sidebar */}
      <div className="w-1/3 border-r border-surface flex flex-col bg-background/50">
        <div className="p-6 border-b border-surface flex items-center justify-between">
          <h2 className="text-xl font-bold flex items-center gap-3">
            <MessageCircle size={24} className="text-social" /> CRM
          </h2>
          <span className="text-xs font-semibold bg-surface px-2 py-1 rounded-md text-muted border border-surface/50">
            {contacts.length} Contacts
          </span>
        </div>
        <div className="flex-1 overflow-y-auto">
          {contacts.map((contact) => {
            // Determine urgency
            const lastContact = new Date(contact.last_contact_time);
            const daysSince = (new Date() - lastContact) / (1000 * 60 * 60 * 24);
            const isUrgent = daysSince >= contact.urgency_threshold_days;

            return (
              <div 
                key={contact.username}
                onClick={() => {
                  setSelectedUsername(contact.username);
                  setManualChatId("");
                }}
                className={cn(
                  "p-4 cursor-pointer hover:bg-surface/50 border-b border-surface/50 flex items-center justify-between transition-all",
                  selectedUsername === contact.username ? "bg-surface border-l-4 border-l-primary" : "border-l-4 border-l-transparent"
                )}
              >
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center text-primary shadow-inner">
                    <User size={20} />
                  </div>
                  <div>
                    <p className="font-semibold text-text">{contact.name}</p>
                    <p className="text-xs text-muted">
                      {daysSince.toFixed(1)} days ago
                    </p>
                  </div>
                </div>
                {isUrgent ? (
                  <div className="w-8 h-8 rounded-full bg-work/10 flex items-center justify-center text-work animate-pulse" title="High Urgency">
                    <AlertCircle size={18} />
                  </div>
                ) : (
                  <div className="w-3 h-3 rounded-full bg-social shadow-lg shadow-social/50" title="Healthy"></div>
                )}
              </div>
            );
          })}
          {contacts.length === 0 && (
            <div className="p-6 text-center text-muted text-sm">
              No contacts in registry.
            </div>
          )}
        </div>
      </div>

      {/* Chat Canvas */}
      <div className="w-2/3 flex flex-col bg-[url('https://www.transparenttextures.com/patterns/cubes.png')] bg-opacity-5">
        {selectedUsername && activeContact ? (() => {
          return (
          <>
            <div className="p-4 border-b border-surface bg-surface/80 backdrop-blur-md flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center text-primary">
                <User size={20} />
              </div>
              <div>
                <h3 className="font-bold text-lg text-text">
                  {activeContact?.name || 'Chat'}
                </h3>
                <p className="text-xs text-social flex items-center gap-1">
                  <span className="w-2 h-2 rounded-full bg-social inline-block"></span> {activeContact?.chat_id ? "Online" : "Pending Handshake"}
                </p>
              </div>
            </div>
            
            <div className="flex-1 overflow-y-auto p-6 space-y-6 flex flex-col">
              {!activeContact?.chat_id ? (
                <div className="h-full flex flex-col items-center justify-center text-muted gap-4 w-3/4 mx-auto">
                  <div className="w-16 h-16 rounded-full bg-yellow-500/10 flex items-center justify-center text-yellow-500 border border-yellow-500/30">
                    <AlertCircle size={32} />
                  </div>
                  <div className="text-center">
                    <p className="font-bold text-lg text-yellow-500 mb-2">Pending Telegram Link: This contact cannot receive proactive messages yet.</p>
                    <p className="text-sm">Ask {activeContact?.name} to message the bot to auto-link their account, or paste their Chat ID below.</p>
                  </div>
                  <div className="flex w-full gap-2 mt-4">
                    <input 
                      type="text" 
                      placeholder="Enter Chat ID manually..." 
                      className="flex-1 bg-background border border-surface rounded-lg p-3 text-sm text-text outline-none focus:border-primary transition-colors"
                      value={manualChatId}
                      onChange={(e) => setManualChatId(e.target.value)}
                    />
                    <button 
                      onClick={handleSaveChatId}
                      className="bg-primary text-white px-6 py-3 rounded-lg font-bold hover:bg-primary/90 transition-colors"
                    >
                      Save
                    </button>
                  </div>
                </div>
              ) : messages.length === 0 ? (
                <div className="h-full flex items-center justify-center text-muted">
                  No messages history found.
                </div>
              ) : (
                messages.map((msg, idx) => {
                  const isAgent = msg.sender?.startsWith('agent');
                  return (
                    <div key={idx} className={cn("flex flex-col max-w-[75%]", isAgent ? "ml-auto items-end" : "mr-auto items-start")}>
                      <span className="text-xs text-muted mb-1 font-semibold tracking-wide ml-1 mr-1">{msg.name}</span>
                      <div 
                        onClick={() => {
                          if (msg.pending_approval && onReopenProposal) {
                            onReopenProposal(activeContact.chat_id);
                          }
                        }}
                        className={cn(
                        "p-4 rounded-2xl shadow-sm text-sm leading-relaxed",
                        isAgent ? "bg-primary text-white rounded-tr-none" : "bg-surface text-text rounded-tl-none border border-surface/50",
                        msg.pending_approval && "border-2 border-yellow-500/50 bg-yellow-500/20 text-yellow-100 shadow-[0_0_15px_rgba(234,179,8,0.2)] animate-pulse cursor-pointer hover:bg-yellow-500/30 hover:shadow-[0_0_20px_rgba(234,179,8,0.3)] transition-all"
                      )}>
                        {msg.text}
                      </div>
                    </div>
                  );
                })
              )}
            </div>

            <div className="p-4 border-t border-surface bg-background/80 backdrop-blur-sm">
              <div className="flex items-center gap-2 bg-surface p-2 rounded-full border border-surface focus-within:border-primary/50 focus-within:ring-2 focus-within:ring-primary/20 transition-all shadow-inner">
                <input 
                  type="text" 
                  value={inputText}
                  onChange={(e) => setInputText(e.target.value)}
                  placeholder={activeContact?.chat_id ? "Type a message to send directly..." : "Waiting for handshake..."}
                  disabled={!activeContact?.chat_id}
                  className="flex-1 bg-transparent border-none outline-none px-4 text-text placeholder-muted/50 disabled:opacity-50"
                />
                <button 
                  disabled={!activeContact?.chat_id}
                  className="w-10 h-10 rounded-full bg-primary flex items-center justify-center text-white hover:bg-primary/90 transition-all hover:scale-105 active:scale-95 shadow-md shadow-primary/20 disabled:opacity-50 disabled:hover:scale-100 disabled:cursor-not-allowed"
                  onClick={() => alert('Manual send not fully hooked up in backend yet.')}
                >
                  <Send size={18} className="ml-1" />
                </button>
              </div>
            </div>
          </>
          );
        })() : (
          <div className="h-full flex flex-col items-center justify-center text-muted gap-4">
            <div className="w-16 h-16 rounded-full bg-surface flex items-center justify-center text-muted/50">
              <MessageCircle size={32} />
            </div>
            <p>Select a contact to view chat</p>
          </div>
        )}
      </div>
    </div>
  );
}
