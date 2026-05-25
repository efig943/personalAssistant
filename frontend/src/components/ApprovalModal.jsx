import React, { useState } from 'react';
import { Calendar, AlertTriangle, Check, X, MessageSquareWarning, RefreshCw } from 'lucide-react';

export default function ApprovalModal({ draft, onApprove, onDecline, onReject, onConflictSend, onProposeNewTime }) {
  const [editedMessage, setEditedMessage] = useState(draft.draft || "");
  const [isRejecting, setIsRejecting] = useState(false);
  const [rejectReason, setRejectReason] = useState("");
  const [approveError, setApproveError] = useState(null);
  const [isApproving, setIsApproving] = useState(false);
  const [isAnchorConflict, setIsAnchorConflict] = useState(false);
  const [newDate, setNewDate] = useState("");
  const [newTime, setNewTime] = useState("");

  const hasConflict = Boolean(draft.conflict);

  const handleApprove = async () => {
    setApproveError(null);
    setIsApproving(true);
    try {
      if (hasConflict) {
        // Conflict path: send the apology message, no calendar event, reset to negotiating
        await onConflictSend(editedMessage);
      } else {
        // Happy path: send confirmation, create calendar event
        await onApprove(editedMessage, draft.proposed_time);
      }
    } catch (err) {
      if (err?.response?.status === 409) {
        setIsAnchorConflict(true);
        const today = new Date();
        setNewDate(today.toISOString().split('T')[0]);
        setNewTime("18:00");
      } else {
        let msg = err?.response?.data?.detail;
        if (Array.isArray(msg)) {
          msg = msg.map(e => `${e.loc?.join('.')} ${e.msg}`).join(', ');
        }
        msg = msg || err?.message || "Failed to send message.";
        setApproveError(msg);
      }
    } finally {
      setIsApproving(false);
    }
  };

  const handleProposeSubmit = async () => {
    setIsApproving(true);
    setApproveError(null);
    try {
      // Create local ISO strings for the new start and end time (1 hour duration)
      const startIso = new Date(`${newDate}T${newTime}`).toISOString();
      const endIso = new Date(new Date(`${newDate}T${newTime}`).getTime() + 3600000).toISOString();
      await onProposeNewTime(startIso, endIso);
    } catch (err) {
      let msg = err?.response?.data?.detail;
      if (Array.isArray(msg)) {
        msg = msg.map(e => `${e.loc?.join('.')} ${e.msg}`).join(', ');
      }
      msg = msg || err?.message || "Failed to propose new time.";
      setApproveError(msg);
    } finally {
      setIsApproving(false);
    }
  };

  return (
    <div 
      className="fixed inset-0 z-[100] flex items-center justify-center bg-black/70 backdrop-blur-md"
      onClick={(e) => {
        if (e.target === e.currentTarget) onDecline();
      }}
    >
      <div className="bg-surface border border-surface shadow-2xl rounded-2xl w-full max-w-lg overflow-hidden flex flex-col scale-100 animate-in fade-in zoom-in-95 duration-200">
        
        {/* Header */}
        <div className={`p-5 border-b border-surface flex items-center justify-between ${hasConflict ? 'bg-work/10' : 'bg-social/10'}`}>
          <h2 className={`text-xl font-bold flex items-center gap-3 ${hasConflict ? 'text-work' : 'text-social'}`}>
            <div className={`w-8 h-8 rounded-full flex items-center justify-center ${hasConflict ? 'bg-work/20' : 'bg-social/20'}`}>
              {hasConflict ? <AlertTriangle size={18} /> : <MessageSquareWarning size={18} />}
            </div>
            {hasConflict ? 'Scheduling Conflict' : 'Approve Social Event'}
          </h2>
          {draft.recipient_name && (
            <span className="bg-background px-3 py-1 rounded-full text-xs font-bold text-text border border-surface shadow-inner">
              To: {draft.recipient_name}
            </span>
          )}
        </div>

        {/* Content */}
        <div className="p-6 space-y-6 flex-1 overflow-y-auto">
          {/* Conflict banner */}
          {hasConflict && (
            <div className="bg-work/10 border border-work/30 rounded-xl p-4 flex gap-3 text-work shadow-sm">
              <AlertTriangle className="shrink-0 mt-0.5" />
              <div>
                <p className="font-bold text-sm tracking-wide uppercase">Conflict Detected</p>
                <p className="text-sm mt-1">{draft.conflict}</p>
                <p className="text-xs mt-2 text-work/70">The draft below will send an apology to your friend. No event will be created — the conversation will reset so you can pick a new time.</p>
              </div>
            </div>
          )}

          {/* Original Context */}
          {draft.original_message && (
            <div className="space-y-2">
              <p className="text-xs font-bold text-muted uppercase tracking-wider ml-1">Friend Said</p>
              <div className="bg-background/50 rounded-xl p-4 border border-surface text-sm italic text-muted">
                "{draft.original_message}"
              </div>
            </div>
          )}

          {/* Proposed Time (only show for non-conflict) */}
          {draft.proposed_time && !hasConflict && (
            <div className="flex items-center gap-3 bg-primary/10 border border-primary/20 text-primary rounded-xl p-4 shadow-sm">
              <Calendar size={20} />
              <div className="text-sm">
                <span className="font-bold">Proposed Time: </span>
                {new Date(draft.proposed_time.start).toLocaleString()}
              </div>
            </div>
          )}

          {/* Draft Message Editor */}
          <div className="space-y-2">
            <p className="text-xs font-bold text-muted uppercase tracking-wider ml-1 flex justify-between items-center">
              <span>Agent Draft</span>
              <span className="text-[10px] font-normal text-muted/50">Edit if needed</span>
            </p>
            <textarea
              value={editedMessage}
              onChange={(e) => setEditedMessage(e.target.value)}
              className="w-full h-28 bg-background border border-surface rounded-xl p-4 text-text focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary/50 resize-none transition-all shadow-inner leading-relaxed text-sm"
            />
          </div>

          {/* Renegotiation UI triggered by a 409 Hard Conflict */}
          {isAnchorConflict && (
            <div className="bg-work/10 border border-work/30 rounded-xl p-4 space-y-4 animate-in slide-in-from-top-2">
              <div className="flex gap-3 text-work">
                <AlertTriangle className="shrink-0 mt-0.5" />
                <div>
                  <p className="font-bold text-sm tracking-wide uppercase">Conflict with Fixed Event</p>
                  <p className="text-sm mt-1">This time slot is blocked by an anchored event (like Work or Sleep) and cannot be overwritten. Please pick a new time to propose.</p>
                </div>
              </div>
              <div className="flex gap-4">
                <div className="flex-1 space-y-1">
                  <label className="text-xs font-bold text-muted uppercase">Date</label>
                  <input 
                    type="date" 
                    value={newDate} 
                    onChange={e => setNewDate(e.target.value)}
                    className="w-full bg-background border border-surface rounded-lg p-2 text-sm text-text focus:outline-none focus:border-primary"
                  />
                </div>
                <div className="flex-1 space-y-1">
                  <label className="text-xs font-bold text-muted uppercase">Time</label>
                  <input 
                    type="time" 
                    value={newTime} 
                    onChange={e => setNewTime(e.target.value)}
                    className="w-full bg-background border border-surface rounded-lg p-2 text-sm text-text focus:outline-none focus:border-primary"
                  />
                </div>
              </div>
            </div>
          )}

          {/* Backend error toast */}
          {approveError && (
            <div className="bg-work/10 border border-work/30 rounded-xl p-3 flex gap-2 text-work text-sm animate-in fade-in duration-150">
              <AlertTriangle size={16} className="shrink-0 mt-0.5" />
              <span>{approveError}</span>
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="p-5 border-t border-surface bg-background/80 backdrop-blur-sm flex flex-col gap-4">
          {isAnchorConflict ? (
            <div className="flex gap-4 justify-between w-full animate-in fade-in">
              <button 
                onClick={onDecline}
                className="px-5 py-2.5 rounded-xl font-semibold text-muted hover:text-work hover:bg-work/10 transition-colors flex items-center gap-2"
              >
                <X size={18} /> Cancel
              </button>
              <button 
                onClick={handleProposeSubmit}
                disabled={isApproving || !newDate || !newTime}
                className="px-6 py-2.5 rounded-xl font-bold bg-primary hover:bg-primary/90 text-white transition-all shadow-lg flex items-center gap-2 disabled:opacity-50"
              >
                {isApproving ? "Proposing…" : "Propose New Time"}
              </button>
            </div>
          ) : isRejecting ? (
            <div className="flex flex-col gap-3 w-full animate-in fade-in slide-in-from-bottom-2 duration-200">
              <input 
                type="text"
                value={rejectReason}
                onChange={(e) => setRejectReason(e.target.value)}
                placeholder="Why? (Optional - e.g., 'Too far, suggest coffee')"
                className="w-full bg-background border border-surface rounded-xl p-3 text-text focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary/50 transition-all shadow-inner text-sm"
                autoFocus
              />
              <div className="flex gap-4 justify-end">
                <button 
                  onClick={() => setIsRejecting(false)}
                  className="px-5 py-2.5 rounded-xl font-semibold text-muted hover:bg-surface transition-colors"
                >
                  Cancel
                </button>
                <button 
                  onClick={() => onReject(rejectReason)}
                  className="px-6 py-2.5 rounded-xl font-bold bg-primary hover:bg-primary/90 text-white transition-all shadow-[0_4px_14px_0_rgba(59,130,246,0.39)] hover:shadow-[0_6px_20px_rgba(59,130,246,0.23)] hover:-translate-y-0.5 active:translate-y-0"
                >
                  Send Rejection
                </button>
              </div>
            </div>
          ) : (
            <div className="flex gap-4 justify-between w-full">
              <button 
                onClick={onDecline}
                className="px-5 py-2.5 rounded-xl font-semibold text-muted hover:text-work hover:bg-work/10 transition-colors flex items-center gap-2"
              >
                <X size={18} /> Dismiss
              </button>
              <div className="flex gap-3">
                {!hasConflict && (
                  <button 
                    onClick={() => setIsRejecting(true)}
                    className="px-5 py-2.5 rounded-xl font-bold border border-primary text-primary hover:bg-primary/10 transition-all flex items-center gap-2"
                  >
                    Reject &amp; Pivot
                  </button>
                )}
                <button 
                  onClick={handleApprove}
                  disabled={isApproving}
                  className={
                    isApproving
                      ? "px-6 py-2.5 rounded-xl font-bold bg-surface text-muted cursor-not-allowed flex items-center gap-2 opacity-60"
                      : hasConflict
                        ? "px-6 py-2.5 rounded-xl font-bold bg-work hover:bg-work/90 text-white transition-all shadow-[0_4px_14px_0_rgba(239,68,68,0.39)] hover:shadow-[0_6px_20px_rgba(239,68,68,0.23)] hover:-translate-y-0.5 active:translate-y-0 flex items-center gap-2"
                        : "px-6 py-2.5 rounded-xl font-bold bg-social hover:bg-social/90 text-background transition-all shadow-[0_4px_14px_0_rgba(16,185,129,0.39)] hover:shadow-[0_6px_20px_rgba(16,185,129,0.23)] hover:-translate-y-0.5 active:translate-y-0 flex items-center gap-2"
                  }
                >
                  {isApproving
                    ? "Sending…"
                    : hasConflict
                      ? <><RefreshCw size={16} /> Send &amp; Reschedule</>
                      : <><Check size={18} /> Approve &amp; Send</>
                  }
                </button>
              </div>
            </div>
          )}
        </div>
        
      </div>
    </div>
  );
}
