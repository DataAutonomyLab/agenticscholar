// Embedded Progress Panel Component with Real Backend Sync and Sub-Steps
import React, { useState, useEffect } from 'react';
import { 
  Loader2, CheckCircle, XCircle, Clock, ChevronDown, ChevronUp, ChevronRight 
} from 'lucide-react';

const EmbeddedProgressPanel = ({ 
  searchStatus = 'idle', 
  progressData = null,
  searchQuery = ''
}) => {
  const [isFullyCollapsed, setIsFullyCollapsed] = useState(false);
  const [collapsedSteps, setCollapsedSteps] = useState(new Set());

  // Auto-collapse completed steps that are not current (but expand all when search is completed)
  useEffect(() => {
    if (progressData?.steps) {
      const newCollapsed = new Set();
      const currentStep = progressData.currentStep;
      
      // If search is completed, expand all steps to show the full history
      if (searchStatus === 'completed') {
        setCollapsedSteps(new Set()); // Expand all steps
      } else {
        // During search, auto-collapse completed steps that are not current
        progressData.steps.forEach((step, index) => {
          if (step.status === 'completed' && step.name !== currentStep) {
            newCollapsed.add(index);
          }
        });
        setCollapsedSteps(newCollapsed);
      }
    }
  }, [progressData?.steps, progressData?.currentStep, searchStatus]);

  // Auto-collapse when search is completed
  useEffect(() => {
    if (searchStatus === 'completed') {
      setTimeout(() => {
        setIsFullyCollapsed(true);
      }, 3000); // Wait 3 seconds before auto-collapsing
    } else {
      // Reset collapse when starting new search
      setIsFullyCollapsed(false);
    }
  }, [searchStatus]);

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

  const getStepIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckCircle size={14} style={{color: '#10b981'}} />;
      case 'processing':
        return <Loader2 className="animate-spin" size={14} style={{color: 'var(--primary-color)'}} />;
      case 'failed':
        return <XCircle size={14} style={{color: '#ef4444'}} />;
      default:
        return <Clock size={14} style={{color: 'var(--text-tertiary)'}} />;
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

  if (searchStatus === 'idle') return null;

  // Show collapsed completion bar
  if (isFullyCollapsed && searchStatus === 'completed') {
    return (
      <div style={{
        backgroundColor: 'var(--bg-secondary)',
        border: '1px solid var(--border-color)',
        borderRadius: 'var(--radius-lg)',
        padding: '12px 16px',
        margin: '16px',
        cursor: 'pointer',
        transition: 'all var(--transition-normal)'
      }}
      onClick={() => setIsFullyCollapsed(false)}
      onMouseOver={(e) => e.currentTarget.style.backgroundColor = 'var(--bg-tertiary)'}
      onMouseOut={(e) => e.currentTarget.style.backgroundColor = 'var(--bg-secondary)'}
      >
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}>
            <CheckCircle size={16} style={{color: '#10b981'}} />
            <span style={{ 
              fontSize: '14px', 
              fontWeight: '500', 
              color: 'var(--text-primary)' 
            }}>
              Synapse completed its research in {progressData?.duration || 0} seconds.
            </span>
          </div>
          <ChevronDown size={16} style={{color: 'var(--text-tertiary)'}} />
        </div>
      </div>
    );
  }

  return (
    <div style={{
      backgroundColor: 'var(--bg-primary)',
      padding: '16px',
      height: '100%',
      overflowY: 'auto'
    }}>
      {/* Header */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: '16px',
        paddingBottom: '12px',
        borderBottom: '1px solid var(--border-color)'
      }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px'
        }}>
          {getStatusIcon()}
          <div style={{
            fontSize: '16px',
            fontWeight: '600',
            color: 'var(--text-primary)'
          }}>
            Search Progress
          </div>
        </div>
        
        {searchStatus === 'completed' && (
          <button
            onClick={() => setIsFullyCollapsed(true)}
            style={{
              background: 'none',
              border: 'none',
              color: 'var(--text-tertiary)',
              cursor: 'pointer',
              padding: '4px',
              borderRadius: 'var(--radius-sm)',
              transition: 'color var(--transition-fast)'
            }}
            onMouseOver={(e) => e.target.style.color = 'var(--text-primary)'}
            onMouseOut={(e) => e.target.style.color = 'var(--text-tertiary)'}
            title="Collapse progress panel"
          >
            <ChevronUp size={16} />
          </button>
        )}
      </div>

      {/* Query Display */}
      {searchQuery && (
        <div style={{
          fontSize: '12px',
          color: 'var(--text-secondary)',
          backgroundColor: 'var(--bg-tertiary)',
          padding: '8px 10px',
          borderRadius: 'var(--radius-sm)',
          marginBottom: '16px',
          fontStyle: 'italic',
          border: '1px solid var(--border-color)'
        }}>
          Query: "{searchQuery}"
        </div>
      )}

      {/* Current Step Display */}
      {progressData?.currentStep && progressData.currentStep !== 'completed' && progressData.currentStep !== 'idle' && (
        <div style={{
          fontSize: '14px',
          color: 'var(--text-primary)',
          marginBottom: '16px',
          padding: '8px',
          backgroundColor: 'var(--primary-color)10',
          borderRadius: 'var(--radius-sm)',
          border: '1px solid var(--primary-color)30'
        }}>
          <strong>Current:</strong> {progressData.currentStep}
        </div>
      )}

      {/* Completion Status Display */}
      {searchStatus === 'completed' && progressData?.duration && (
        <div style={{
          fontSize: '14px',
          color: '#10b981',
          marginBottom: '16px',
          padding: '8px',
          backgroundColor: '#10b98110',
          borderRadius: 'var(--radius-sm)',
          border: '1px solid #10b98130',
          fontWeight: '500'
        }}>
          ✓ Search completed in {progressData.duration} seconds
        </div>
      )}

      {/* Real Backend Steps with Sub-Steps */}
      {progressData?.steps && progressData.steps.length > 0 && (
        <div style={{ marginBottom: '16px' }}>
          {progressData.steps.map((step, index) => {
            const isStepCollapsed = collapsedSteps.has(index);
            const hasSubSteps = step.subSteps && Array.isArray(step.subSteps) && step.subSteps.length > 0;
            const isCurrent = step.name === progressData.currentStep && step.status !== 'completed';
            
            return (
              <div 
                key={index}
                style={{
                  marginBottom: '8px',
                  border: `1px solid ${isCurrent ? 'var(--primary-color)' : 'var(--border-color)'}`,
                  borderRadius: 'var(--radius-md)',
                  backgroundColor: isCurrent ? 'var(--primary-color)10' : 'var(--bg-secondary)',
                  overflow: 'hidden',
                  transition: 'all var(--transition-normal)'
                }}
              >
                <div 
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '10px 12px',
                    cursor: hasSubSteps ? 'pointer' : 'default'
                  }}
                  onClick={() => hasSubSteps && toggleStepCollapse(index)}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    {getStepIcon(step.status)}
                    <div>
                      <div style={{ 
                        fontSize: '14px', 
                        fontWeight: '500', 
                        color: 'var(--text-primary)' 
                      }}>
                        {step.name}
                      </div>
                      <div style={{
                        fontSize: '12px',
                        color: 'var(--text-secondary)',
                        marginTop: '2px'
                      }}>
                        {step.description}
                      </div>
                    </div>
                  </div>
                  {hasSubSteps && (
                    <div>
                      {isStepCollapsed ? <ChevronRight size={16} /> : <ChevronDown size={16} />}
                    </div>
                  )}
                </div>
                
                {/* Sub-steps */}
                {!isStepCollapsed && hasSubSteps && (
                  <div style={{ 
                    padding: '0 12px 12px',
                    backgroundColor: 'var(--bg-tertiary)',
                    borderTop: '1px solid var(--border-color)'
                  }}>
                    {step.subSteps.map((subStep, subIndex) => (
                      <div key={subIndex} style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px',
                        padding: '6px 8px',
                        fontSize: '12px',
                        borderRadius: 'var(--radius-sm)',
                        marginTop: '4px',
                        backgroundColor: subStep.status === 'processing' ? 'var(--primary-color)08' : 'transparent'
                      }}>
                        {getStepIcon(subStep.status)}
                        <span style={{ 
                          color: 'var(--text-secondary)',
                          fontWeight: subStep.status === 'processing' ? '500' : '400'
                        }}>
                          {subStep.name}
                        </span>
                        {subStep.message && (
                          <span style={{ color: 'var(--text-tertiary)', fontStyle: 'italic' }}>
                            - {subStep.message}
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Overall Progress Bar */}
      {(searchStatus === 'searching' || searchStatus === 'processing') && (
        <div style={{ marginBottom: '16px' }}>
          <div style={{
            backgroundColor: 'var(--bg-tertiary)',
            borderRadius: 'var(--radius-full)',
            height: '8px',
            overflow: 'hidden',
            marginBottom: '8px',
            border: '1px solid var(--border-color)'
          }}>
            <div
              style={{
                backgroundColor: 'var(--primary-color)',
                height: '100%',
                width: `${(() => {
                  if (!progressData?.steps) return 10;
                  const completedSteps = progressData.steps.filter(step => step.status === 'completed').length;
                  const totalSteps = progressData.steps.length;
                  return (completedSteps / totalSteps) * 100;
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
              if (!progressData?.steps) return 'Initializing...';
              const completedSteps = progressData.steps.filter(step => step.status === 'completed').length;
              const totalSteps = progressData.steps.length;
              return `Step ${completedSteps + 1} of ${totalSteps}`;
            })()}
          </div>
        </div>
      )}

      {/* Completion Message */}
      {searchStatus === 'completed' && progressData?.duration && (
        <div style={{
          padding: '12px',
          backgroundColor: '#10b98110',
          borderRadius: 'var(--radius-sm)',
          fontSize: '13px',
          color: '#10b981',
          textAlign: 'center',
          border: '1px solid #10b98130'
        }}>
          ✓ Synapse completed its research in {progressData.duration} seconds.
          <br />
          <span style={{ fontSize: '12px', opacity: 0.8 }}>
            Found {progressData?.resultsCount || 0} papers
          </span>
        </div>
      )}

      {/* Error Message */}
      {searchStatus === 'failed' && progressData?.error && (
        <div style={{
          padding: '12px',
          backgroundColor: '#ef444410',
          borderRadius: 'var(--radius-sm)',
          fontSize: '13px',
          color: '#ef4444',
          textAlign: 'center',
          border: '1px solid #ef444430'
        }}>
          ✗ {progressData.error}
          {progressData?.duration && (
            <div style={{ fontSize: '12px', marginTop: '4px', opacity: 0.8 }}>
              Failed after {progressData.duration} seconds
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default EmbeddedProgressPanel;