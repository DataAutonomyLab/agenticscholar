// Enhanced Search Bar Component with Seed Paper Support
import React, { useState } from 'react';
import { Search, Plus, Upload, X } from 'lucide-react';

const EnhancedSearchBar = ({ onSearch, isLoading = false, searchTerm, setSearchTerm, isCompact = false }) => {
  const [seedPapers, setSeedPapers] = useState([]);
  const [showSeedInput, setShowSeedInput] = useState(false);
  const [newSeedUrl, setNewSeedUrl] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (searchTerm.trim()) {
      onSearch(searchTerm.trim(), seedPapers.length > 0 ? seedPapers : undefined);
    }
  };

  const addSeedPaper = () => {
    if (newSeedUrl.trim() && !seedPapers.includes(newSeedUrl.trim())) {
      setSeedPapers([...seedPapers, newSeedUrl.trim()]);
      setNewSeedUrl('');
    }
  };

  const removeSeedPaper = (index) => {
    setSeedPapers(seedPapers.filter((_, i) => i !== index));
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      handleSubmit(e);
    }
  };

  const handleFileUpload = (e) => {
    const files = e.target.files;
    if (files) {
      // TODO: Handle file upload to get URLs
      console.log('Files to upload:', Array.from(files));
      // For now, show a placeholder message
      alert('File upload feature will be implemented in the next iteration');
    }
  };

  return (
    <div className={`search-container ${isCompact ? 'compact' : ''}`}>
      <form onSubmit={handleSubmit} className="search-form">
        <div className="search-main-row">
          <div className="search-input-container">
            <Search className="search-icon" size={20} style={{color: 'var(--text-tertiary)'}} />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Describe your research topic..."
              className="search-input"
              disabled={isLoading}
            />
            <button 
              type="submit" 
              className="search-button"
              disabled={isLoading || !searchTerm.trim()}
            >
              {isLoading ? 'Searching...' : 'Search'}
            </button>
          </div>
          
          {/* Inline options for compact mode */}
          <div className="search-options-inline">
            <div className="seed-papers-section" style={{display: 'flex', gap: '8px'}}>
              <button
                type="button"
                onClick={() => setShowSeedInput(!showSeedInput)}
                className="btn-secondary"
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                  padding: '6px 10px',
                  fontSize: '12px',
                  whiteSpace: 'nowrap'
                }}
              >
                <Plus size={14} />
                Seed papers
              </button>
              
              <label className="btn-secondary" style={{
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                padding: '6px 10px',
                fontSize: '12px',
                cursor: 'pointer',
                whiteSpace: 'nowrap'
              }}>
                <Upload size={14} />
                Upload
                <input
                  type="file"
                  multiple
                  accept=".pdf,.doc,.docx"
                  onChange={handleFileUpload}
                  style={{ display: 'none' }}
                />
              </label>
            </div>
          </div>
        </div>
        
        {/* Original options for non-compact mode */}
        <div className="search-options" style={{display: 'flex', gap: '12px', justifyContent: 'flex-start'}}>
          <div className="seed-papers-section" style={{display: 'flex', gap: '12px'}}>
            <button
              type="button"
              onClick={() => setShowSeedInput(!showSeedInput)}
              className="btn-secondary"
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '8px 12px',
                fontSize: '14px'
              }}
            >
              <Plus size={16} />
              Seed paper links
            </button>
            
            <label className="btn-secondary" style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '8px 12px',
              fontSize: '14px',
              cursor: 'pointer'
            }}>
              <Upload size={16} />
              Upload seed papers
              <input
                type="file"
                multiple
                accept=".pdf,.doc,.docx"
                onChange={handleFileUpload}
                style={{ display: 'none' }}
              />
            </label>
          </div>
        </div>
      </form>

      {showSeedInput && (
        <div style={{
          marginTop: '12px',
          padding: '16px',
          backgroundColor: 'var(--bg-tertiary)',
          borderRadius: 'var(--radius-lg)',
          border: '1px solid var(--border-color)'
        }}>
          <div style={{display: 'flex', gap: '8px', marginBottom: '12px'}}>
            <input
              type="url"
              value={newSeedUrl}
              onChange={(e) => setNewSeedUrl(e.target.value)}
              placeholder="Enter paper URL or DOI..."
              className="input-primary"
              style={{flex: 1, padding: '8px 12px', fontSize: '14px'}}
            />
            <button 
              type="button" 
              onClick={addSeedPaper}
              className="btn-primary"
              disabled={!newSeedUrl.trim()}
              style={{padding: '8px 16px', fontSize: '14px'}}
            >
              Add
            </button>
          </div>
          
          {seedPapers.length > 0 && (
            <div style={{display: 'flex', flexDirection: 'column', gap: '8px'}}>
              {seedPapers.map((url, index) => (
                <div key={index} style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '8px 12px',
                  backgroundColor: 'var(--bg-secondary)',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--border-color)'
                }}>
                  <span style={{
                    fontSize: '14px',
                    color: 'var(--text-secondary)',
                    wordBreak: 'break-all'
                  }}>{url}</span>
                  <button 
                    type="button"
                    onClick={() => removeSeedPaper(index)}
                    style={{
                      background: 'none',
                      border: 'none',
                      color: 'var(--text-tertiary)',
                      cursor: 'pointer',
                      padding: '4px',
                      borderRadius: 'var(--radius-sm)',
                      transition: 'color var(--transition-fast)'
                    }}
                    onMouseOver={(e) => e.target.style.color = '#dc2626'}
                    onMouseOut={(e) => e.target.style.color = 'var(--text-tertiary)'}
                  >
                    <X size={16} />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default EnhancedSearchBar;
