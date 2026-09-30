import React from 'react';
import { UploadCloud, Send, Loader2 } from 'lucide-react';

function InputArea({
    currentKB,
    chatInput,
    setChatInput,
    loading, 
    handleSendMessage,
    fileInputRef,
    handleFileSelected
}) {
    const handleFileUploadClick = () => {
        // Changed from: fileInputRef.current?.click();
        // to an explicit if check to satisfy the linter rule and for clarity.
        if (fileInputRef.current) {
            fileInputRef.current.click();
        }
    };

    return (
        <footer className="p-3 md:p-4 flex-shrink-0" style={{ backgroundColor: 'var(--bg-secondary)', borderTop: '1px solid var(--border-color)' }}>
            <div className="flex items-center space-x-2">
                <button
                    onClick={handleFileUploadClick}
                    className="p-3 rounded-full transition-colors"
                    style={{
                        color: !currentKB ? 'var(--text-muted)' : 'var(--text-tertiary)'
                    }}
                    onMouseOver={(e) => {
                        if (currentKB) {
                            e.currentTarget.style.color = 'var(--primary-color)';
                            e.currentTarget.style.backgroundColor = 'var(--bg-tertiary)';
                        }
                    }}
                    onMouseOut={(e) => {
                        if (currentKB) {
                            e.currentTarget.style.color = 'var(--text-tertiary)';
                            e.currentTarget.style.backgroundColor = 'transparent';
                        }
                    }}
                    title="Upload file"
                    disabled={!currentKB}
                >
                    <UploadCloud className="h-5 w-5" />
                </button>
                <input
                    type="file"
                    ref={fileInputRef}
                    onChange={handleFileSelected}
                    className="hidden"
                    accept=".pdf,.txt,.md,.docx,.pptx,.html"
                />
                <input
                    type="text"
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && !loading && handleSendMessage()}
                    placeholder={currentKB ? `Ask anything (KB: ${currentKB.name})...` : "Select a KB to start chatting..."}
                    className="flex-grow px-4 py-3 rounded-lg transition focus:outline-none focus:ring-2"
                    style={{
                        backgroundColor: 'var(--bg-tertiary)',
                        border: '1px solid var(--border-color)',
                        color: 'var(--text-primary)',
                        '--placeholder-color': 'var(--text-muted)'
                    }}
                    onFocus={(e) => {
                        e.target.style.borderColor = 'var(--primary-color)';
                        e.target.style.boxShadow = `0 0 0 2px ${window.getComputedStyle(document.documentElement).getPropertyValue('--primary-color')}33`;
                    }}
                    onBlur={(e) => {
                        e.target.style.borderColor = 'var(--border-color)';
                        e.target.style.boxShadow = 'none';
                    }}
                    disabled={!currentKB || loading}
                />
                <button
                    onClick={handleSendMessage}
                    disabled={!chatInput.trim() || !currentKB || loading}
                    className="p-3 rounded-lg font-medium transition"
                    style={{
                        backgroundColor: (!chatInput.trim() || !currentKB || loading) ? 'var(--bg-muted)' : 'var(--primary-color)',
                        color: 'white',
                        opacity: (!chatInput.trim() || !currentKB || loading) ? 0.6 : 1
                    }}
                    onMouseOver={(e) => {
                        if (chatInput.trim() && currentKB && !loading) {
                            e.currentTarget.style.backgroundColor = 'var(--primary-dark)';
                        }
                    }}
                    onMouseOut={(e) => {
                        if (chatInput.trim() && currentKB && !loading) {
                            e.currentTarget.style.backgroundColor = 'var(--primary-color)';
                        }
                    }}
                >
                    {loading ? <Loader2 className="animate-spin h-5 w-5" /> : <Send className="h-5 w-5" />}
                </button>
            </div>
        </footer>
    );
}

export default InputArea;