import React, { useState } from 'react';
import { 
  Search, 
  Filter, 
  Calendar, 
  Clock, 
  Users, 
  PlayCircle, 
  Download,
  Star,
  MoreHorizontal,
  Grid,
  List,
  ChevronDown
} from 'lucide-react';
import type { Page } from '../App';

interface MeetingsProps {
  onNavigate: (page: Page) => void;
  onMeetingSelect: (id: string) => void;
}

export const Meetings: React.FC<MeetingsProps> = ({ onNavigate, onMeetingSelect }) => {
  const [view, setView] = useState<'grid' | 'list'>('grid');
  const [filterOpen, setFilterOpen] = useState(false);
  const [selectedFilter, setSelectedFilter] = useState('all');

  const meetings = [
    {
      id: '1',
      title: 'Weekly Team Standup',
      date: '2024-01-15',
      time: '9:00 AM',
      duration: '45 min',
      participants: 8,
      status: 'completed',
      hasTranscript: true,
      isStarred: true,
      thumbnail: 'https://images.pexels.com/photos/3184292/pexels-photo-3184292.jpeg?auto=compress&cs=tinysrgb&w=400'
    },
    {
      id: '2',
      title: 'Product Strategy Review',
      date: '2024-01-14',
      time: '2:00 PM',
      duration: '1h 20min',
      participants: 12,
      status: 'completed',
      hasTranscript: true,
      isStarred: false,
      thumbnail: 'https://images.pexels.com/photos/3184465/pexels-photo-3184465.jpeg?auto=compress&cs=tinysrgb&w=400'
    },
    {
      id: '3',
      title: 'Client Onboarding Call',
      date: '2024-01-14',
      time: '10:30 AM',
      duration: '30 min',
      participants: 4,
      status: 'completed',
      hasTranscript: true,
      isStarred: false,
      thumbnail: 'https://images.pexels.com/photos/3184339/pexels-photo-3184339.jpeg?auto=compress&cs=tinysrgb&w=400'
    },
    {
      id: '4',
      title: 'Engineering Sync',
      date: '2024-01-13',
      time: '11:00 AM',
      duration: '55 min',
      participants: 6,
      status: 'completed',
      hasTranscript: true,
      isStarred: true,
      thumbnail: 'https://images.pexels.com/photos/3184418/pexels-photo-3184418.jpeg?auto=compress&cs=tinysrgb&w=400'
    },
    {
      id: '5',
      title: 'Marketing Campaign Review',
      date: '2024-01-12',
      time: '3:30 PM',
      duration: '1h 15min',
      participants: 10,
      status: 'completed',
      hasTranscript: true,
      isStarred: false,
      thumbnail: 'https://images.pexels.com/photos/3184291/pexels-photo-3184291.jpeg?auto=compress&cs=tinysrgb&w=400'
    },
    {
      id: '6',
      title: 'User Research Session',
      date: '2024-01-11',
      time: '1:00 PM',
      duration: '2h 30min',
      participants: 15,
      status: 'completed',
      hasTranscript: true,
      isStarred: true,
      thumbnail: 'https://images.pexels.com/photos/3184357/pexels-photo-3184357.jpeg?auto=compress&cs=tinysrgb&w=400'
    },
  ];

  const filters = [
    { id: 'all', label: 'All Meetings', count: meetings.length },
    { id: 'starred', label: 'Starred', count: meetings.filter(m => m.isStarred).length },
    { id: 'recent', label: 'Recent', count: 10 },
    { id: 'long', label: '1+ Hour', count: 3 },
  ];

  const handleMeetingClick = (meetingId: string) => {
    onMeetingSelect(meetingId);
    onNavigate('meeting-detail');
  };

  const MeetingCard = ({ meeting }: { meeting: typeof meetings[0] }) => (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden hover:shadow-md transition-shadow group">
      <div className="relative">
        <img 
          src={meeting.thumbnail} 
          alt={meeting.title}
          className="w-full h-32 object-cover"
        />
        <div className="absolute inset-0 bg-black bg-opacity-40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
          <button
            onClick={() => handleMeetingClick(meeting.id)}
            className="bg-white text-gray-900 p-3 rounded-full hover:bg-gray-100 transition-colors"
          >
            <PlayCircle className="w-6 h-6" />
          </button>
        </div>
        <div className="absolute top-3 left-3">
          {meeting.hasTranscript && (
            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-500 text-white">
              Transcript
            </span>
          )}
        </div>
        <div className="absolute top-3 right-3">
          {meeting.isStarred && (
            <Star className="w-5 h-5 fill-yellow-400 text-yellow-400" />
          )}
        </div>
        <div className="absolute bottom-3 right-3">
          <span className="bg-black bg-opacity-70 text-white px-2 py-1 rounded text-sm">
            {meeting.duration}
          </span>
        </div>
      </div>
      
      <div className="p-4">
        <h3 className="font-semibold text-gray-900 mb-2 group-hover:text-blue-600 cursor-pointer">
          {meeting.title}
        </h3>
        <div className="space-y-1 text-sm text-gray-500">
          <div className="flex items-center space-x-2">
            <Calendar className="w-4 h-4" />
            <span>{new Date(meeting.date).toLocaleDateString()} at {meeting.time}</span>
          </div>
          <div className="flex items-center space-x-2">
            <Users className="w-4 h-4" />
            <span>{meeting.participants} participants</span>
          </div>
        </div>
        
        <div className="flex items-center justify-between mt-4 pt-3 border-t border-gray-100">
          <button
            onClick={() => handleMeetingClick(meeting.id)}
            className="text-blue-600 hover:text-blue-700 font-medium text-sm"
          >
            View Details
          </button>
          <div className="flex items-center space-x-2">
            <button className="text-gray-400 hover:text-gray-600 p-1 rounded">
              <Download className="w-4 h-4" />
            </button>
            <button className="text-gray-400 hover:text-gray-600 p-1 rounded">
              <MoreHorizontal className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );

  const MeetingRow = ({ meeting }: { meeting: typeof meetings[0] }) => (
    <div className="bg-white border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors group cursor-pointer">
      <div className="flex items-center space-x-4">
        <div className="relative flex-shrink-0">
          <img 
            src={meeting.thumbnail} 
            alt={meeting.title}
            className="w-16 h-12 rounded object-cover"
          />
          <div className="absolute inset-0 bg-black bg-opacity-40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center rounded">
            <PlayCircle className="w-5 h-5 text-white" />
          </div>
        </div>
        
        <div className="flex-1 min-w-0">
          <div className="flex items-center space-x-2">
            <h3 className="font-medium text-gray-900 truncate group-hover:text-blue-600">
              {meeting.title}
            </h3>
            {meeting.isStarred && (
              <Star className="w-4 h-4 fill-yellow-400 text-yellow-400 flex-shrink-0" />
            )}
          </div>
          <div className="flex items-center space-x-4 mt-1 text-sm text-gray-500">
            <span>{new Date(meeting.date).toLocaleDateString()} at {meeting.time}</span>
            <span>{meeting.duration}</span>
            <span>{meeting.participants} participants</span>
            {meeting.hasTranscript && (
              <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                Transcript Ready
              </span>
            )}
          </div>
        </div>
        
        <div className="flex items-center space-x-2">
          <button
            onClick={() => handleMeetingClick(meeting.id)}
            className="text-blue-600 hover:text-blue-700 p-2 rounded"
          >
            <PlayCircle className="w-5 h-5" />
          </button>
          <button className="text-gray-400 hover:text-gray-600 p-2 rounded">
            <Download className="w-4 h-4" />
          </button>
          <button className="text-gray-400 hover:text-gray-600 p-2 rounded">
            <MoreHorizontal className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Meetings</h1>
          <p className="text-gray-600 mt-1">Manage and review your recorded meetings</p>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-4 sm:space-y-0 sm:space-x-4">
        <div className="flex-1 max-w-md relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
          <input
            type="text"
            placeholder="Search meetings..."
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
        
        <div className="flex items-center space-x-3">
          <div className="relative">
            <button
              onClick={() => setFilterOpen(!filterOpen)}
              className="flex items-center space-x-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            >
              <Filter className="w-4 h-4" />
              <span>Filter</span>
              <ChevronDown className="w-4 h-4" />
            </button>
            
            {filterOpen && (
              <div className="absolute right-0 mt-2 w-48 bg-white border border-gray-200 rounded-lg shadow-lg z-10">
                <div className="p-2">
                  {filters.map((filter) => (
                    <button
                      key={filter.id}
                      onClick={() => {
                        setSelectedFilter(filter.id);
                        setFilterOpen(false);
                      }}
                      className={`w-full flex items-center justify-between px-3 py-2 text-sm rounded hover:bg-gray-100 transition-colors ${
                        selectedFilter === filter.id ? 'bg-blue-50 text-blue-700' : 'text-gray-700'
                      }`}
                    >
                      <span>{filter.label}</span>
                      <span className="text-gray-400">({filter.count})</span>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
          
          <div className="flex border border-gray-300 rounded-lg">
            <button
              onClick={() => setView('grid')}
              className={`p-2 ${view === 'grid' ? 'bg-blue-50 text-blue-600' : 'text-gray-600 hover:bg-gray-50'} transition-colors`}
            >
              <Grid className="w-5 h-5" />
            </button>
            <button
              onClick={() => setView('list')}
              className={`p-2 ${view === 'list' ? 'bg-blue-50 text-blue-600' : 'text-gray-600 hover:bg-gray-50'} transition-colors`}
            >
              <List className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>

      {/* Meetings Display */}
      {view === 'grid' ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {meetings.map((meeting) => (
            <MeetingCard key={meeting.id} meeting={meeting} />
          ))}
        </div>
      ) : (
        <div className="space-y-3">
          {meetings.map((meeting) => (
            <MeetingRow key={meeting.id} meeting={meeting} />
          ))}
        </div>
      )}

      {/* Load More */}
      <div className="text-center pt-6">
        <button className="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">
          Load More Meetings
        </button>
      </div>
    </div>
  );
};