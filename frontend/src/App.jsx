import React, { useState, useEffect, useRef, useCallback } from 'react';
import axios from 'axios';
import CalendarPanel from './components/CalendarPanel';
import CRMPanel from './components/CRMPanel';
import ApprovalModal from './components/ApprovalModal';
import SettingsModal from './components/SettingsModal';
import { Settings } from 'lucide-react';

const API_BASE = 'http://localhost:8000/api';

function App() {
  const [pendingDrafts, setPendingDrafts] = useState([]);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const dismissedDraftsRef = useRef(new Set());

  const [appData, setAppData] = useState({
    events: [],
    goals: null,
    contacts: [],
    interests: [],
    states: {}
  });

  const fetchAllData = useCallback(async () => {
    try {
      const [eventsRes, goalsRes, contactsRes, interestsRes, statesRes] = await Promise.all([
        axios.get(`${API_BASE}/calendar/events`),
        axios.get(`${API_BASE}/goals`),
        axios.get(`${API_BASE}/crm/contacts`),
        axios.get(`${API_BASE}/interests`),
        axios.get(`${API_BASE}/social/states`)
      ]);

      const states = statesRes.data;

      setAppData({
        events: eventsRes.data.data?.events || [],
        goals: goalsRes.data,
        contacts: contactsRes.data.contacts || [],
        interests: interestsRes.data.interests || [],
        states: states
      });

      const pending = [];
      for (const [chatId, state] of Object.entries(states)) {
        if (state.status === 'pending_approval' && !dismissedDraftsRef.current.has(chatId)) {
          pending.push({ chatId, ...state });
        }
      }
      // Prevent state thrashing by deep comparing or just updating
      setPendingDrafts(prev => {
        if (JSON.stringify(prev) === JSON.stringify(pending)) return prev;
        return pending;
      });
    } catch (err) {
      console.error('Error fetching master data:', err);
    }
  }, []);

  useEffect(() => {
    fetchAllData();
    const interval = setInterval(fetchAllData, 10000);
    return () => clearInterval(interval);
  }, [fetchAllData]);

  const handleApprove = async (chatId, approvedMessage, proposedTime) => {
    try {
      const res = await axios.post(`${API_BASE}/social/approve`, {
        chat_id: chatId,
        approved_message: approvedMessage,
        event_title: "Social Plan",
        event_start: proposedTime?.start || new Date().toISOString(),
        event_end: proposedTime?.end || new Date(Date.now() + 3600000).toISOString()
      });
      
      // Remove from local state immediately to close modal
      setPendingDrafts(prev => prev.filter(d => d.chatId !== chatId));
      
      // Show verification payload if gap-scan moved an event
      if (res.data?.detail && res.data.detail.includes("successfully moved")) {
        alert(res.data.detail);
      }
      
      return res.data;
    } catch (err) {
      console.error('Approval failed:', err);
      alert('Failed to approve event: ' + err.message);
      throw err;
    }
  };

  const handleDecline = (chatId) => {
    dismissedDraftsRef.current.add(String(chatId));
    setPendingDrafts(prev => prev.filter(d => String(d.chatId) !== String(chatId)));
  };

  const handleReopenProposal = (chatId) => {
    dismissedDraftsRef.current.delete(String(chatId));
    fetchAllData();
  };

  const handleReject = async (chatId, reason) => {
    try {
      await axios.post(`${API_BASE}/social/reject`, {
        chat_id: chatId,
        reason: reason || null
      });
      setPendingDrafts(prev => prev.filter(d => d.chatId !== chatId));
    } catch (err) {
      console.error('Reject failed:', err);
      alert('Failed to reject event: ' + err.message);
    }
  };

  const handleConflictSend = async (chatId, approvedMessage) => {
    // Sends the apology message WITHOUT creating a calendar event, then resets to negotiating.
    const res = await axios.post(`${API_BASE}/social/send_conflict_response`, {
      chat_id: chatId,
      approved_message: approvedMessage,
    });
    setPendingDrafts(prev => prev.filter(d => d.chatId !== chatId));
    return res.data;
  };



  const handleProposeNewTime = async (chatId, newStart, newEnd) => {
    try {
      await axios.post(`${API_BASE}/social/propose`, {
        chat_id: chatId,
        new_start: newStart,
        new_end: newEnd
      });
      setPendingDrafts(prev => prev.filter(d => d.chatId !== chatId));
    } catch (err) {
      console.error('Propose new time failed:', err);
      alert('Failed to propose new time: ' + err.message);
      throw err;
    }
  };

  return (
    <div className="h-screen w-screen bg-background text-text flex overflow-hidden">
      {/* Left Panel: Calendar & Habit Context */}
      <div className="w-1/2 h-full border-r border-surface flex flex-col p-4 overflow-hidden relative">
        <div className="flex justify-between items-center mb-4">
          <h1 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-primary to-social">
            Omni-Assistant
          </h1>
          <button
            onClick={() => setIsSettingsOpen(true)}
            className="p-2 rounded-full hover:bg-surface text-muted hover:text-primary transition-colors focus:outline-none focus:ring-2 focus:ring-primary/50"
            title="Settings & Control Panel"
          >
            <Settings size={22} />
          </button>
        </div>
        <CalendarPanel events={appData.events} goals={appData.goals} />
      </div>

      {/* Right Panel: Telegram CRM */}
      <div className="w-1/2 h-full flex flex-col overflow-hidden">
        <CRMPanel contacts={appData.contacts} onReopenProposal={handleReopenProposal} />
      </div>

      {/* Global Approval Modal */}
      {pendingDrafts.length > 0 && (
        <ApprovalModal
          draft={pendingDrafts[0]}
          onApprove={(msg, time) => handleApprove(pendingDrafts[0].chatId, msg, time)}
          onDecline={() => handleDecline(pendingDrafts[0].chatId)}
          onReject={(reason) => handleReject(pendingDrafts[0].chatId, reason)}
          onConflictSend={(msg) => handleConflictSend(pendingDrafts[0].chatId, msg)}
          onProposeNewTime={(start, end) => handleProposeNewTime(pendingDrafts[0].chatId, start, end)}
        />
      )}

      {/* Settings Modal */}
      {isSettingsOpen && <SettingsModal
        initialGoals={appData.goals}
        initialContacts={appData.contacts}
        initialInterests={appData.interests}
        onClose={() => setIsSettingsOpen(false)}
      />}
    </div>
  );
}

export default App;
