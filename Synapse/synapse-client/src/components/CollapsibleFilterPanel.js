// Collapsible Filter Panel Component
import React, { useState } from 'react';
import { Sliders, ChevronLeft, Calendar, Award, Hash, Filter, ArrowUp, ArrowDown } from 'lucide-react';
import Slider from 'rc-slider';
import 'rc-slider/assets/index.css';

const CollapsibleFilterPanel = ({ 
  isExpanded = false,
  onToggle,
  filters = {},
  onFiltersChange,
  sortOption = { field: 'relevance', direction: 'desc' },
  onSortChange,
  paperCount = 0
}) => {
  // Slider states for showing current values
  const [isDraggingYear, setIsDraggingYear] = useState(false);
  const [isDraggingCitation, setIsDraggingCitation] = useState(false);
  const [isDraggingRelevance, setIsDraggingRelevance] = useState(false);

  const handleFilterChange = (key, value) => {
    const newFilters = { ...filters, [key]: value };
    onFiltersChange && onFiltersChange(newFilters);
  };

  const handleYearRangeChange = (value) => {
    if (Array.isArray(value)) {
      handleFilterChange('yearRange', {
        min: value[0] === 2000 ? undefined : value[0],
        max: value[1] === 2025 ? undefined : value[1]
      });
    }
  };

  const handleCitationRangeChange = (value) => {
    if (Array.isArray(value)) {
      handleFilterChange('citationRange', {
        min: value[0],
        max: value[1]
      });
    }
  };

  const handleRelevanceScoreChange = (value) => {
    if (typeof value === 'number') {
      handleFilterChange('minRelevanceScore', value);
    }
  };

  const handleSortChange = (field) => {
    const newDirection = (sortOption.field === field && sortOption.direction === 'desc') ? 'asc' : 'desc';
    const newSortOption = {
      field,
      direction: newDirection,
      label: `${field.charAt(0).toUpperCase() + field.slice(1)} ${newDirection === 'desc' ? '↓' : '↑'}`
    };
    onSortChange && onSortChange(newSortOption);
  };

  const resetFilters = () => {
    const defaultFilters = {
      yearRange: {},
      citationRange: { min: 0, max: 1000 },
      paperTypes: [],
      venues: [],
      minRelevanceScore: 0.6,
      showCriticalOnly: false
    };
    onFiltersChange && onFiltersChange(defaultFilters);
  };

  const paperTypes = [
    { value: 'SURVEY', label: 'Survey' },
    { value: 'DEMO', label: 'Demo' },
    { value: 'SYSTEM', label: 'System' },
    { value: 'THEORY', label: 'Theory' },
    { value: 'DATASET', label: 'Dataset' }
    // METHOD removed as it's too common and not useful for filtering
  ];

  const sortOptions = [
    { field: 'relevance', label: 'Relevance' },
    { field: 'year', label: 'Year' },
    { field: 'citations', label: 'Citations' },
    { field: 'title', label: 'Title' }
  ];

  return (
    <div className={`filter-panel-collapsed ${isExpanded ? 'expanded' : ''}`}>
      {/* Tab/Toggle Button */}
      <div className="filter-panel-tab" onClick={onToggle}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '4px',
          whiteSpace: 'nowrap'
        }}>
          <Sliders size={14} />
          <span>Filters</span>
          {isExpanded ? <ChevronLeft size={12} /> : <Filter size={12} />}
        </div>
      </div>

      {/* Panel Content */}
      <div style={{ 
        padding: '0 4px',
        maxHeight: '80vh',
        overflowY: 'auto'
      }}>
        {/* Header */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: '16px',
          paddingBottom: '8px',
          borderBottom: '1px solid var(--border-color)'
        }}>
          <h3 style={{
            fontSize: '16px',
            fontWeight: '600',
            color: 'var(--text-primary)',
            margin: 0
          }}>
            Filter & Sort
          </h3>
          <button
            onClick={resetFilters}
            style={{
              background: 'none',
              border: '1px solid var(--border-color)',
              color: 'var(--text-secondary)',
              fontSize: '12px',
              padding: '4px 8px',
              borderRadius: 'var(--radius-sm)',
              cursor: 'pointer',
              transition: 'all var(--transition-fast)'
            }}
            onMouseOver={(e) => {
              e.target.style.borderColor = 'var(--primary-color)';
              e.target.style.color = 'var(--primary-color)';
            }}
            onMouseOut={(e) => {
              e.target.style.borderColor = 'var(--border-color)';
              e.target.style.color = 'var(--text-secondary)';
            }}
          >
            Reset
          </button>
        </div>

        {/* Results Count */}
        {paperCount > 0 && (
          <div style={{
            fontSize: '14px',
            color: 'var(--text-secondary)',
            marginBottom: '16px',
            textAlign: 'center'
          }}>
            Showing {paperCount} papers
          </div>
        )}

        {/* Sort Section */}
        <div style={{ marginBottom: '24px' }}>
          <h4 style={{
            fontSize: '14px',
            fontWeight: '600',
            color: 'var(--text-primary)',
            marginBottom: '12px',
            display: 'flex',
            alignItems: 'center',
            gap: '6px'
          }}>
            <Hash size={14} />
            Sort By
          </h4>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {sortOptions.map(option => (
              <button
                key={option.field}
                onClick={() => handleSortChange(option.field)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '8px 12px',
                  border: `1px solid ${sortOption.field === option.field ? 'var(--primary-color)' : 'var(--border-color)'}`,
                  backgroundColor: sortOption.field === option.field ? 'var(--primary-light)' : 'transparent',
                  color: sortOption.field === option.field ? 'var(--primary-color)' : 'var(--text-secondary)',
                  borderRadius: 'var(--radius-md)',
                  cursor: 'pointer',
                  fontSize: '13px',
                  transition: 'all var(--transition-fast)'
                }}
                onMouseOver={(e) => {
                  if (sortOption.field !== option.field) {
                    e.target.style.borderColor = 'var(--primary-border)';
                    e.target.style.backgroundColor = 'var(--bg-tertiary)';
                  }
                }}
                onMouseOut={(e) => {
                  if (sortOption.field !== option.field) {
                    e.target.style.borderColor = 'var(--border-color)';
                    e.target.style.backgroundColor = 'transparent';
                  }
                }}
              >
                <span>{option.label}</span>
                {sortOption.field === option.field && (
                  sortOption.direction === 'desc' ? <ArrowDown size={12} /> : <ArrowUp size={12} />
                )}
              </button>
            ))}
          </div>
        </div>

        {/* Year Range Filter */}
        <div style={{ marginBottom: '24px' }}>
          <h4 style={{
            fontSize: '14px',
            fontWeight: '600',
            color: 'var(--text-primary)',
            marginBottom: '12px',
            display: 'flex',
            alignItems: 'center',
            gap: '6px'
          }}>
            <Calendar size={14} />
            Year Range
          </h4>
          
          <div style={{ position: 'relative', padding: '8px 16px' }}>
            {isDraggingYear && (
              <div style={{
                position: 'absolute',
                top: '-25px',
                left: '50%',
                transform: 'translateX(-50%)',
                backgroundColor: 'var(--primary-color)',
                color: 'white',
                padding: '4px 8px',
                borderRadius: 'var(--radius-sm)',
                fontSize: '12px',
                fontWeight: '500',
                zIndex: 1000
              }}>
                {filters.yearRange?.min || 2000} - {filters.yearRange?.max || 2025}
              </div>
            )}
            <div style={{ marginLeft: '8px', marginRight: '8px' }}>
            <Slider
              range
              min={2000}
              max={2025}
              value={[filters.yearRange?.min || 2000, filters.yearRange?.max || 2025]}
              onChange={handleYearRangeChange}
              onBeforeChange={() => setIsDraggingYear(true)}
              onAfterChange={() => setTimeout(() => setIsDraggingYear(false), 1000)}
              styles={{
                track: { backgroundColor: 'var(--primary-color)' },
                handle: {
                  borderColor: 'var(--primary-color)',
                  backgroundColor: 'white'
                },
                rail: { backgroundColor: 'var(--border-color)' }
              }}
              marks={{
                2000: '2000',
                2025: '2025'
              }}
            />
          </div>
        </div>
        </div>

        {/* Citation Range Filter */}
        <div style={{ marginBottom: '24px' }}>
          <h4 style={{
            fontSize: '14px',
            fontWeight: '600',
            color: 'var(--text-primary)',
            marginBottom: '12px',
            display: 'flex',
            alignItems: 'center',
            gap: '6px'
          }}>
            <Award size={14} />
            Citations
          </h4>
          
          <div style={{ position: 'relative', padding: '8px 16px' }}>
            {isDraggingCitation && (
              <div style={{
                position: 'absolute',
                top: '-25px',
                left: '50%',
                transform: 'translateX(-50%)',
                backgroundColor: 'var(--primary-color)',
                color: 'white',
                padding: '4px 8px',
                borderRadius: 'var(--radius-sm)',
                fontSize: '12px',
                fontWeight: '500',
                zIndex: 1000
              }}>
                {filters.citationRange?.min || 0} - {filters.citationRange?.max === 1000 ? '1000+' : filters.citationRange?.max || 1000}
              </div>
            )}
            <div style={{ marginLeft: '8px', marginRight: '8px' }}>
              <Slider
                range
                min={0}
                max={1000}
                value={[filters.citationRange?.min || 0, filters.citationRange?.max || 1000]}
                onChange={handleCitationRangeChange}
                onBeforeChange={() => setIsDraggingCitation(true)}
                onAfterChange={() => setTimeout(() => setIsDraggingCitation(false), 1000)}
                styles={{
                  track: { backgroundColor: 'var(--primary-color)' },
                  handle: {
                    borderColor: 'var(--primary-color)',
                    backgroundColor: 'white'
                  },
                  rail: { backgroundColor: 'var(--border-color)' }
                }}
                marks={{
                  0: '0',
                  1000: '1000+'
                }}
              />
            </div>
          </div>
        </div>

        {/* Paper Types Filter */}
        <div style={{ marginBottom: '24px' }}>
          <h4 style={{
            fontSize: '14px',
            fontWeight: '600',
            color: 'var(--text-primary)',
            marginBottom: '12px',
            display: 'flex',
            alignItems: 'center',
            gap: '6px'
          }}>
            <Filter size={14} />
            Paper Types
          </h4>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {paperTypes.map(type => (
              <label
                key={type.value}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  fontSize: '13px',
                  color: 'var(--text-secondary)',
                  cursor: 'pointer'
                }}
              >
                <input
                  type="checkbox"
                  checked={filters.paperTypes?.includes(type.value) || false}
                  onChange={(e) => {
                    const currentTypes = filters.paperTypes || [];
                    const newTypes = e.target.checked
                      ? [...currentTypes, type.value]
                      : currentTypes.filter(t => t !== type.value);
                    handleFilterChange('paperTypes', newTypes);
                  }}
                  style={{
                    accentColor: 'var(--primary-color)'
                  }}
                />
                <span>{type.label}</span>
              </label>
            ))}
          </div>
        </div>

        {/* Relevance Score Filter */}
        <div style={{ marginBottom: '24px' }}>
          <h4 style={{
            fontSize: '14px',
            fontWeight: '600',
            color: 'var(--text-primary)',
            marginBottom: '12px',
            display: 'flex',
            alignItems: 'center',
            gap: '6px'
          }}>
            <Award size={14} />
            Min Relevance Score
          </h4>
          
          <div style={{ position: 'relative', padding: '8px 16px' }}>
            {isDraggingRelevance && (
              <div style={{
                position: 'absolute',
                top: '-25px',
                left: '50%',
                transform: 'translateX(-50%)',
                backgroundColor: 'var(--primary-color)',
                color: 'white',
                padding: '4px 8px',
                borderRadius: 'var(--radius-sm)',
                fontSize: '12px',
                fontWeight: '500',
                zIndex: 1000
              }}>
                {((filters.minRelevanceScore || 0.5) * 100).toFixed(0)}%
              </div>
            )}
            <div style={{ marginLeft: '8px', marginRight: '8px' }}>
              <Slider
                min={0}
                max={1}
                step={0.1}
                value={filters.minRelevanceScore || 0.5}
                onChange={handleRelevanceScoreChange}
                onBeforeChange={() => setIsDraggingRelevance(true)}
                onAfterChange={() => setTimeout(() => setIsDraggingRelevance(false), 1000)}
                styles={{
                  track: { backgroundColor: 'var(--primary-color)' },
                  handle: {
                    borderColor: 'var(--primary-color)',
                    backgroundColor: 'white'
                  },
                  rail: { backgroundColor: 'var(--border-color)' }
                }}
                marks={{
                  0: '0%',
                  0.5: '50%',
                  1: '100%'
                }}
              />
            </div>
          </div>
        </div>

        {/* Show Critical Papers Only */}
        <div>
          <label style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            fontSize: '13px',
            color: 'var(--text-secondary)',
            cursor: 'pointer'
          }}>
            <input
              type="checkbox"
              checked={filters.showCriticalOnly || false}
              onChange={(e) => handleFilterChange('showCriticalOnly', e.target.checked)}
              style={{
                accentColor: 'var(--primary-color)'
              }}
            />
            <span>Show critical papers only</span>
          </label>
        </div>
      </div>
    </div>
  );
};

export default CollapsibleFilterPanel;
