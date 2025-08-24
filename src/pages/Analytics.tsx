import React, { useState } from 'react';
import { TrendingUp, Clock, Users, MessageCircle, Calendar, BarChart3 } from 'lucide-react';

export const Analytics: React.FC = () => {
  const [timeRange, setTimeRange] = useState('30d');

  const stats = [
    {
      label: 'Total Meetings',
      value: '248',
      change: '+12%',
      trend: 'up',
      icon: BarChart3,
    },
    {
      label: 'Total Hours',
      value: '1,420',
      change: '+8%',
      trend: 'up',
      icon: Clock,
    },
    {
      label: 'Avg. Meeting Length',
      value: '42min',
      change: '-5%',
      trend: 'down',
      icon: TrendingUp,
    },
    {
      label: 'Participants',
      value: '86',
      change: '+24%',
      trend: 'up',
      icon: Users,
    },
  ];

  const meetingTrends = [
    { month: 'Jan', meetings: 45, hours: 180 },
    { month: 'Feb', meetings: 52, hours: 208 },
    { month: 'Mar', meetings: 48, hours: 192 },
    { month: 'Apr', meetings: 61, hours: 244 },
    { month: 'May', meetings: 55, hours: 220 },
    { month: 'Jun', meetings: 67, hours: 268 },
  ];

  const topParticipants = [
    { name: 'John Doe', meetings: 24, hours: 96, avatar: 'JD' },
    { name: 'Sarah Chen', meetings: 22, hours: 88, avatar: 'SC' },
    { name: 'Mike Johnson', meetings: 19, hours: 76, avatar: 'MJ' },
    { name: 'Emily Davis', meetings: 18, hours: 72, avatar: 'ED' },
    { name: 'Alex Wilson', meetings: 16, hours: 64, avatar: 'AW' },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Analytics</h1>
          <p className="text-gray-600 mt-1">Track your meeting performance and insights</p>
        </div>
        <div className="flex items-center space-x-2">
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="7d">Last 7 days</option>
            <option value="30d">Last 30 days</option>
            <option value="90d">Last 90 days</option>
            <option value="1y">Last year</option>
          </select>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat, index) => {
          const Icon = stat.icon;
          return (
            <div key={index} className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">{stat.label}</p>
                  <p className="text-2xl font-bold text-gray-900 mt-1">{stat.value}</p>
                  <div className="flex items-center mt-1">
                    <span className={`text-sm font-medium ${
                      stat.trend === 'up' ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {stat.change}
                    </span>
                    <span className="text-sm text-gray-500 ml-1">vs last period</span>
                  </div>
                </div>
                <div className="w-12 h-12 bg-blue-50 rounded-lg flex items-center justify-center">
                  <Icon className="w-6 h-6 text-blue-600" />
                </div>
              </div>
            </div>
          );
        })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Meeting Trends Chart */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold mb-6">Meeting Trends</h2>
          <div className="space-y-4">
            {meetingTrends.map((data, index) => (
              <div key={index} className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <span className="w-12 text-sm font-medium text-gray-600">{data.month}</span>
                  <div className="flex-1">
                    <div className="flex items-center space-x-4">
                      <div className="flex-1 bg-gray-200 rounded-full h-2">
                        <div 
                          className="bg-blue-500 h-2 rounded-full" 
                          style={{ width: `${(data.meetings / 70) * 100}%` }}
                        ></div>
                      </div>
                      <span className="text-sm font-medium text-gray-900 w-16">{data.meetings}</span>
                    </div>
                    <div className="text-xs text-gray-500 mt-1">{data.hours} hours</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Top Participants */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold mb-6">Top Participants</h2>
          <div className="space-y-4">
            {topParticipants.map((participant, index) => (
              <div key={index} className="flex items-center space-x-4">
                <div className="flex items-center space-x-3 flex-1">
                  <div className="w-10 h-10 bg-blue-500 rounded-full flex items-center justify-center text-white font-medium">
                    {participant.avatar}
                  </div>
                  <div>
                    <div className="font-medium text-gray-900">{participant.name}</div>
                    <div className="text-sm text-gray-500">{participant.meetings} meetings</div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="font-medium text-gray-900">{participant.hours}h</div>
                  <div className="text-sm text-gray-500">total time</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Meeting Duration Distribution */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold mb-6">Meeting Duration Distribution</h2>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          {[
            { range: '0-15 min', count: 45, percentage: 18, color: 'bg-green-500' },
            { range: '15-30 min', count: 89, percentage: 36, color: 'bg-blue-500' },
            { range: '30-60 min', count: 76, percentage: 31, color: 'bg-yellow-500' },
            { range: '60+ min', count: 38, percentage: 15, color: 'bg-red-500' },
          ].map((item, index) => (
            <div key={index} className="text-center">
              <div className="mb-4">
                <div className={`w-16 h-16 ${item.color} rounded-full mx-auto flex items-center justify-center text-white font-bold text-xl`}>
                  {item.percentage}%
                </div>
              </div>
              <div className="space-y-1">
                <div className="font-medium text-gray-900">{item.range}</div>
                <div className="text-sm text-gray-500">{item.count} meetings</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};