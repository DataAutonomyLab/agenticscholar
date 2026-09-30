import React from 'react';
import { Brain, Search, Plus, Folder, MessageSquare, UserCircle, LogOut, Loader2 } from 'lucide-react';

function Sidebar({ 
    isSidebarOpen, 
    setIsSidebarOpen,
    currentUser, 
    userId, 
    onLogout, 
    loading,
    knowledgeBases,
    currentKB,
    handleViewKBPapers,
    resultAreaView,
    chatSessions,
    currentSession,
    selectChatSession,
    setResultAreaView,
    setSearchTerm,
    setPapersInView,
    handleNewChat
}) {
    if (!isSidebarOpen) return null;

    return (
        <div className="transition-all duration-300 ease-in-out sidebar-light w-64 flex flex-col h-full">
            {/* Top Section - Scrollable Content */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
                <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                        <Brain className="h-8 w-8" style={{color: 'var(--primary-color)'}} />
                        <h1 className="text-2xl font-semibold">Synapse</h1>
                    </div>
                    {/* Collapse Button */}
                    <button
                        onClick={() => setIsSidebarOpen && setIsSidebarOpen(false)}
                        className="p-2.5 rounded-lg sidebar-collapse-btn group"
                        style={{ 
                            color: 'var(--text-secondary)',
                            backgroundColor: 'var(--bg-tertiary)',
                            border: '1px solid var(--border-color)'
                        }}
                        onMouseOver={(e) => {
                            e.currentTarget.style.backgroundColor = 'var(--primary-color)';
                            e.currentTarget.style.color = 'white';
                            e.currentTarget.style.borderColor = 'var(--primary-color)';
                            e.currentTarget.style.transform = 'translateX(-2px)';
                        }}
                        onMouseOut={(e) => {
                            e.currentTarget.style.backgroundColor = 'var(--bg-tertiary)';
                            e.currentTarget.style.color = 'var(--text-secondary)';
                            e.currentTarget.style.borderColor = 'var(--border-color)';
                            e.currentTarget.style.transform = 'translateX(0)';
                        }}
                        title="Collapse sidebar"
                    >
                        <svg 
                            width="20" 
                            height="20" 
                            viewBox="0 0 24 24" 
                            fill="none" 
                            stroke="currentColor" 
                            strokeWidth="2.5" 
                            strokeLinecap="round" 
                            strokeLinejoin="round"
                            className="transition-all duration-200"
                        >
                            <path d="M11 19l-7-7 7-7"/>
                            <path d="M21 19l-7-7 7-7"/>
                        </svg>
                    </button>
                </div>
            
            <button
                onClick={() => { setResultAreaView('paperSearchResults'); setSearchTerm(''); setPapersInView([]); }}
                className="w-full flex items-center space-x-3 p-3 rounded-lg transition-normal"
            >
                <Search className="h-5 w-5" />
                <span className="text-sm">Paper Search</span>
            </button>
            <button
                onClick={handleNewChat}
                disabled={!currentKB || loading.action}
                className="w-full flex items-center space-x-3 p-3 rounded-lg transition-normal disabled:opacity-50 disabled:cursor-not-allowed"
            >
                <Plus className="h-5 w-5" />
                <span className="text-sm">New Chat</span>
                {loading.action && handleNewChat.name === 'handleNewChat' && <Loader2 className="animate-spin h-4 w-4 ml-auto" />}
            </button>

            <div>
                <h3 className="text-xs font-semibold text-tertiary uppercase tracking-wider mb-2 px-3">Knowledge Bases</h3>
                {loading.kbs ? <Loader2 className="animate-spin h-5 w-5 mx-auto my-2" style={{color: 'var(--primary-color)'}} /> : (
                    knowledgeBases.length === 0 ? <p className="text-xs text-secondary px-3">No KBs yet. Create one!</p> :
                    <ul className="space-y-1">
                        {knowledgeBases.map(kb => ( 
                            <li key={kb.id}>
                                <button
                                    onClick={() => handleViewKBPapers(kb)}
                                    className="w-full flex items-center justify-between p-3 rounded-lg text-sm transition-colors duration-150"
                                    style={{
                                        backgroundColor: currentKB?.id === kb.id && (resultAreaView === 'kbPapers') ? 'var(--primary-color)' : 'transparent',
                                        color: currentKB?.id === kb.id && (resultAreaView === 'kbPapers') ? 'white' : 'var(--text-primary)',
                                        fontWeight: currentKB?.id === kb.id && (resultAreaView === 'kbPapers') ? '500' : '400'
                                    }}
                                    onMouseOver={(e) => {
                                        if (!(currentKB?.id === kb.id && (resultAreaView === 'kbPapers'))) {
                                            e.currentTarget.style.backgroundColor = 'var(--bg-tertiary)';
                                        }
                                    }}
                                    onMouseOut={(e) => {
                                        if (!(currentKB?.id === kb.id && (resultAreaView === 'kbPapers'))) {
                                            e.currentTarget.style.backgroundColor = 'transparent';
                                        }
                                    }}
                                >
                                    <div className="flex items-center space-x-2 truncate">
                                        <Folder 
                                            className="h-4 w-4 flex-shrink-0"
                                            style={{
                                                color: currentKB?.id === kb.id && resultAreaView === 'kbPapers' ? 'white' : 'var(--primary-color)'
                                            }}
                                        />
                                        <span 
                                            className="truncate"
                                            style={{
                                                color: currentKB?.id === kb.id && resultAreaView === 'kbPapers' ? 'white' : 'var(--text-primary)'
                                            }}
                                        >{kb.name}</span>
                                    </div>
                                    <span 
                                        className="text-xs px-1.5 py-0.5 rounded-full"
                                        style={{
                                            backgroundColor: currentKB?.id === kb.id && resultAreaView === 'kbPapers' ? 'rgba(255,255,255,0.2)' : 'var(--bg-tertiary)',
                                            color: currentKB?.id === kb.id && resultAreaView === 'kbPapers' ? 'white' : 'var(--text-tertiary)'
                                        }}
                                    >{kb.paperCount || 0}</span>
                                </button>
                            </li>
                        ))}
                    </ul>
                )}
            </div>

            <div>
                <h3 className="text-xs font-semibold uppercase tracking-wider mb-2 px-3" style={{ color: 'var(--text-tertiary)' }}>Session History</h3>
                 {loading.sessions ? <Loader2 className="animate-spin h-5 w-5 text-sky-400 mx-auto my-2" /> : (
                    chatSessions.length === 0 ? <p className="text-xs px-3" style={{ color: 'var(--text-muted)' }}>No sessions yet.</p> :
                    <ul className="space-y-1">
                        {chatSessions.map(session => ( 
                            <li key={session.id}>
                                <button
                                    onClick={() => selectChatSession(session)}
                                    className="w-full flex items-center space-x-2 p-3 rounded-lg text-sm transition-colors duration-150 truncate"
                                    style={{
                                        backgroundColor: currentSession?.id === session.id && resultAreaView === 'chat' ? 'var(--primary-color)' : 'transparent',
                                        color: currentSession?.id === session.id && resultAreaView === 'chat' ? 'white' : 'var(--text-primary)',
                                        fontWeight: currentSession?.id === session.id && resultAreaView === 'chat' ? '500' : '400'
                                    }}
                                    onMouseOver={(e) => {
                                        if (!(currentSession?.id === session.id && resultAreaView === 'chat')) {
                                            e.currentTarget.style.backgroundColor = 'var(--bg-tertiary)';
                                        }
                                    }}
                                    onMouseOut={(e) => {
                                        if (!(currentSession?.id === session.id && resultAreaView === 'chat')) {
                                            e.currentTarget.style.backgroundColor = 'transparent';
                                        }
                                    }}
                                >
                                    <MessageSquare 
                                        className="h-4 w-4 flex-shrink-0" 
                                        style={{ 
                                            color: currentSession?.id === session.id && resultAreaView === 'chat' ? 'white' : 'var(--primary-color)'
                                        }} 
                                    />
                                    <span 
                                        className="truncate"
                                        style={{
                                            color: currentSession?.id === session.id && resultAreaView === 'chat' ? 'white' : 'var(--text-primary)'
                                        }}
                                    >{session.name} (KB: {session.kbNameUsed || 'N/A'})</span>
                                </button>
                            </li>
                        ))}
                    </ul>
                 )}
            </div>
            
            </div>
            
            {/* Bottom Section - Fixed to bottom */}
            <div className="flex-shrink-0 p-3" style={{ borderTop: '1px solid var(--border-color)' }}>
                 <div className="flex items-center space-x-3 p-2 rounded-lg mb-2">
                    <UserCircle className="h-6 w-6" style={{ color: 'var(--text-tertiary)' }} />
                    <div className="text-sm truncate">
                        <p className="font-medium truncate" style={{ color: 'var(--text-primary)' }}>{currentUser.name || currentUser.email || "User"}</p>
                        <p className="text-xs" style={{ color: 'var(--text-muted)' }} title={userId}>User ID: {userId ? userId.substring(0,12) + '...' : 'N/A'}</p>
                    </div>
                </div>
                <button
                    onClick={onLogout} 
                    disabled={loading.action}
                    className="w-full flex items-center space-x-3 p-2 rounded-lg transition-colors duration-150"
                    style={{
                        color: '#ef4444',
                        backgroundColor: 'transparent'
                    }}
                    onMouseOver={(e) => {
                        if (!loading.action) {
                            e.currentTarget.style.backgroundColor = 'rgba(239, 68, 68, 0.1)';
                            e.currentTarget.style.color = '#dc2626';
                        }
                    }}
                    onMouseOut={(e) => {
                        if (!loading.action) {
                            e.currentTarget.style.backgroundColor = 'transparent';
                            e.currentTarget.style.color = '#ef4444';
                        }
                    }}
                >
                    <LogOut className="h-5 w-5" />
                    <span>Log out</span>
                </button>
            </div>
        </div>
    );
}

export default Sidebar;
