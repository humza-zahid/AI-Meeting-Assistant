import React from 'react';
import { 
  Calendar, 
  Clock, 
  Users, 
  TrendingUp, 
  Video, 
  PlayCircle,
  MoreHorizontal,
  Star,
  FileText
} from 'lucide-react';
import type { Page } from '../App';

interface DashboardProps {
  onNavigate: (page: Page) => void;
  onMeetingSelect: (id: string) => void;
}

export const Dashboard: React.FC<DashboardProps> = ({ onNavigate, onMeetingSelect }) => {
  const stats = [
    { label: 'Total Meetings', value: '248', change: '+12%', icon: Video, color: 'blue' },
    { label: 'Hours Recorded', value: '1,420', change: '+8%', icon: Clock, color: 'green' },
    { label: 'Participants', value: '86', change: '+24%', icon: Users, color: 'purple' },
    { label: 'Action Items', value: '142', change: '+16%', icon: FileText, color: 'amber' },
  ];

  const recentMeetings = [
    {
      id: '1',
      title: 'Weekly Team Standup',
      date: '2024-01-15',
      duration: '45 min',
      participants: 8,
      status: 'completed',
      hasTranscript: true,
      isStarred: true
    },
    {
      id: '2',
      title: 'Product Strategy Review',
      date: '2024-01-14',
      duration: '1h 20min',
      participants: 12,
      status: 'completed',
      hasTranscript: true,
      isStarred: false
    },
    {
      id: '3',
      title: 'Client Onboarding Call',
      date: '2024-01-14',
      duration: '30 min',
      participants: 4,
      status: 'completed',
      hasTranscript: true,
      isStarred: false
    },
    {
      id: '4',
      title: 'Engineering Sync',
      date: '2024-01-13',
      duration: '55 min',
      participants: 6,
      status: 'completed',
      hasTranscript: true,
      isStarred: true
    },
  ];

  const upcomingMeetings = [
    {
      id: '5',
      title: 'Quarterly Business Review',
      date: '2024-01-16',
      time: '10:00 AM',
      participants: 15,
    },
    {
      id: '6',
      title: 'Design System Workshop',
      date: '2024-01-16',
      time: '2:00 PM',
      participants: 8,
    },
  ];

  const getColorClasses = (color: string) => {
    const colors = {
      blue: 'bg-blue-500 text-blue-50',
      green: 'bg-green-500 text-green-50',
      purple: 'bg-purple-500 text-purple-50',
      amber: 'bg-amber-500 text-amber-50',
    };
    return colors[color as keyof typeof colors] || 'bg-gray-500 text-gray-50';
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Welcome back, John!</h1>
          <p className="text-gray-600 mt-1">Here's what's happening with your meetings today.</p>
        </div>
        <div className="text-sm text-gray-500">
          {new Date().toLocaleDateString('en-US', { 
            weekday: 'long', 
            year: 'numeric', 
            month: 'long', 
            day: 'numeric' 
          })}
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat, index) => {
          const Icon = stat.icon;
          return (
            <div key={index} className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-shadow">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">{stat.label}</p>
                  <p className="text-2xl font-bold text-gray-900 mt-1">{stat.value}</p>
                  <p className="text-sm text-green-600 mt-1">{stat.change} from last month</p>
                </div>
                <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${getColorClasses(stat.color)}`}>
                  <Icon className="w-6 h-6" />
                </div>
              </div>
            </div>
          );
        })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Meetings */}
        <div className="lg:col-span-2 bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="p-6 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold">Recent Meetings</h2>
              <button
                onClick={() => onNavigate('meetings')}
                className="text-blue-600 hover:text-blue-700 text-sm font-medium"
              >
                View All
              </button>
            </div>
          </div>
          <div className="divide-y divide-gray-200">
            {recentMeetings.map((meeting) => (
              <div key={meeting.id} className="p-6 hover:bg-gray-50 transition-colors cursor-pointer group">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2">
                      <h3 className="font-medium text-gray-900 group-hover:text-blue-600">
                        {meeting.title}
                      </h3>
                      {meeting.isStarred && (
                        <Star className="w-4 h-4 fill-yellow-400 text-yellow-400" />
                      )}
                    </div>
                    <div className="flex items-center space-x-4 mt-2 text-sm text-gray-500">
                      <div className="flex items-center space-x-1">
                        <Calendar className="w-4 h-4" />
                        <span>{new Date(meeting.date).toLocaleDateString()}</span>
                      </div>
                      <div className="flex items-center space-x-1">
                        <Clock className="w-4 h-4" />
                        <span>{meeting.duration}</span>
                      </div>
                      <div className="flex items-center space-x-1">
                        <Users className="w-4 h-4" />
                        <span>{meeting.participants} participants</span>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    {meeting.hasTranscript && (
                      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                        Transcript Ready
                      </span>
                    )}
                    <button
                      onClick={() => {
                        onMeetingSelect(meeting.id);
                        onNavigate('meeting-detail');
                      }}
                      className="text-blue-600 hover:text-blue-700 p-1 rounded"
                    >
                      <PlayCircle className="w-5 h-5" />
                    </button>
                    <button className="text-gray-400 hover:text-gray-600 p-1 rounded">
                      <MoreHorizontal className="w-5 h-5" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Upcoming Meetings */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="p-6 border-b border-gray-200">
            <h2 className="text-lg font-semibold">Upcoming Meetings</h2>
          </div>
          <div className="p-6 space-y-4">
            {upcomingMeetings.map((meeting) => (
              <div key={meeting.id} className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors">
                <h4 className="font-medium text-gray-900">{meeting.title}</h4>
                <div className="mt-2 space-y-1">
                  <div className="flex items-center space-x-2 text-sm text-gray-500">
                    <Calendar className="w-4 h-4" />
                    <span>{new Date(meeting.date).toLocaleDateString()}</span>
                  </div>
                  <div className="flex items-center space-x-2 text-sm text-gray-500">
                    <Clock className="w-4 h-4" />
                    <span>{meeting.time}</span>
                  </div>
                  <div className="flex items-center space-x-2 text-sm text-gray-500">
                    <Users className="w-4 h-4" />
                    <span>{meeting.participants} participants</span>
                  </div>
                </div>
              </div>
            ))}
            
            <button className="w-full p-3 border-2 border-dashed border-gray-300 rounded-lg text-gray-600 hover:bg-gray-50 hover:border-gray-400 transition-colors">
              <Calendar className="w-5 h-5 mx-auto mb-1" />
              <span className="text-sm">Schedule New Meeting</span>
            </button>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg p-6 text-white">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold">Ready to record your next meeting?</h2>
            <p className="mt-1 opacity-90">Get AI-powered transcripts and insights in minutes.</p>
          </div>
          <button className="bg-white text-blue-600 px-6 py-3 rounded-lg font-medium hover:bg-gray-100 transition-colors">
            Start Recording
          </button>
        </div>
      </div>
    </div>
  );
};