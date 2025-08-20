import React, { useState } from 'react';
import { Homepage } from './pages/Homepage';
import { LoginModal } from './components/LoginModal';
import { Dashboard } from './pages/Dashboard';
import { Meetings } from './pages/Meetings';
import { Analytics } from './pages/Analytics';
import { Settings } from './pages/Settings';
import { Profile } from './pages/Profile';
import { MeetingDetail } from './pages/MeetingDetail';
import { Sidebar } from './components/Sidebar';
import { Header } from './components/Header';

export type Page = 'homepage' | 'dashboard' | 'meetings' | 'analytics' | 'settings' | 'profile' | 'meeting-detail';

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [currentPage, setCurrentPage] = useState<Page>('homepage');
  const [selectedMeetingId, setSelectedMeetingId] = useState<string | null>(null);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  const handleLogin = (email: string, password: string) => {
    // Dummy login - accept any email/password
    if (email && password) {
      setIsLoggedIn(true);
      setShowLoginModal(false);
      setCurrentPage('dashboard');
      return true;
    }
    return false;
  };

  const handleLogout = () => {
    setIsLoggedIn(false);
    setCurrentPage('homepage');
  };

  const renderPage = () => {
    if (!isLoggedIn) {
      return <Homepage onLogin={() => setShowLoginModal(true)} />;
    }

    switch (currentPage) {
      case 'dashboard':
        return <Dashboard onNavigate={setCurrentPage} onMeetingSelect={setSelectedMeetingId} />;
      case 'meetings':
        return <Meetings onNavigate={setCurrentPage} onMeetingSelect={setSelectedMeetingId} />;
      case 'analytics':
        return <Analytics />;
      case 'settings':
        return <Settings />;
      case 'profile':
        return <Profile />;
      case 'meeting-detail':
        return <MeetingDetail meetingId={selectedMeetingId} onBack={() => setCurrentPage('meetings')} />;
      default:
        return <Dashboard onNavigate={setCurrentPage} onMeetingSelect={setSelectedMeetingId} />;
    }
  };

  if (!isLoggedIn) {
    return (
      <>
        <Homepage onLogin={() => setShowLoginModal(true)} />
        {showLoginModal && (
          <LoginModal 
            onClose={() => setShowLoginModal(false)}
            onLogin={handleLogin}
          />
        )}
      </>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 flex">
      <Sidebar 
        currentPage={currentPage} 
        onNavigate={setCurrentPage}
        collapsed={sidebarCollapsed}
        onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
        onLogout={handleLogout}
      />
      <div className={`flex-1 flex flex-col transition-all duration-300 ${sidebarCollapsed ? 'ml-16' : 'ml-64'}`}>
        <Header onToggleSidebar={() => setSidebarCollapsed(!sidebarCollapsed)} />
        <main className="flex-1 p-6">
          {renderPage()}
        </main>
      </div>
    </div>
  );
}

export default App;