import React, { useState, useEffect } from 'react';
import { Calendar, dateFnsLocalizer } from 'react-big-calendar';
import { format, parse, startOfWeek, getDay } from 'date-fns';
import enUS from 'date-fns/locale/en-US';
import 'react-big-calendar/lib/css/react-big-calendar.css';
import axios from 'axios';
import { Activity, Moon, Utensils } from 'lucide-react';

const API_BASE = 'http://localhost:8000/api';

const locales = {
  'en-US': enUS,
}
const localizer = dateFnsLocalizer({
  format,
  parse,
  startOfWeek,
  getDay,
  locales,
});

export default function CalendarPanel({ events, goals }) {
  const [view, setView] = useState('week');
  const [date, setDate] = useState(new Date());
  const [selectedEvent, setSelectedEvent] = useState(null);
  

  // Dynamic Nutrition Scan
  const todayName = new Date().toLocaleDateString('en-US', { weekday: 'long' });
  let trainingState = 'REST Day';
  let totalProtein = 0;
  let perMeal = 0;
  let sleepHours = 8;
  
  if (goals) {
    const template = goals.weekly_template_registry?.[todayName] || {};
    const multiplier = template.multiplier || 1.0;
    trainingState = template.training_state ? `${template.training_state} Day` : 'REST Day';
    
    const baseline = goals.nutrition?.baseline_protein_floor_g || 160;
    const meals = goals.nutrition?.meals_per_day || 4;
    
    totalProtein = Math.round(baseline * multiplier);
    perMeal = Math.round(totalProtein / Math.max(1, meals));
    sleepHours = goals.sleep_settings?.required_duration_hours || 8;
  }

  const eventStyleGetter = (event) => {
    let backgroundColor = '#3b82f6'; // default primary
    if (event.type === 'work') backgroundColor = '#ef4444'; // work = red
    if (event.type === 'habit') backgroundColor = '#3b82f6'; // habit = blue
    if (event.type === 'social') backgroundColor = '#10b981'; // social = green
    
    return {
      style: {
        backgroundColor,
        borderRadius: '6px',
        opacity: 0.9,
        color: 'white',
        border: 'none',
        display: 'block',
        padding: '2px 5px',
        fontWeight: 'bold',
        boxShadow: '0 2px 4px rgba(0,0,0,0.2)',
        overflow: 'visible'
      }
    };
  };

  return (
    <div className="flex flex-col h-full gap-4">
      {/* Nutrition & Habit Context Dashboard */}
      <div className="bg-surface rounded-xl p-4 flex justify-between items-center shadow-lg border border-surface/50">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-primary/20 text-primary rounded-xl shadow-inner">
            <Activity size={24} />
          </div>
          <div>
            <p className="text-xs uppercase tracking-wider text-muted font-bold">Today's State</p>
            <p className="font-bold text-xl tracking-tight">{trainingState}</p>
          </div>
        </div>
        <div className="flex items-center gap-3 border-l border-surface pl-6">
          <div className="p-3 bg-social/20 text-social rounded-xl shadow-inner">
            <Utensils size={24} />
          </div>
          <div>
            <p className="text-xs uppercase tracking-wider text-muted font-bold">Protein Goal</p>
            <p className="font-bold text-xl tracking-tight">
              {totalProtein}g <span className="text-sm font-normal text-muted">({perMeal}g/meal)</span>
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <div className="p-3 bg-work/20 text-work rounded-xl shadow-inner">
            <Moon size={24} />
          </div>
          <div>
            <p className="text-xs uppercase tracking-wider text-muted font-bold">Sleep Target</p>
            <p className="font-bold text-xl tracking-tight">{sleepHours} Hours</p>
          </div>
        </div>
      </div>

      {/* Calendar View */}
      <div className="flex-1 bg-surface/30 rounded-xl p-4 border border-surface shadow-inner overflow-hidden">
        <Calendar
          localizer={localizer}
          events={events.map(e => ({
            ...e,
            start: new Date(e.start),
            end: new Date(e.end)
          }))}
          startAccessor="start"
          endAccessor="end"
          view={view}
          onView={(newView) => setView(newView)}
          date={date}
          onNavigate={(newDate) => setDate(newDate)}
          views={['week', 'day']}
          step={30}
          showMultiDayTimes={true}
          eventPropGetter={eventStyleGetter}
          onSelectEvent={(event) => setSelectedEvent(event)}
          className="h-full rounded-lg text-text"
        />
      </div>

      {/* Event Details Modal */}
      {selectedEvent && (
        <div className="absolute inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm p-4">
          <div className="bg-surface border border-surface/50 rounded-2xl p-6 w-full max-w-md shadow-2xl relative">
            <h2 className="text-2xl font-bold mb-4">{selectedEvent.title}</h2>
            
            {selectedEvent.type === 'social' && selectedEvent.extendedProps ? (
              <div className="flex flex-col gap-3 mb-6">
                <div className="flex justify-between border-b border-surface/50 pb-2">
                  <span className="text-muted font-bold uppercase text-xs">Who</span>
                  <span className="font-medium text-right">{selectedEvent.extendedProps.who || 'TBD'}</span>
                </div>
                <div className="flex justify-between border-b border-surface/50 pb-2">
                  <span className="text-muted font-bold uppercase text-xs">What</span>
                  <span className="font-medium text-right">{selectedEvent.extendedProps.what || 'TBD'}</span>
                </div>
                <div className="flex justify-between border-b border-surface/50 pb-2">
                  <span className="text-muted font-bold uppercase text-xs">Where</span>
                  <span className="font-medium text-right">{selectedEvent.extendedProps.where || 'TBD'}</span>
                </div>
                <div className="flex justify-between border-b border-surface/50 pb-2">
                  <span className="text-muted font-bold uppercase text-xs">Date</span>
                  <span className="font-medium text-right">
                    {format(selectedEvent.start, 'EEEE, MMMM d')}
                  </span>
                </div>
                <div className="flex justify-between border-b border-surface/50 pb-2">
                  <span className="text-muted font-bold uppercase text-xs">Time</span>
                  <span className="font-medium text-right">
                    {format(selectedEvent.start, 'h:mm a')}
                  </span>
                </div>
              </div>
            ) : (
              <div className="flex flex-col gap-3 mb-6">
                <div className="flex justify-between border-b border-surface/50 pb-2">
                  <span className="text-muted font-bold uppercase text-xs">Date</span>
                  <span className="font-medium text-right">
                    {format(selectedEvent.start, 'EEEE, MMMM d')}
                  </span>
                </div>
                <div className="flex justify-between border-b border-surface/50 pb-2">
                  <span className="text-muted font-bold uppercase text-xs">Time</span>
                  <span className="font-medium text-right">
                    {format(selectedEvent.start, 'h:mm a')} - {format(selectedEvent.end, 'h:mm a')}
                  </span>
                </div>
                <div className="flex justify-between border-b border-surface/50 pb-2">
                  <span className="text-muted font-bold uppercase text-xs">Type</span>
                  <span className="font-medium text-right capitalize">
                    {selectedEvent.type || 'Event'}
                  </span>
                </div>
              </div>
            )}
            
            <button
              onClick={() => setSelectedEvent(null)}
              className="w-full bg-surface hover:bg-surface/80 border border-surface/50 font-bold py-3 px-4 rounded-xl transition-all"
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
