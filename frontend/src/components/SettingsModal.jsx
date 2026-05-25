import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Settings, X, Save, Trash2, Plus } from 'lucide-react';
import { cn } from './CRMPanel';

const API_BASE = 'http://localhost:8000/api';

export default function SettingsModal({ onClose, initialGoals, initialContacts, initialInterests }) {
  const [goals, setGoals] = useState(initialGoals || null);
  const [contacts, setContacts] = useState(initialContacts || []);
  const [interests, setInterests] = useState(initialInterests || []);
  const [activeTab, setActiveTab] = useState('profile');
  const [isSaving, setIsSaving] = useState(false);


  const handleChange = (path, value) => {
    setGoals((prev) => {
      const newGoals = JSON.parse(JSON.stringify(prev)); // deep copy to ensure reactivity
      let current = newGoals;
      for (let i = 0; i < path.length - 1; i++) {
        current = current[path[i]];
      }
      current[path[path.length - 1]] = value;
      return newGoals;
    });
  };

  const handleSave = async () => {
    setIsSaving(true);
    try {
      await Promise.all([
        axios.put(`${API_BASE}/goals`, goals),
        axios.post(`${API_BASE}/contacts`, { contacts }),
        axios.post(`${API_BASE}/interests`, { interests })
      ]);
      window.location.reload();
    } catch (err) {
      console.error('Failed to save settings:', err);
      alert('Failed to save settings: ' + err.message);
      setIsSaving(false);
    }
  };

  if (!goals || !contacts || !interests) {
    return null; // Don't render until loaded
  }

  const daysOfWeek = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/70 backdrop-blur-md">
      <div className="bg-surface border border-surface shadow-2xl rounded-2xl w-full max-w-2xl overflow-hidden flex flex-col h-[80vh] animate-in fade-in zoom-in-95 duration-200">
        
        {/* Header */}
        <div className="bg-background p-5 border-b border-surface flex items-center justify-between">
          <h2 className="text-xl font-bold text-primary flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center">
              <Settings size={18} />
            </div>
            Settings & Control Panel
          </h2>
          <button onClick={onClose} className="p-2 rounded-full hover:bg-surface text-muted transition-colors">
            <X size={20} />
          </button>
        </div>

        {/* Tab Navigation */}
        <div className="flex border-b border-surface bg-background px-6">
          <button 
            className={cn("py-3 px-4 font-semibold text-sm transition-all border-b-2", activeTab === 'profile' ? "border-primary text-primary" : "border-transparent text-muted hover:text-text")}
            onClick={() => setActiveTab('profile')}
          >
            Profile & AI
          </button>
          <button 
            className={cn("py-3 px-4 font-semibold text-sm transition-all border-b-2", activeTab === 'habits' ? "border-primary text-primary" : "border-transparent text-muted hover:text-text")}
            onClick={() => setActiveTab('habits')}
          >
            Core Habits
          </button>
          <button 
            className={cn("py-3 px-4 font-semibold text-sm transition-all border-b-2", activeTab === 'template' ? "border-primary text-primary" : "border-transparent text-muted hover:text-text")}
            onClick={() => setActiveTab('template')}
          >
            Weekly Template
          </button>
          <button 
            className={cn("py-3 px-4 font-semibold text-sm transition-all border-b-2", activeTab === 'contacts' ? "border-primary text-primary" : "border-transparent text-muted hover:text-text")}
            onClick={() => setActiveTab('contacts')}
          >
            Contacts
          </button>
          <button 
            className={cn("py-3 px-4 font-semibold text-sm transition-all border-b-2", activeTab === 'interests' ? "border-primary text-primary" : "border-transparent text-muted hover:text-text")}
            onClick={() => setActiveTab('interests')}
          >
            Interests
          </button>
        </div>

        {/* Tab Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6 bg-background/50">
          
          {activeTab === 'profile' && (
            <div className="space-y-4 animate-in fade-in duration-200">
              <h3 className="font-bold text-text mb-4">Profile Information</h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-muted uppercase tracking-wider mb-1">Name</label>
                  <input type="text" value={goals.profile?.name || ''} onChange={(e) => handleChange(['profile', 'name'], e.target.value)} className="w-full bg-surface border border-surface/50 rounded-lg p-2 text-sm text-text focus:border-primary outline-none" />
                </div>
                <div>
                  <label className="block text-xs font-bold text-muted uppercase tracking-wider mb-1">Timezone</label>
                  <input type="text" value={goals.profile?.timezone || ''} onChange={(e) => handleChange(['profile', 'timezone'], e.target.value)} className="w-full bg-surface border border-surface/50 rounded-lg p-2 text-sm text-text focus:border-primary outline-none" />
                </div>
                <div>
                  <label className="block text-xs font-bold text-muted uppercase tracking-wider mb-1">Social Quota / Week</label>
                  <input type="number" value={goals.profile?.social_events_per_week || 0} onChange={(e) => handleChange(['profile', 'social_events_per_week'], parseInt(e.target.value))} className="w-full bg-surface border border-surface/50 rounded-lg p-2 text-sm text-text focus:border-primary outline-none" />
                </div>
              </div>

              <h3 className="font-bold text-text mb-4 mt-6">LLM Routing</h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-muted uppercase tracking-wider mb-1">Tool Worker Model</label>
                  <input type="text" value={goals.llm_model_routing?.tool_worker || ''} onChange={(e) => handleChange(['llm_model_routing', 'tool_worker'], e.target.value)} className="w-full bg-surface border border-surface/50 rounded-lg p-2 text-sm text-text focus:border-primary outline-none" />
                </div>
                <div>
                  <label className="block text-xs font-bold text-muted uppercase tracking-wider mb-1">Reasoning Worker Model</label>
                  <input type="text" value={goals.llm_model_routing?.reasoning_worker || ''} onChange={(e) => handleChange(['llm_model_routing', 'reasoning_worker'], e.target.value)} className="w-full bg-surface border border-surface/50 rounded-lg p-2 text-sm text-text focus:border-primary outline-none" />
                </div>
              </div>
            </div>
          )}

          {activeTab === 'habits' && (
            <div className="space-y-4 animate-in fade-in duration-200">
              <h3 className="font-bold text-text mb-4">Nutrition & Sleep</h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-muted uppercase tracking-wider mb-1">Baseline Protein (g)</label>
                  <input type="number" value={goals.nutrition?.baseline_protein_floor_g || 0} onChange={(e) => handleChange(['nutrition', 'baseline_protein_floor_g'], parseInt(e.target.value))} className="w-full bg-surface border border-surface/50 rounded-lg p-2 text-sm text-text focus:border-primary outline-none" />
                </div>
                <div>
                  <label className="block text-xs font-bold text-muted uppercase tracking-wider mb-1">Meals Per Day</label>
                  <input type="number" value={goals.nutrition?.meals_per_day || 0} onChange={(e) => handleChange(['nutrition', 'meals_per_day'], parseInt(e.target.value))} className="w-full bg-surface border border-surface/50 rounded-lg p-2 text-sm text-text focus:border-primary outline-none" />
                </div>
                <div>
                  <label className="block text-xs font-bold text-muted uppercase tracking-wider mb-1">Target Wake Time</label>
                  <input type="time" value={goals.sleep_settings?.target_wake_time || '07:00'} onChange={(e) => handleChange(['sleep_settings', 'target_wake_time'], e.target.value)} className="w-full bg-surface border border-surface/50 rounded-lg p-2 text-sm text-text focus:border-primary outline-none" />
                </div>
                <div>
                  <label className="block text-xs font-bold text-muted uppercase tracking-wider mb-1">Sleep Duration (hrs)</label>
                  <input type="number" value={goals.sleep_settings?.required_duration_hours || 8} onChange={(e) => handleChange(['sleep_settings', 'required_duration_hours'], parseInt(e.target.value))} className="w-full bg-surface border border-surface/50 rounded-lg p-2 text-sm text-text focus:border-primary outline-none" />
                </div>
              </div>

              <h3 className="font-bold text-text mb-4 mt-6">Gym Scheduling</h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-muted uppercase tracking-wider mb-1">Session Duration (min)</label>
                  <input type="number" value={goals.gym_scheduling?.session_duration_minutes || 45} onChange={(e) => handleChange(['gym_scheduling', 'session_duration_minutes'], parseInt(e.target.value))} className="w-full bg-surface border border-surface/50 rounded-lg p-2 text-sm text-text focus:border-primary outline-none" />
                </div>
                <div>
                  <label className="block text-xs font-bold text-muted uppercase tracking-wider mb-1">Scan Policy</label>
                  <select value={goals.gym_scheduling?.scan_policy || 'first_available_gap'} onChange={(e) => handleChange(['gym_scheduling', 'scan_policy'], e.target.value)} className="w-full bg-surface border border-surface/50 rounded-lg p-2 text-sm text-text focus:border-primary outline-none">
                    <option value="first_available_gap">First Available Gap</option>
                  </select>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'template' && (
            <div className="space-y-4 animate-in fade-in duration-200">
              <h3 className="font-bold text-text mb-4">Weekly Schedule Anchors</h3>
              {daysOfWeek.map((day) => {
                const dayData = goals.weekly_template_registry?.[day] || {};
                return (
                  <div key={day} className="bg-surface/50 border border-surface rounded-xl p-4 flex flex-col gap-3">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-sm">{day}</span>
                      <div className="flex items-center gap-4">
                        <div className="flex items-center gap-2 text-xs">
                          <label className="text-muted">State:</label>
                          <select 
                            value={dayData.training_state || 'REST'} 
                            onChange={(e) => handleChange(['weekly_template_registry', day, 'training_state'], e.target.value)}
                            className="bg-background border border-surface rounded p-1 text-text outline-none"
                          >
                            <option value="LIFT">LIFT</option>
                            <option value="REST">REST</option>
                            <option value="SPORTS">SPORTS</option>
                          </select>
                        </div>
                        <div className="flex items-center gap-2 text-xs">
                          <label className="text-muted">Multiplier:</label>
                          <input 
                            type="number" 
                            step="0.01"
                            value={dayData.multiplier || 1.0} 
                            onChange={(e) => handleChange(['weekly_template_registry', day, 'multiplier'], parseFloat(e.target.value))}
                            className="bg-background border border-surface rounded p-1 text-text outline-none w-16"
                          />
                        </div>
                        <label className="flex items-center gap-2 text-xs text-muted cursor-pointer">
                          <input 
                            type="checkbox" 
                            checked={dayData.is_anchor || false}
                            onChange={(e) => handleChange(['weekly_template_registry', day, 'is_anchor'], e.target.checked)}
                            className="accent-primary"
                          />
                          Fixed Anchor
                        </label>
                      </div>
                    </div>
                    {dayData.is_anchor && (
                      <div className="flex items-center gap-4 mt-2 pt-2 border-t border-surface/50">
                        <div className="flex items-center gap-2 text-xs">
                          <label className="text-muted">Start Time:</label>
                          <input 
                            type="time" 
                            value={dayData.anchor_start || ''} 
                            onChange={(e) => handleChange(['weekly_template_registry', day, 'anchor_start'], e.target.value)}
                            className="bg-background border border-surface rounded p-1 text-text outline-none"
                          />
                        </div>
                        <div className="flex items-center gap-2 text-xs">
                          <label className="text-muted">End Time:</label>
                          <input 
                            type="time" 
                            value={dayData.anchor_end || ''} 
                            onChange={(e) => handleChange(['weekly_template_registry', day, 'anchor_end'], e.target.value)}
                            className="bg-background border border-surface rounded p-1 text-text outline-none"
                          />
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}

          {activeTab === 'contacts' && (
            <div className="space-y-4 animate-in fade-in duration-200">
              <h3 className="font-bold text-text mb-4">Contacts Registry</h3>
              <div className="space-y-3">
                {contacts.map((contact, index) => (
                  <div key={index} className="bg-surface/50 border border-surface rounded-xl p-4 flex items-start justify-between gap-4">
                    <div className="grid grid-cols-3 gap-4 flex-1">
                      <div>
                        <label className="block text-xs font-bold text-muted uppercase tracking-wider mb-1">Name</label>
                        <input type="text" value={contact.name} onChange={(e) => {
                          const newContacts = [...contacts];
                          newContacts[index].name = e.target.value;
                          setContacts(newContacts);
                        }} className="w-full bg-background border border-surface rounded-lg p-2 text-sm text-text focus:border-primary outline-none" />
                      </div>
                      <div>
                        <label className="block text-xs font-bold text-muted uppercase tracking-wider mb-1">Username</label>
                        <input type="text" value={contact.username} onChange={(e) => {
                          const newContacts = [...contacts];
                          newContacts[index].username = e.target.value;
                          setContacts(newContacts);
                        }} className="w-full bg-background border border-surface rounded-lg p-2 text-sm text-text focus:border-primary outline-none" />
                      </div>
                      <div>
                        <label className="block text-xs font-bold text-muted uppercase tracking-wider mb-1">Urgency (Days)</label>
                        <input type="number" value={contact.urgency_threshold_days} onChange={(e) => {
                          const newContacts = [...contacts];
                          newContacts[index].urgency_threshold_days = parseInt(e.target.value) || 0;
                          setContacts(newContacts);
                        }} className="w-full bg-background border border-surface rounded-lg p-2 text-sm text-text focus:border-primary outline-none" />
                      </div>
                      <div className="col-span-3 flex gap-2">
                        <span className="text-xs bg-work/10 text-work px-2 py-1 rounded-md border border-work/20">
                          ID: {contact.chat_id || "Pending Handshake"}
                        </span>
                        <span className="text-xs bg-social/10 text-social px-2 py-1 rounded-md border border-social/20">
                          Last Contact: {contact.last_contact_time ? new Date(contact.last_contact_time).toLocaleString() : "Never"}
                        </span>
                      </div>
                    </div>
                    <button onClick={() => {
                      const newContacts = contacts.filter((_, i) => i !== index);
                      setContacts(newContacts);
                    }} className="p-2 bg-red-500/10 text-red-500 rounded-lg hover:bg-red-500/20 transition-colors mt-6">
                      <Trash2 size={18} />
                    </button>
                  </div>
                ))}
              </div>
              <button 
                onClick={() => setContacts([...contacts, { name: "", username: "", urgency_threshold_days: 7, chat_id: null, last_contact_time: null }])}
                className="mt-4 flex items-center justify-center gap-2 w-full py-3 border border-dashed border-primary/50 text-primary rounded-xl hover:bg-primary/10 transition-colors font-bold text-sm"
              >
                <Plus size={18} /> Add New Contact
              </button>
            </div>
          )}

          {activeTab === 'interests' && (
            <div className="space-y-4 animate-in fade-in duration-200">
              <h3 className="font-bold text-text mb-4">Interests & Activities</h3>
              <div className="space-y-3">
                {interests.map((interest, index) => (
                  <div key={index} className="flex items-center gap-3">
                    <input type="text" value={interest} onChange={(e) => {
                      const newInterests = [...interests];
                      newInterests[index] = e.target.value;
                      setInterests(newInterests);
                    }} className="flex-1 bg-surface border border-surface rounded-lg p-3 text-sm text-text focus:border-primary outline-none" />
                    <button onClick={() => {
                      const newInterests = interests.filter((_, i) => i !== index);
                      setInterests(newInterests);
                    }} className="p-3 bg-red-500/10 text-red-500 rounded-lg hover:bg-red-500/20 transition-colors">
                      <Trash2 size={18} />
                    </button>
                  </div>
                ))}
              </div>
              <button 
                onClick={() => setInterests([...interests, ""])}
                className="mt-4 flex items-center justify-center gap-2 w-full py-3 border border-dashed border-primary/50 text-primary rounded-xl hover:bg-primary/10 transition-colors font-bold text-sm"
              >
                <Plus size={18} /> Add Interest
              </button>
            </div>
          )}

        </div>

        {/* Footer Actions */}
        <div className="p-5 border-t border-surface bg-background flex justify-end gap-3">
          <button 
            onClick={onClose}
            className="px-5 py-2 rounded-xl font-semibold text-muted hover:bg-surface transition-colors"
          >
            Cancel
          </button>
          <button 
            onClick={handleSave}
            disabled={isSaving}
            className="px-6 py-2 rounded-xl font-bold bg-primary hover:bg-primary/90 text-white transition-all shadow-[0_4px_14px_0_rgba(59,130,246,0.39)] hover:shadow-[0_6px_20px_rgba(59,130,246,0.23)] flex items-center gap-2"
          >
            {isSaving ? "Saving..." : <><Save size={18} /> Save & Apply</>}
          </button>
        </div>

      </div>
    </div>
  );
}
