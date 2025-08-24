import React, { useState } from 'react';
import { 
  ArrowLeft, 
  Play, 
  Pause, 
  Download, 
  Share, 
  Star,
  Clock,
  Users,
  Calendar,
  FileText,
  Search,
  Copy,
  CheckSquare
} from 'lucide-react';

interface MeetingDetailProps {
  meetingId: string | null;
  onBack: () => void;
}

export const MeetingDetail: React.FC<MeetingDetailProps> = ({ meetingId, onBack }) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [activeTab, setActiveTab] = useState<'transcript' | 'summary' | 'action-items'>('transcript');

  const meeting = {
    id: meetingId || '1',
    title: 'Weekly Team Standup',
    date: '2024-01-15',
    time: '9:00 AM',
    duration: '45 min',
    participants: [
      { name: 'John Doe', role: 'Product Manager', avatar: 'JD' },
      { name: 'Sarah Chen', role: 'Engineer', avatar: 'SC' },
      { name: 'Mike Johnson', role: 'Designer', avatar: 'MJ' },
      { name: 'Emily Davis', role: 'Marketing', avatar: 'ED' },
    ],
    isStarred: true,
    thumbnail: 'https://images.pexels.com/photos/3184292/pexels-photo-3184292.jpeg?auto=compress&cs=tinysrgb&w=800'
  };

  const transcript = [
    {
      speaker: 'John Doe',
      time: '00:02',
      text: 'Good morning everyone, thanks for joining today\'s standup. Let\'s start with updates from each team member.'
    },
    {
      speaker: 'Sarah Chen', 
      time: '00:15',
      text: 'I completed the user authentication feature yesterday. Today I\'m working on the dashboard improvements and should have that ready by end of week.'
    },
    {
      speaker: 'Mike Johnson',
      time: '00:45', 
      text: 'I finished the mockups for the new landing page. I\'ve shared them in Figma and would love to get feedback from everyone by Wednesday.'
    },
    {
      speaker: 'Emily Davis',
      time: '01:20',
      text: 'The campaign performance looks great this month. We\'re seeing a 25% increase in sign-ups. I\'ll have the full report ready for the stakeholder meeting on Friday.'
    },
  ];

  const summary = {
    keyPoints: [
      'User authentication feature completed by Sarah',
      'Dashboard improvements in progress, ETA end of week',
      'New landing page mockups ready for review',
      'Campaign performance up 25% this month',
      'Stakeholder meeting scheduled for Friday'
    ],
    topics: ['Product Development', 'Design Review', 'Marketing Performance', 'Team Updates'],
    sentiment: 'Positive'
  };

  const actionItems = [
    {
      id: 1,
      task: 'Review landing page mockups in Figma',
      assignee: 'Team',
      dueDate: 'Wednesday',
      completed: false
    },
    {
      id: 2,
      task: 'Complete dashboard improvements',
      assignee: 'Sarah Chen',
      dueDate: 'End of week',
      completed: false
    },
    {
      id: 3,
      task: 'Prepare full campaign report',
      assignee: 'Emily Davis',
      dueDate: 'Friday',
      completed: false
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-start space-x-4">
          <button
            onClick={onBack}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-2xl font-bold text-gray-900">{meeting.title}</h1>
              <button className="p-1 hover:bg-gray-100 rounded">
                <Star className={`w-5 h-5 ${meeting.isStarred ? 'fill-yellow-400 text-yellow-400' : 'text-gray-400'}`} />
              </button>
            </div>
            <div className="flex items-center space-x-6 mt-2 text-sm text-gray-500">
              <div className="flex items-center space-x-1">
                <Calendar className="w-4 h-4" />
                <span>{new Date(meeting.date).toLocaleDateString()} at {meeting.time}</span>
              </div>
              <div className="flex items-center space-x-1">
                <Clock className="w-4 h-4" />
                <span>{meeting.duration}</span>
              </div>
              <div className="flex items-center space-x-1">
                <Users className="w-4 h-4" />
                <span>{meeting.participants.length} participants</span>
              </div>
            </div>
          </div>
        </div>
        
        <div className="flex items-center space-x-2">
          <button className="flex items-center space-x-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">
            <Share className="w-4 h-4" />
            <span>Share</span>
          </button>
          <button className="flex items-center space-x-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">
            <Download className="w-4 h-4" />
            <span>Download</span>
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Video Player */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
            <div className="relative">
              <img 
                src={meeting.thumbnail} 
                alt={meeting.title}
                className="w-full h-80 object-cover"
              />
              <div className="absolute inset-0 bg-black bg-opacity-20 flex items-center justify-center">
                <button
                  onClick={() => setIsPlaying(!isPlaying)}
                  className="bg-white text-gray-900 p-4 rounded-full hover:bg-gray-100 transition-colors shadow-lg"
                >
                  {isPlaying ? (
                    <Pause className="w-8 h-8" />
                  ) : (
                    <Play className="w-8 h-8 ml-1" />
                  )}
                </button>
              </div>
            </div>
            
            {/* Video Controls */}
            <div className="p-4 bg-gray-50 border-t">
              <div className="flex items-center space-x-4">
                <button
                  onClick={() => setIsPlaying(!isPlaying)}
                  className="p-2 hover:bg-gray-200 rounded transition-colors"
                >
                  {isPlaying ? (
                    <Pause className="w-5 h-5" />
                  ) : (
                    <Play className="w-5 h-5" />
                  )}
                </button>
                <div className="flex-1 bg-gray-300 rounded-full h-2">
                  <div className="bg-blue-500 h-2 rounded-full" style={{ width: '35%' }}></div>
                </div>
                <span className="text-sm text-gray-600">15:45 / 45:00</span>
              </div>
            </div>
          </div>

          {/* Tabs */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200">
            <div className="border-b border-gray-200">
              <nav className="flex space-x-8 px-6">
                {[
                  { id: 'transcript', label: 'Transcript', icon: FileText },
                  { id: 'summary', label: 'Summary', icon: FileText },
                  { id: 'action-items', label: 'Action Items', icon: CheckSquare },
                ].map((tab) => {
                  const Icon = tab.icon;
                  return (
                    <button
                      key={tab.id}
                      onClick={() => setActiveTab(tab.id as typeof activeTab)}
                      className={`flex items-center space-x-2 py-4 border-b-2 transition-colors ${
                        activeTab === tab.id
                          ? 'border-blue-500 text-blue-600'
                          : 'border-transparent text-gray-600 hover:text-gray-900'
                      }`}
                    >
                      <Icon className="w-4 h-4" />
                      <span className="font-medium">{tab.label}</span>
                    </button>
                  );
                })}
              </nav>
            </div>

            <div className="p-6">
              {activeTab === 'transcript' && (
                <div className="space-y-4">
                  <div className="flex items-center space-x-4 mb-6">
                    <div className="flex-1 relative">
                      <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                      <input
                        type="text"
                        placeholder="Search transcript..."
                        className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      />
                    </div>
                    <button className="flex items-center space-x-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">
                      <Copy className="w-4 h-4" />
                      <span>Copy All</span>
                    </button>
                  </div>
                  
                  <div className="space-y-4">
                    {transcript.map((item, index) => (
                      <div key={index} className="flex space-x-4 p-4 rounded-lg hover:bg-gray-50 transition-colors">
                        <div className="text-sm text-blue-600 font-medium min-w-[50px]">
                          {item.time}
                        </div>
                        <div className="flex-1">
                          <div className="font-medium text-gray-900 mb-1">{item.speaker}</div>
                          <div className="text-gray-700">{item.text}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {activeTab === 'summary' && (
                <div className="space-y-6">
                  <div>
                    <h3 className="text-lg font-semibold mb-3">Key Points</h3>
                    <ul className="space-y-2">
                      {summary.keyPoints.map((point, index) => (
                        <li key={index} className="flex items-start space-x-2">
                          <div className="w-2 h-2 bg-blue-500 rounded-full mt-2 flex-shrink-0"></div>
                          <span className="text-gray-700">{point}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                  
                  <div>
                    <h3 className="text-lg font-semibold mb-3">Topics Discussed</h3>
                    <div className="flex flex-wrap gap-2">
                      {summary.topics.map((topic, index) => (
                        <span key={index} className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm">
                          {topic}
                        </span>
                      ))}
                    </div>
                  </div>
                  
                  <div>
                    <h3 className="text-lg font-semibold mb-3">Overall Sentiment</h3>
                    <span className="inline-flex items-center px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm font-medium">
                      {summary.sentiment}
                    </span>
                  </div>
                </div>
              )}

              {activeTab === 'action-items' && (
                <div className="space-y-4">
                  {actionItems.map((item) => (
                    <div key={item.id} className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors">
                      <div className="flex items-start space-x-3">
                        <input
                          type="checkbox"
                          checked={item.completed}
                          onChange={() => {}}
                          className="mt-1 w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                        />
                        <div className="flex-1">
                          <h4 className="font-medium text-gray-900">{item.task}</h4>
                          <div className="flex items-center space-x-4 mt-2 text-sm text-gray-500">
                            <span>Assigned to: {item.assignee}</span>
                            <span>Due: {item.dueDate}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Participants */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h3 className="text-lg font-semibold mb-4">Participants</h3>
            <div className="space-y-3">
              {meeting.participants.map((participant, index) => (
                <div key={index} className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-blue-500 rounded-full flex items-center justify-center text-white font-medium">
                    {participant.avatar}
                  </div>
                  <div>
                    <div className="font-medium text-gray-900">{participant.name}</div>
                    <div className="text-sm text-gray-500">{participant.role}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Meeting Stats */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h3 className="text-lg font-semibold mb-4">Meeting Stats</h3>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-600">Duration</span>
                <span className="font-medium">45 minutes</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Words spoken</span>
                <span className="font-medium">2,847</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Action items</span>
                <span className="font-medium">3</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Questions asked</span>
                <span className="font-medium">7</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};