// Enhanced Paper Card Component - Based on external/synapse_searcher/frontend implementation
import React from 'react';
import { Download, ExternalLink, Calendar, Users, Award, Plus } from 'lucide-react';

const EnhancedPaperCard = ({ paper, onAddToKB }) => {
  // 🎯 Now receiving complete backend data!
  
  // Helper function to convert ArXiv URLs to abstract URL
  const getArxivAbsUrl = (url) => {
    if (!url) return '';
    
    // Extract ArXiv ID from various ArXiv URL formats
    const arxivIdMatch = url.match(/(?:arxiv\.org\/(?:abs\/|pdf\/))([0-9]{4}\.[0-9]{4,5}(?:v[0-9]+)?)/);
    if (arxivIdMatch) {
      return `https://arxiv.org/abs/${arxivIdMatch[1]}`;
    }
    
    // If not ArXiv URL, return original URL
    return url;
  };

  const getArxivPdfUrl = (url) => {
    if (!url) return '';
    
    // Extract ArXiv ID from various ArXiv URL formats
    const arxivIdMatch = url.match(/(?:arxiv\.org\/(?:abs\/|pdf\/))([0-9]{4}\.[0-9]{4,5}(?:v[0-9]+)?)/);
    if (arxivIdMatch) {
      return `https://arxiv.org/pdf/${arxivIdMatch[1]}.pdf`;
    }
    
    // If not ArXiv URL, return original URL
    return url;
  };

  const formatAuthors = (authors) => {
    if (!authors || authors.length === 0) return 'Unknown Authors';
    
    if (authors.length <= 3) {
      return authors.map(author => author.name).join(', ');
    }
    return `${authors.slice(0, 3).map(author => author.name).join(', ')} et al.`;
  };

  const formatDate = () => {
    // Handle both field name variations
    const year = paper.publishYear || paper.publish_year;
    const month = paper.publishMonth || paper.publish_month;
    
    if (!year || year === null) return '';
    if (month && month !== null) {
      const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                         'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
      return `${monthNames[month - 1]} ${year}`;
    }
    return year.toString();
  };

  const getVenueType = () => {
    if (!paper.venue) return 'Preprint';
    
    const venueType = typeof paper.venue === 'string' ? null : paper.venue.type;
    switch (venueType) {
      case 'conference': return 'Conference';
      case 'journal': return 'Journal';
      case 'preprint': return 'Preprint';
      case 'workshop': return 'Workshop';
      default: return 'Preprint';
    }
  };

  const getVenueName = () => {
    if (!paper.venue) return null;
    if (typeof paper.venue === 'string') return paper.venue;
    if (typeof paper.venue === 'object' && paper.venue.name) return paper.venue.name;
    return null;
  };

  const getPaperTypeLabel = (type) => {
    if (!type) return 'Method';
    const typeUpper = type.toString().toUpperCase();
    switch (typeUpper) {
      case 'SURVEY': return 'Survey';
      case 'DEMO': return 'Demo';
      case 'THEORY': return 'Theory';
      case 'SYSTEM': return 'System';
      case 'DATASET': return 'Dataset';
      default: return 'Method';
    }
  };

  const getPaperTypeClass = (type) => {
    if (!type) return 'paper-type-method';
    return `paper-type-${type.toString().toLowerCase()}`;
  };

  // Handle both field name variations
  const citationCount = paper.citationCount || paper.citation_count;
  const relevanceScore = paper.relevanceScore || paper.relevance_score;
  const isCritical = paper.isCritical || paper.is_critical;
  const paperType = paper.paperType || paper.type;
  const paperLink = paper.link;
  

  
  return (
    <div className={`paper-card ${isCritical ? 'critical' : ''}`} style={{
      backgroundColor: 'white',
      borderRadius: '12px',
      padding: '24px',
      boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
      border: '1px solid #e0e0e0',
      transition: 'all 0.2s ease',
      borderLeft: isCritical ? '4px solid #ff9800' : undefined,
      marginBottom: '16px'
    }}
    onMouseEnter={(e) => {
      e.currentTarget.style.boxShadow = '0 4px 16px rgba(0,0,0,0.12)';
      e.currentTarget.style.borderColor = '#1a73e8';
    }}
    onMouseLeave={(e) => {
      e.currentTarget.style.boxShadow = '0 2px 8px rgba(0,0,0,0.08)';
      e.currentTarget.style.borderColor = '#e0e0e0';
    }}
    >
      <div className="paper-header" style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'flex-start',
        marginBottom: '12px',
        gap: '16px'
      }}>
        <h3 
          className="paper-title" 
          onClick={() => paperLink && window.open(getArxivAbsUrl(paperLink), '_blank')}
          style={{ 
            fontSize: '18px',
            fontWeight: '600',
            color: '#1a73e8',
            cursor: paperLink ? 'pointer' : 'default',
            lineHeight: '1.4',
            margin: '0',
            flex: '1'
          }}
          onMouseEnter={(e) => paperLink && (e.target.style.textDecoration = 'underline')}
          onMouseLeave={(e) => paperLink && (e.target.style.textDecoration = 'none')}
        >
          {paper.title}
        </h3>
        <div className="paper-badges" style={{
          display: 'flex',
          gap: '8px',
          flexShrink: '0'
        }}>
          {paperType && getPaperTypeLabel(paperType) !== 'Method' && (
            <span className={`paper-type-badge ${getPaperTypeClass(paperType)}`} style={{
              padding: '4px 8px',
              borderRadius: '12px',
              fontSize: '12px',
              fontWeight: '500',
              textTransform: 'uppercase',
              ...((() => {
                const label = getPaperTypeLabel(paperType);
                switch (label) {
                  case 'Survey': return { background: '#e3f2fd', color: '#1976d2' };
                  case 'Demo': return { background: '#f3e5f5', color: '#7b1fa2' };
                  case 'Theory': return { background: '#e8f5e8', color: '#388e3c' };
                  case 'System': return { background: '#fff3e0', color: '#f57c00' };
                  case 'Dataset': return { background: '#fce4ec', color: '#c2185b' };
                  default: return { background: '#f5f5f5', color: '#616161' };
                }
              })())
            }}>
              {getPaperTypeLabel(paperType)}
            </span>
          )}
          {isCritical && (
            <span className="critical-badge" style={{
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              padding: '4px 8px',
              background: '#fff8e1',
              color: '#ff8f00',
              borderRadius: '12px',
              fontSize: '12px',
              fontWeight: '500'
            }}>
              <Award size={12} />
              Critical
            </span>
          )}
        </div>
      </div>

      <div className="paper-meta" style={{ marginBottom: '12px' }}>
        <div className="meta-row" style={{
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          marginBottom: '4px',
          fontSize: '14px',
          color: '#666'
        }}>
          <Users size={14} />
          <span className="authors" style={{ fontWeight: '500' }}>{formatAuthors(paper.authors)}</span>
        </div>
        
        {paper.venue && (
          <div className="meta-row" style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            marginBottom: '4px',
            fontSize: '14px',
            color: '#666'
          }}>
            <span className="venue-type" style={{ fontWeight: '500' }}>{getVenueType()}</span>
            <span className="venue-separator" style={{ color: '#ccc' }}>|</span>
            <span className="venue-name" style={{ color: '#333' }}>{getVenueName()}</span>
            {formatDate() && (
              <>
                <span className="venue-separator" style={{ color: '#ccc' }}>|</span>
                <Calendar size={14} />
                <span className="publish-date" style={{ color: '#666' }}>{formatDate()}</span>
              </>
            )}
          </div>
        )}
      </div>

      {(paper.summary || paper.abstract) && (
        <div className="paper-summary" style={{ marginBottom: '16px' }}>
          <p style={{ color: '#555', lineHeight: '1.6', margin: '0' }}>{paper.summary || paper.abstract}</p>
        </div>
      )}

      <div className="paper-stats" style={{ marginBottom: '16px' }}>
        <div className="stats-row" style={{ display: 'flex', gap: '20px' }}>
          {(citationCount !== undefined && citationCount !== null) && (
            <div className="stat-item" style={{ display: 'flex', gap: '4px', fontSize: '14px' }}>
              <span className="stat-label" style={{ color: '#666' }}># Citations:</span>
              <span className="stat-value" style={{ fontWeight: '600', color: '#333' }}>{citationCount.toLocaleString()}</span>
            </div>
          )}
          {(relevanceScore !== undefined && relevanceScore !== null) && (
            <div className="stat-item" style={{ display: 'flex', gap: '4px', fontSize: '14px' }}>
              <span className="stat-label" style={{ color: '#666' }}>Relevance:</span>
              <span className="stat-value" style={{ fontWeight: '600', color: '#333' }}>{(relevanceScore * 100).toFixed(1)}%</span>
            </div>
          )}
        </div>
      </div>

      <div className="paper-actions" style={{
        display: 'flex',
        gap: '8px',
        flexWrap: 'wrap'
      }}>
        <button 
          className="action-button primary"
          onClick={() => paperLink && window.open(getArxivPdfUrl(paperLink), '_blank')}
          disabled={!paperLink}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            padding: '8px 12px',
            borderRadius: '6px',
            fontSize: '14px',
            fontWeight: '500',
            cursor: paperLink ? 'pointer' : 'not-allowed',
            transition: 'all 0.2s ease',
            border: '1px solid',
            background: paperLink ? '#1a73e8' : '#f5f5f5',
            color: paperLink ? 'white' : '#999',
            borderColor: paperLink ? '#1a73e8' : '#ddd'
          }}
          onMouseEnter={(e) => {
            if (paperLink) {
              e.target.style.background = '#1557b0';
              e.target.style.borderColor = '#1557b0';
            }
          }}
          onMouseLeave={(e) => {
            if (paperLink) {
              e.target.style.background = '#1a73e8';
              e.target.style.borderColor = '#1a73e8';
            }
          }}
        >
          <Download size={16} />
          Download
        </button>
        
        <button 
          className="action-button tertiary"
          onClick={() => paperLink && window.open(getArxivAbsUrl(paperLink), '_blank')}
          disabled={!paperLink}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            padding: '8px 12px',
            borderRadius: '6px',
            fontSize: '14px',
            fontWeight: '500',
            cursor: paperLink ? 'pointer' : 'not-allowed',
            transition: 'all 0.2s ease',
            border: '1px solid',
            background: 'white',
            color: paperLink ? '#666' : '#999',
            borderColor: paperLink ? '#ddd' : '#ddd'
          }}
          onMouseEnter={(e) => {
            if (paperLink) {
              e.target.style.background = '#f5f5f5';
              e.target.style.borderColor = '#999';
            }
          }}
          onMouseLeave={(e) => {
            if (paperLink) {
              e.target.style.background = 'white';
              e.target.style.borderColor = '#ddd';
            }
          }}
        >
          <ExternalLink size={16} />
          Details
        </button>

        {onAddToKB && (
          <button 
            className="action-button secondary"
            onClick={() => onAddToKB && onAddToKB(paper)}
            disabled={!paperLink}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '8px 12px',
              borderRadius: '6px',
              fontSize: '14px',
              fontWeight: '500',
              cursor: paperLink ? 'pointer' : 'not-allowed',
              transition: 'all 0.2s ease',
              border: '1px solid',
              background: 'white',
              color: paperLink ? '#1a73e8' : '#999',
              borderColor: paperLink ? '#1a73e8' : '#ddd'
            }}
            onMouseEnter={(e) => {
              if (paperLink) {
                e.target.style.background = '#f0f7ff';
              }
            }}
            onMouseLeave={(e) => {
              if (paperLink) {
                e.target.style.background = 'white';
              }
            }}
          >
            <Plus size={16} />
            Add to KB
          </button>
        )}
      </div>
    </div>
  );
};

export default EnhancedPaperCard;