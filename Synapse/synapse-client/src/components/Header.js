import React from 'react';
import { Menu, X, ChevronDown, Plus, Loader2 } from 'lucide-react';

function Header({
    isSidebarOpen,
    setIsSidebarOpen,
    isKbDropdownOpen,
    setIsKbDropdownOpen,
    kbDropdownRef,
    currentKB,
    knowledgeBases,
    loading,
    handleSelectActiveKBForOperations,
    setShowCreateKbModal,
    resultAreaView
}) {
    return (
        <header className="backdrop-blur-md shadow-md p-3 flex items-center justify-between flex-shrink-0" style={{ backgroundColor: 'var(--bg-secondary)', borderBottom: '1px solid var(--border-color)' }}>
            <div className="flex items-center">
                {/* Show menu button only when sidebar is closed */}
                {!isSidebarOpen && (
                    <button 
                        onClick={() => setIsSidebarOpen(true)} 
                        className="p-2 rounded-md transition-colors mr-4"
                        style={{ 
                            color: 'var(--text-secondary)',
                            ':hover': { backgroundColor: 'var(--bg-tertiary)' }
                        }}
                        onMouseOver={(e) => e.currentTarget.style.backgroundColor = 'var(--bg-tertiary)'}
                        onMouseOut={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                        title="Open sidebar"
                    >
                        <Menu className="h-6 w-6" />
                    </button>
                )}
                {/* Only show KB selector for non-paperSearch pages */}
                {resultAreaView !== 'paperSearchResults' && (
                    <div className="relative ml-4" ref={kbDropdownRef}>
                    <button
                        onClick={() => setIsKbDropdownOpen(!isKbDropdownOpen)}
                        className="flex items-center space-x-2 px-4 py-2 rounded-md transition-colors"
                        style={{
                            backgroundColor: 'var(--bg-tertiary)',
                            color: 'var(--text-primary)'
                        }}
                        onMouseOver={(e) => e.currentTarget.style.backgroundColor = 'var(--bg-secondary)'}
                        onMouseOut={(e) => e.currentTarget.style.backgroundColor = 'var(--bg-tertiary)'}
                    >
                        <span className="font-medium">{currentKB ? currentKB.name : "Select KB"}</span>
                        <ChevronDown className={`h-5 w-5 transition-transform ${isKbDropdownOpen ? 'rotate-180' : ''}`} style={{ color: 'var(--text-tertiary)' }} />
                    </button>
                    {isKbDropdownOpen && (
                        <div 
                            className="absolute top-full left-0 mt-2 w-80 rounded-lg shadow-2xl overflow-hidden kb-dropdown"
                            style={{
                                backgroundColor: 'var(--bg-primary)',
                                border: '1px solid var(--border-color)',
                                zIndex: 10000,
                                boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)'
                            }}
                        >
                            <div className="max-h-60 overflow-y-auto p-2 space-y-1">
                                {loading.kbs ? (
                                    <div className="text-center py-2">
                                        <Loader2 className="animate-spin h-5 w-5 mx-auto" style={{ color: 'var(--primary-color)' }} />
                                    </div>
                                ) :
                                 knowledgeBases.length > 0 ? (
                                    knowledgeBases.map(kb => (
                                        <button
                                            key={kb.id}
                                            onClick={() => handleSelectActiveKBForOperations(kb)}
                                            className="w-full text-left px-3 py-2 rounded-md text-sm transition-colors"
                                            style={{
                                                backgroundColor: currentKB?.id === kb.id ? 'var(--primary-color)' : 'transparent',
                                                color: currentKB?.id === kb.id ? 'white' : 'var(--text-primary)',
                                                fontWeight: currentKB?.id === kb.id ? '600' : '400'
                                            }}
                                            onMouseOver={(e) => {
                                                if (currentKB?.id !== kb.id) {
                                                    e.currentTarget.style.backgroundColor = 'var(--bg-tertiary)';
                                                }
                                            }}
                                            onMouseOut={(e) => {
                                                if (currentKB?.id !== kb.id) {
                                                    e.currentTarget.style.backgroundColor = 'transparent';
                                                }
                                            }}
                                        >
                                            {kb.name} {kb.isDefault && <span className="text-xs opacity-70">(Default)</span>}
                                        </button>
                                    ))
                                ) : (
                                    <p className="text-xs p-2" style={{ color: 'var(--text-muted)' }}>No knowledge bases found.</p>
                                )}
                            </div>
                            <button
                                onClick={() => { setShowCreateKbModal(true); setIsKbDropdownOpen(false); }}
                                className="w-full flex items-center justify-center space-x-2 px-3 py-2.5 text-sm font-medium rounded-md transition-colors"
                                style={{
                                    backgroundColor: 'var(--primary-color)',
                                    color: 'white',
                                    borderTop: '1px solid var(--border-color)'
                                }}
                                onMouseOver={(e) => e.currentTarget.style.backgroundColor = 'var(--primary-dark)'}
                                onMouseOut={(e) => e.currentTarget.style.backgroundColor = 'var(--primary-color)'}
                            >
                                <Plus className="h-4 w-4" />
                                <span>Create New KB</span>
                            </button>
                        </div>
                    )}
                    </div>
                )}
            </div>
        </header>
    );
}

export default Header;
