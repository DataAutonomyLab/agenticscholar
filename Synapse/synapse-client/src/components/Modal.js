import React from 'react';
import { X, Loader2, Plus } from 'lucide-react';

function Modal({
    showCreateKbModal,
    setShowCreateKbModal,
    newKbName,
    setNewKbName,
    handleCreateKB,
    loading
}) {
    if (!showCreateKbModal) return null;

    return (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-[100] p-4">
            <div className="p-6 rounded-xl shadow-2xl w-full max-w-md" style={{ backgroundColor: 'var(--bg-secondary)', border: '1px solid var(--border-color)' }}>
                <div className="flex justify-between items-center mb-4">
                    <h2 className="text-xl font-semibold" style={{ color: 'var(--primary-color)' }}>Create New Knowledge Base</h2>
                    <button 
                        onClick={() => setShowCreateKbModal(false)} 
                        className="p-1 rounded-md transition-colors"
                        style={{ color: 'var(--text-tertiary)' }}
                        onMouseOver={(e) => e.target.style.backgroundColor = 'var(--bg-tertiary)'}
                        onMouseOut={(e) => e.target.style.backgroundColor = 'transparent'}
                    >
                        <X className="h-5 w-5"/>
                    </button>
                </div>
                <input
                    type="text"
                    value={newKbName}
                    onChange={(e) => setNewKbName(e.target.value)}
                    placeholder="Enter KB Name (e.g., My Research)"
                    className="w-full px-4 py-3 rounded-lg transition mb-4 focus:outline-none focus:ring-2"
                    style={{
                        backgroundColor: 'var(--bg-tertiary)',
                        border: '1px solid var(--border-color)',
                        color: 'var(--text-primary)'
                    }}
                    onFocus={(e) => {
                        e.target.style.borderColor = 'var(--primary-color)';
                        e.target.style.boxShadow = `0 0 0 2px ${window.getComputedStyle(document.documentElement).getPropertyValue('--primary-color')}33`;
                    }}
                    onBlur={(e) => {
                        e.target.style.borderColor = 'var(--border-color)';
                        e.target.style.boxShadow = 'none';
                    }}
                    autoFocus
                />
                <button
                    onClick={handleCreateKB}
                    disabled={!newKbName.trim() || loading}
                    className="w-full py-3 px-4 rounded-lg font-medium transition"
                    style={{
                        backgroundColor: (!newKbName.trim() || loading) ? 'var(--bg-muted)' : 'var(--primary-color)',
                        color: 'white',
                        opacity: (!newKbName.trim() || loading) ? 0.6 : 1
                    }}
                    onMouseOver={(e) => {
                        if (newKbName.trim() && !loading) {
                            e.target.style.backgroundColor = 'var(--primary-dark)';
                        }
                    }}
                    onMouseOut={(e) => {
                        if (newKbName.trim() && !loading) {
                            e.target.style.backgroundColor = 'var(--primary-color)';
                        }
                    }}
                >
                    {loading ? <Loader2 className="animate-spin h-5 w-5 mx-auto" /> : 'Create KB'}
                </button>
            </div>
        </div>
    );
}

export default Modal;
