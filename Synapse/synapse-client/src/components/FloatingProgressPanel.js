// Enhanced Floating Progress Panel Component with Detailed Step Tracking
import React, { useEffect, useState } from 'react';
import { 
  Loader2, CheckCircle, XCircle, Clock, ChevronDown, ChevronUp, ChevronRight, Tag, Circle 
} from 'lucide-react';

const FloatingProgressPanel = ({ 
  isVisible = false, 
  searchStatus = 'idle', 
  progressData = null,
  searchQuery = '',
  onClose
}) => {
  const [shouldRender, setShouldRender] = useState(false);
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [collapsedSteps, setCollapsedSteps] = useState(new Set());

  useEffect(() => {
    if (isVisible) {
      setShouldRender(true);
      setIsCollapsed(false); // Always expand when visible
    } else {
      // Don't auto-hide, just make it collapsible
      if (searchStatus === 'completed' || searchStatus === 'failed') {
        setIsCollapsed(true); // Auto-collapse when completed
      } else {
        const timer = setTimeout(() => setShouldRender(false), 300);
        return () => clearTimeout(timer);
      }
    }
  }, [isVisible, searchStatus]);

  // Auto-collapse completed steps that are not current
  useEffect(() => {
    if (progressData?.steps) {
      const newCollapsed = new Set();
      progressData.steps.forEach((step, index) => {
        // Auto-collapse completed steps that are not current
        if (step.status === 'completed' && index !== progressData.currentStepIndex) {
          newCollapsed.add(index);
        }
      });
      setCollapsedSteps(newCollapsed);
    }
  }, [progressData?.steps, progressData?.currentStepIndex]);

  const getStatusIcon = () => {
    switch (searchStatus) {
      case 'searching':
      case 'processing':
        return <Loader2 className="animate-spin" size={16} style={{color: 'var(--primary-color)'}} />;
      case 'completed':
        return <CheckCircle size={16} style={{color: '#10b981'}} />;
      case 'failed':
        return <XCircle size={16} style={{color: '#ef4444'}} />;
      default:
        return <Clock size={16} style={{color: 'var(--text-tertiary)'}} />;
    }
  };

  const getStatusText = () => {
    if (progressData?.currentStep) {
      return `Current: ${progressData.currentStep}`;
    }
    
    switch (searchStatus) {
      case 'searching':
        return 'Searching papers...';
      case 'processing':
        return 'Processing results...';
      case 'completed':
        return 'Search completed';
      case 'failed':
        return 'Search failed';
      default:
        return 'Ready to search';
    }
  };

  const getStepIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="step-icon completed" size={16} style={{color: '#10b981'}} />;
      case 'processing':
        return <Loader2 className="step-icon processing animate-spin" size={16} style={{color: 'var(--primary-color)'}} />;
      case 'failed':
        return <XCircle className="step-icon failed" size={16} style={{color: '#ef4444'}} />;
      default:
        return <Circle className="step-icon pending" size={16} style={{color: 'var(--text-tertiary)'}} />;
    }
  };

  const getKeywordStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="keyword-icon completed" size={12} style={{color: '#10b981'}} />;
      case 'processing':
        return <Loader2 className="keyword-icon processing animate-spin" size={12} style={{color: 'var(--primary-color)'}} />;
      case 'failed':
        return <XCircle className="keyword-icon failed" size={12} style={{color: '#ef4444'}} />;
      default:
        return <Clock className="keyword-icon pending" size={12} style={{color: 'var(--text-tertiary)'}} />;
    }
  };

  const toggleStepCollapse = (stepIndex) => {
    const newCollapsed = new Set(collapsedSteps);
    if (newCollapsed.has(stepIndex)) {
      newCollapsed.delete(stepIndex);
    } else {
      newCollapsed.add(stepIndex);
    }
    setCollapsedSteps(newCollapsed);
  };

  if (!shouldRender) return null;

  return (
    <div 
      className={`progress-panel-floating ${(isVisible || shouldRender) ? 'visible' : ''}`}
      style={{
        position: 'fixed',
        top: '20px',
        right: '20px',
        width: '400px',
        maxHeight: '80vh',
        overflowY: 'auto',
        backgroundColor: 'var(--bg-secondary)',
        border: '1px solid var(--border-color)',
        borderRadius: 'var(--radius-lg)',
        boxShadow: '0 10px 25px rgba(0,0,0,0.15)',
        padding: '16px',
        zIndex: 1000,
        transition: 'all var(--transition-normal)'
      }}
    >
      {/* Header */}
      <div 
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: isCollapsed ? '0' : '12px',
          cursor: 'pointer',
          padding: '4px'
        }}
        onClick={() => setIsCollapsed(!isCollapsed)}
      >
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          fontSize: '14px',
          fontWeight: '600',
          color: 'var(--text-primary)'
        }}>
          {getStatusIcon()}
          Search Progress
        </div>
        
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          {/* Collapse/Expand button */}
          {isCollapsed ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          
          {/* Close button (only show when completed or failed) */}
          {(searchStatus === 'completed' || searchStatus === 'failed') && onClose && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                onClose();
              }}
              style={{
                background: 'none',
                border: 'none',
                color: 'var(--text-tertiary)',
                cursor: 'pointer',
                padding: '4px',
                borderRadius: 'var(--radius-sm)',
                transition: 'color var(--transition-fast)',
                marginLeft: '4px'
              }}
              onMouseOver={(e) => e.target.style.color = 'var(--text-primary)'}
              onMouseOut={(e) => e.target.style.color = 'var(--text-tertiary)'}
            >
              ×
            </button>
          )}
        </div>
      </div>

      {/* Content - only show when not collapsed */}
      {!isCollapsed && (
        <div>
          {/* Query Display */}
          {searchQuery && (
            <div style={{
              fontSize: '12px',
              color: 'var(--text-secondary)',
              backgroundColor: 'var(--bg-tertiary)',
              padding: '6px 8px',
              borderRadius: 'var(--radius-sm)',
              marginBottom: '12px',
              fontStyle: 'italic'
            }}>
              "{searchQuery}"
            </div>
          )}

          {/* Status */}
          <div style={{
            fontSize: '13px',
            color: 'var(--text-secondary)',
            marginBottom: '12px'
          }}>
            {getStatusText()}
          </div>

          {/* Detailed Progress Steps */}
          {progressData?.steps && (
            <div style={{ marginBottom: '12px' }}>
              {progressData.steps.map((step, index) => {
                const isStepCollapsed = collapsedSteps.has(index);
                const hasSubSteps = step.subSteps && Array.isArray(step.subSteps) && step.subSteps.length > 0;
                const hasKeywordProgress = step.keywordProgress && step.keywordProgress.length > 0;
                const hasBatchInfo = step.batchInfo;
                const isCurrent = index === progressData.currentStepIndex && step.status !== 'completed';
                
                return (
                  <div 
                    key={index}
                    style={{
                      marginBottom: '8px',
                      border: `1px solid ${isCurrent ? 'var(--primary-color)' : 'var(--border-color)'}`,
                      borderRadius: 'var(--radius-md)',
                      backgroundColor: isCurrent ? 'var(--primary-color)10' : 'var(--bg-tertiary)',
                      overflow: 'hidden'
                    }}
                  >
                    <div 
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        padding: '8px 12px',
                        cursor: (hasSubSteps || hasKeywordProgress || hasBatchInfo) ? 'pointer' : 'default'
                      }}
                      onClick={() => (hasSubSteps || hasKeywordProgress || hasBatchInfo) && toggleStepCollapse(index)}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        {getStepIcon(step.status)}
                        <span style={{ fontSize: '13px', fontWeight: '500', color: 'var(--text-primary)' }}>
                          {step.name}
                        </span>
                      </div>
                      {(hasSubSteps || hasKeywordProgress || hasBatchInfo) && (
                        <div>
                          {isStepCollapsed ? <ChevronRight size={16} /> : <ChevronDown size={16} />}
                        </div>
                      )}
                    </div>
                    
                    <div style={{
                      fontSize: '12px',
                      color: 'var(--text-secondary)',
                      paddingLeft: '12px',
                      paddingRight: '12px',
                      paddingBottom: '4px'
                    }}>
                      {step.description}
                    </div>
                    
                    {!isStepCollapsed && (
                      <div style={{ padding: '0 12px 12px' }}>
                        {/* Sub-steps */}
                        {hasSubSteps && (
                          <div style={{ marginTop: '8px' }}>
                            {step.subSteps.map((subStep, subIndex) => (
                              <div key={subIndex} style={{
                                display: 'flex',
                                alignItems: 'center',
                                gap: '6px',
                                padding: '4px 0',
                                fontSize: '12px'
                              }}>
                                {getStepIcon(subStep.status)}
                                <span style={{ color: 'var(--text-secondary)' }}>{subStep.name}</span>
                                {subStep.message && (
                                  <span style={{ color: 'var(--text-tertiary)', fontStyle: 'italic' }}>
                                    - {subStep.message}
                                  </span>
                                )}
                              </div>
                            ))}
                          </div>
                        )}
                        
                        {/* Keyword Progress */}
                        {hasKeywordProgress && (
                          <div style={{ marginTop: '8px' }}>
                            <div style={{
                              display: 'flex',
                              alignItems: 'center',
                              gap: '4px',
                              fontSize: '12px',
                              fontWeight: '500',
                              color: 'var(--text-primary)',
                              marginBottom: '6px'
                            }}>
                              <Tag size={12} />
                              <span>Keywords</span>
                            </div>
                            <div style={{
                              display: 'flex',
                              flexWrap: 'wrap',
                              gap: '4px'
                            }}>
                              {step.keywordProgress.map((keyword, keyIndex) => {
                                const truncateKeyword = (text, maxLength = 25) => {
                                  if (text.length <= maxLength) return text;
                                  const words = text.split(' ');
                                  if (words.length <= 2) return text;
                                  return `${words[0]} ${words[1]}...`;
                                };
                                
                                return (
                                  <div 
                                    key={keyIndex}
                                    title={keyword.keyword}
                                    style={{
                                      display: 'flex',
                                      alignItems: 'center',
                                      gap: '3px',
                                      padding: '2px 6px',
                                      backgroundColor: 'var(--bg-secondary)',
                                      border: '1px solid var(--border-color)',
                                      borderRadius: 'var(--radius-sm)',
                                      fontSize: '11px'
                                    }}
                                  >
                                    {getKeywordStatusIcon(keyword.status)}
                                    <span style={{ color: 'var(--text-secondary)' }}>
                                      {truncateKeyword(keyword.keyword)}
                                    </span>
                                    {keyword.resultsCount !== undefined && (
                                      <span style={{ color: 'var(--text-tertiary)' }}>
                                        ({keyword.resultsCount})
                                      </span>
                                    )}
                                    {keyword.errorMessage && (
                                      <span title={keyword.errorMessage} style={{ color: '#ef4444' }}>⚠️</span>
                                    )}
                                  </div>
                                );
                              })}
                            </div>
                          </div>
                        )}
                        
                        {/* Batch Info */}
                        {hasBatchInfo && (
                          <div style={{ marginTop: '8px' }}>
                            <div style={{
                              backgroundColor: 'var(--bg-secondary)',
                              borderRadius: 'var(--radius-sm)',
                              height: '4px',
                              overflow: 'hidden',
                              marginBottom: '4px'
                            }}>
                              <div
                                style={{
                                  backgroundColor: 'var(--primary-color)',
                                  height: '100%',
                                  width: `${(step.batchInfo.currentBatch / step.batchInfo.totalBatches) * 100}%`,
                                  transition: 'width var(--transition-normal)'
                                }}
                              />
                            </div>
                            <div style={{
                              fontSize: '11px',
                              color: 'var(--text-tertiary)',
                              textAlign: 'center'
                            }}>
                              Batch {step.batchInfo.currentBatch}/{step.batchInfo.totalBatches}
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}

          {/* Overall Progress Bar */}
          {progressData?.steps && (
            <div style={{ marginBottom: '12px' }}>
              <div style={{
                backgroundColor: 'var(--bg-tertiary)',
                borderRadius: 'var(--radius-full)',
                height: '6px',
                overflow: 'hidden',
                marginBottom: '6px'
              }}>
                <div
                  style={{
                    backgroundColor: 'var(--primary-color)',
                    height: '100%',
                    width: `${(() => {
                      const allCompleted = progressData.steps.every(step => step.status === 'completed');
                      if (allCompleted) return 100;
                      return ((progressData.currentStepIndex + 1) / progressData.totalSteps) * 100;
                    })()}%`,
                    borderRadius: 'var(--radius-full)',
                    transition: 'width var(--transition-normal)'
                  }}
                />
              </div>
              <div style={{
                fontSize: '12px',
                color: 'var(--text-secondary)',
                textAlign: 'center'
              }}>
                {(() => {
                  const allCompleted = progressData.steps.every(step => step.status === 'completed');
                  if (allCompleted) return `All ${progressData.totalSteps} steps completed`;
                  return `Step ${progressData.currentStepIndex + 1} of ${progressData.totalSteps}`;
                })()}
              </div>
            </div>
          )}

          {/* Simple Progress Bar (fallback when no detailed steps) */}
          {!progressData?.steps && (searchStatus === 'searching' || searchStatus === 'processing') && (
            <div style={{
              backgroundColor: 'var(--bg-tertiary)',
              borderRadius: 'var(--radius-full)',
              height: '6px',
              overflow: 'hidden',
              marginBottom: '12px'
            }}>
              <div
                className="animate-pulse"
                style={{
                  backgroundColor: 'var(--primary-color)',
                  height: '100%',
                  width: '60%',
                  borderRadius: 'var(--radius-full)',
                  transition: 'width var(--transition-normal)'
                }}
              />
            </div>
          )}

          {/* Results Summary (when completed) */}
          {searchStatus === 'completed' && progressData?.resultsCount !== undefined && (
            <div style={{
              marginTop: '12px',
              padding: '8px',
              backgroundColor: '#10b98110',
              borderRadius: 'var(--radius-sm)',
              fontSize: '12px',
              color: '#10b981'
            }}>
              ✓ Found {progressData.resultsCount} papers
            </div>
          )}

          {/* Error Message (when failed) */}
          {searchStatus === 'failed' && progressData?.error && (
            <div style={{
              marginTop: '12px',
              padding: '8px',
              backgroundColor: '#ef444410',
              borderRadius: 'var(--radius-sm)',
              fontSize: '12px',
              color: '#ef4444'
            }}>
              ✗ {progressData.error}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default FloatingProgressPanel;