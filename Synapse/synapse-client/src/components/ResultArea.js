import React, { useRef, useEffect, useState } from 'react';
import { Loader2, MessageSquare, Trash2, UploadCloud, Menu } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { marked } from 'marked';
import DOMPurify from 'dompurify';
import EnhancedSearchBar from './EnhancedSearchBar';
import EnhancedPaperCard from './EnhancedPaperCard';
import CollapsibleFilterPanel from './CollapsibleFilterPanel';

function ResultArea({
    resultAreaView,
    loading,
    messages,
    currentSession,
    handleNewChat,
    currentKB,
    papersInView,
    handleDeletePaper,
    searchTerm,
    setSearchTerm,
    handlePaperSearch,
    handleAddPaperToKB,
    onUploadFileToKBClick, // Changed prop name
    isSidebarOpen,
    setIsSidebarOpen,
    searchProgress,
    setSearchProgress
}) {
    const chatEndRef = useRef(null);
    
    // Enhanced Paper Search State
    const [filteredPapers, setFilteredPapers] = useState([]);
    const [isFilterPanelExpanded, setIsFilterPanelExpanded] = useState(false);
    const [filters, setFilters] = useState({
        yearRange: {},
        citationRange: { min: 0, max: 1000 },
        paperTypes: [],
        venues: [],
        minRelevanceScore: 0.5,
        showCriticalOnly: false
    });
    const [sortOption, setSortOption] = useState({
        field: 'relevance',
        direction: 'desc',
        label: 'Relevance ↓'
    });

    useEffect(() => {
        if (resultAreaView === 'chat' && chatEndRef.current) {
            chatEndRef.current.scrollIntoView({ behavior: 'smooth' });
        }
    }, [messages, resultAreaView]);

    // Apply filters and sorting to papers
    useEffect(() => {
        let filtered = [...papersInView];
        
        // Debug: check data flow
        if (papersInView.length > 0) {
            console.log('Papers received:', papersInView.length);
        }

        // Only apply filters if we have papers to filter
        if (papersInView.length === 0) {
            setFilteredPapers([]);
            return;
        }

        // Apply year range filter - only if user has set specific year constraints
        if (filters.yearRange.min && filters.yearRange.min > 2000) {
            filtered = filtered.filter(paper => {
                const year = paper.publish_year || paper.publishYear;
                return year && year >= filters.yearRange.min;
            });
        }
        if (filters.yearRange.max && filters.yearRange.max < 2025) {
            filtered = filtered.filter(paper => {
                const year = paper.publish_year || paper.publishYear;
                return year && year <= filters.yearRange.max;
            });
        }

        // Apply paper type filter - only if types are selected
        if (filters.paperTypes.length > 0) {
            filtered = filtered.filter(paper => 
                filters.paperTypes.includes(paper.type)
            );
        }

        // Apply citation range filter - only if user changed from defaults
        if (filters.citationRange.min > 0 || filters.citationRange.max < 1000) {
            filtered = filtered.filter(paper => {
                const citationCount = paper.citation_count || paper.citationCount || 0;
                const maxCitations = filters.citationRange.max === 1000 ? Infinity : filters.citationRange.max;
                return citationCount >= filters.citationRange.min && citationCount <= maxCitations;
            });
        }

        // Apply minimum relevance score filter - only if user changed from default
        if (filters.minRelevanceScore > 0.5) {
            filtered = filtered.filter(paper => {
                const relevanceScore = paper.relevance_score || paper.relevanceScore || 0;
                return relevanceScore >= filters.minRelevanceScore;
            });
        }

        // Apply critical papers filter - only if enabled
        if (filters.showCriticalOnly) {
            filtered = filtered.filter(paper => paper.is_critical || paper.isCritical);
        }



        // Apply sorting
        filtered.sort((a, b) => {
            let aValue, bValue;
            
            switch (sortOption.field) {
                case 'relevance':
                    aValue = (a.relevance_score || a.relevanceScore || 0);
                    bValue = (b.relevance_score || b.relevanceScore || 0);
                    break;
                case 'year':
                    aValue = (a.publish_year || a.publishYear || 0);
                    bValue = (b.publish_year || b.publishYear || 0);
                    break;
                case 'citations':
                    aValue = (a.citation_count || a.citationCount || 0);
                    bValue = (b.citation_count || b.citationCount || 0);
                    break;
                case 'title':
                    aValue = a.title.toLowerCase();
                    bValue = b.title.toLowerCase();
                    break;
                default:
                    return 0;
            }

            if (sortOption.direction === 'asc') {
                return aValue > bValue ? 1 : aValue < bValue ? -1 : 0;
            } else {
                return aValue < bValue ? 1 : aValue > bValue ? -1 : 0;
            }
        });

        setFilteredPapers(filtered);
    }, [papersInView, filters, sortOption]);

    // Enhanced Paper Search Handler
    const handleEnhancedPaperSearch = async (query, seedPapers) => {
        if (!query.trim()) return;
        
        try {
            // Update search term for parent component compatibility
            setSearchTerm(query);
            
            // Call the original paper search handler with seed papers
            await handlePaperSearch(seedPapers);

        } catch (error) {
            console.error('Enhanced paper search failed:', error);
        }
    };







const renderChatView = () => (
    <div className="h-full flex flex-col">
        {/* Add a style block to override the default prose table styles */}
        <style>
            {`
                .prose table {
                    border-collapse: collapse;
                }
                .prose th, .prose td {
                    border: 1px solid #64748b; /* slate-500 */
                    padding: 0.5rem 1rem;
                }
            `}
        </style>
        <div style={{ 
            flex: 1, 
            display: 'flex', 
            flexDirection: 'column', 
            gap: '16px', 
            overflowY: 'auto',
            padding: '0 8px 0 0'
        }}>
            {loading.messages ? (
                <div style={{ textAlign: 'center', padding: '40px' }}>
                    <Loader2 className="animate-spin" size={32} style={{ 
                        color: 'var(--primary-color)', 
                        margin: '0 auto' 
                    }} />
                </div>
            ) :
            !currentSession ? (
                <div style={{ 
                    textAlign: 'center', 
                    padding: '40px 20px', 
                    color: 'var(--text-tertiary)'
                }}>
                    <MessageSquare size={64} style={{
                        margin: '0 auto 16px auto',
                        opacity: 0.3,
                        color: 'var(--text-muted)'
                    }}/>
                    <p style={{ fontSize: '18px', marginBottom: '8px' }}>No chat session selected.</p>
                    <p>Start a <button onClick={handleNewChat} disabled={!currentKB} style={{
                        color: !currentKB ? 'var(--text-muted)' : 'var(--primary-color)',
                        background: 'none',
                        border: 'none',
                        textDecoration: 'underline',
                        cursor: !currentKB ? 'not-allowed' : 'pointer',
                        opacity: !currentKB ? 0.5 : 1
                    }}>new chat</button> or select one from history.</p>
                    {!currentKB && <p style={{ 
                        fontSize: '14px', 
                        color: 'var(--warning-color)', 
                        marginTop: '8px' 
                    }}>Please select or create a Knowledge Base first.</p>}
                </div>
            ) : messages.length === 0 ? (
                <div style={{ 
                    textAlign: 'center', 
                    padding: '40px 20px', 
                    color: 'var(--text-tertiary)'
                }}>
                    <p style={{ fontSize: '18px', marginBottom: '8px' }}>This chat is empty.</p>
                    <p>Send a message to start the conversation with KB: <span style={{ 
                        fontWeight: '600', 
                        color: 'var(--primary-color)' 
                    }}>{currentKB?.name || "N/A"}</span>.</p>
                </div>
            ) : (
                messages.map(msg => (
                    <div key={msg.id} className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
                        {/* Updated to use CSS variables instead of Tailwind classes */}
                        <div style={{
                            maxWidth: '85%',
                            padding: '12px 16px',
                            borderRadius: 'var(--radius-lg)',
                            boxShadow: 'var(--shadow-sm)',
                            marginBottom: '8px',
                            backgroundColor: msg.sender === 'user' ? 'var(--primary-color)' : 'var(--bg-secondary)',
                            color: msg.sender === 'user' ? 'white' : 'var(--text-primary)',
                            borderBottomRightRadius: msg.sender === 'user' ? '4px' : 'var(--radius-lg)',
                            borderBottomLeftRadius: msg.sender === 'user' ? 'var(--radius-lg)' : '4px'
                        }}>
                            {/* We are now using ReactMarkdown, which is safer and better integrated with React.
                              - `remarkPlugins={[remarkGfm]}` adds support for tables.
                              - `className="prose ..."` styles the output.
                            */}
                            <div style={{ 
                                fontSize: '14px', 
                                lineHeight: '1.5'
                            }}>
                            <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                {msg.text || ''}
                            </ReactMarkdown>
                            </div>
                            
                            <p style={{
                                fontSize: '12px',
                                marginTop: '8px',
                                opacity: 0.7,
                                textAlign: 'right',
                                color: msg.sender === 'user' ? 'rgba(255,255,255,0.8)' : 'var(--text-tertiary)'
                            }}>
                                {msg.timestamp ? new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Sending...'}
                            </p>
                        </div>
                    </div>
                ))
            )}
            <div ref={chatEndRef} />
        </div>
    </div>
);


    const renderKBPapersView = () => (
        <div className="main-content-area">
            <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: '24px',
                paddingBottom: '16px',
                borderBottom: '1px solid var(--border-color)'
            }}>
                <h2 style={{
                    fontSize: '24px',
                    fontWeight: '600',
                    color: 'var(--text-primary)'
                }}>
                    Papers in: <span style={{ color: 'var(--primary-color)' }}>{currentKB?.name || "Selected KB"}</span>
                </h2>
                {currentKB && ( 
                    <button
                        onClick={onUploadFileToKBClick}
                        className="button-primary"
                        style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '8px',
                            padding: '10px 16px',
                            fontSize: '14px',
                            fontWeight: '500'
                        }}
                        title={`Upload file to ${currentKB.name}`}
                    >
                        <UploadCloud size={16} />
                        <span>Upload File to KB</span>
                    </button>
                )}
            </div>

            {loading.papers ? (
                <div style={{ textAlign: 'center', padding: '40px' }}>
                    <Loader2 className="animate-spin" size={32} style={{ 
                        color: 'var(--primary-color)', 
                        margin: '0 auto' 
                    }} />
                </div>
            ) :
             !currentKB ? (
                <div style={{ 
                    textAlign: 'center', 
                    padding: '40px 20px', 
                    color: 'var(--text-tertiary)' 
                }}>
                    <p>No Knowledge Base selected.</p>
                </div>
             ) :
             papersInView.length === 0 ? (
                <div style={{ 
                    textAlign: 'center', 
                    padding: '40px 20px', 
                    color: 'var(--text-tertiary)' 
                }}>
                    <p>No papers in this Knowledge Base yet.</p>
                    <p style={{ fontSize: '14px', marginTop: '8px' }}>
                        Add some via <span style={{ color: 'var(--primary-color)' }}>Paper Search</span> or upload files.
                    </p>
                </div>
             ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    {papersInView.map(paper => (
                        <div 
                            key={paper.id} 
                            className="card-base"
                            style={{
                                padding: '16px',
                                backgroundColor: 'var(--bg-secondary)',
                                border: '1px solid var(--border-color)',
                                borderRadius: 'var(--radius-lg)',
                                transition: 'all var(--transition-normal)',
                                boxShadow: 'var(--shadow-sm)'
                            }}
                            onMouseOver={(e) => {
                                e.currentTarget.style.boxShadow = 'var(--shadow-lg)';
                                e.currentTarget.style.borderColor = 'var(--primary-border)';
                            }}
                            onMouseOut={(e) => {
                                e.currentTarget.style.boxShadow = 'var(--shadow-sm)';
                                e.currentTarget.style.borderColor = 'var(--border-color)';
                            }}
                        >
                            <div style={{
                                display: 'flex',
                                justifyContent: 'space-between',
                                alignItems: 'flex-start',
                                gap: '16px'
                            }}>
                                <div style={{ flex: 1 }}>
                                    <h3 style={{
                                        fontSize: '16px',
                                        fontWeight: '600',
                                        color: 'var(--primary-color)',
                                        marginBottom: '8px',
                                        lineHeight: '1.4'
                                    }}>
                                        {paper.title}
                                    </h3>
                                    {paper.abstract && (
                                        <p style={{
                                            fontSize: '14px',
                                            color: 'var(--text-secondary)',
                                            marginBottom: '8px',
                                            lineHeight: '1.4',
                                            whiteSpace: 'pre-wrap'
                                        }}>
                                            {paper.abstract}
                                        </p>
                                    )}
                                    <p style={{
                                        fontSize: '12px',
                                        color: 'var(--text-tertiary)'
                                    }}>
                                        Source: {paper.source} | Added: {paper.addedAt ? new Date(paper.addedAt).toLocaleDateString() : 'N/A'}
                                    </p>
                                </div>
                                <button
                                    onClick={() => handleDeletePaper(currentKB.id, paper.id, paper.title)}
                                    disabled={loading.action}
                                    style={{
                                        color: loading.action ? 'var(--text-muted)' : '#ef4444',
                                        background: 'none',
                                        border: 'none',
                                        cursor: loading.action ? 'not-allowed' : 'pointer',
                                        padding: '8px',
                                        borderRadius: 'var(--radius-sm)',
                                        transition: 'all var(--transition-fast)',
                                        opacity: loading.action ? 0.5 : 1
                                    }}
                                    onMouseOver={(e) => {
                                        if (!loading.action) {
                                            e.target.style.backgroundColor = 'rgba(239, 68, 68, 0.1)';
                                        }
                                    }}
                                    onMouseOut={(e) => {
                                        e.target.style.backgroundColor = 'transparent';
                                    }}
                                    title="Delete paper"
                                >
                                    <Trash2 size={20} />
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );

    const renderPaperSearchView = () => (
        <div style={{ position: 'relative', height: '100%', display: 'flex', flexDirection: 'column' }}>
            {/* Sidebar Toggle (only when sidebar is closed) */}
            {!isSidebarOpen && (
                <div style={{ marginBottom: '16px' }}>
                    <button
                        onClick={() => setIsSidebarOpen(true)}
                        className="p-2 rounded-md transition-colors"
                        style={{
                            color: 'var(--text-secondary)',
                            backgroundColor: 'transparent'
                        }}
                        onMouseOver={(e) => e.currentTarget.style.backgroundColor = 'var(--bg-tertiary)'}
                        onMouseOut={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                        title="Open sidebar"
                    >
                        <Menu className="h-6 w-6" />
                    </button>
                </div>
            )}

            {/* Enhanced Search Bar */}
            <div 
                className={`search-bar-container ${filteredPapers.length > 0 || loading.papers ? 'compact' : ''}`}
            >
                <EnhancedSearchBar
                    onSearch={handleEnhancedPaperSearch}
                    isLoading={loading.papers}
                    searchTerm={searchTerm}
                    setSearchTerm={setSearchTerm}
                    isCompact={filteredPapers.length > 0 || loading.papers}
                />
            </div>

            {/* Search Results */}
            <div style={{ flex: 1, overflow: 'auto' }}>
                {/* Results Header */}
                {filteredPapers.length > 0 && (
                    <div style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        marginBottom: '20px'
                    }}>
                        <h2 style={{
                            fontSize: '24px',
                            fontWeight: '600',
                            color: 'var(--text-primary)',
                            margin: 0
                        }}>
                            Search Results ({filteredPapers.length})
                        </h2>
                        
                        {searchTerm && (
                            <div style={{
                                fontSize: '14px',
                                color: 'var(--text-secondary)',
                                fontStyle: 'italic'
                            }}>
                                for "{searchTerm}"
                            </div>
                        )}
                    </div>
                )}

                {/* Loading State */}
                {loading.papers && (
                    <div style={{
                        display: 'flex',
                        justifyContent: 'center',
                        alignItems: 'center',
                        minHeight: '200px'
                    }}>
                        <div style={{ textAlign: 'center' }}>
                            <Loader2 className="animate-spin" size={32} style={{color: 'var(--primary-color)'}} />
                            <p style={{ marginTop: '12px', color: 'var(--text-secondary)' }}>
                                Searching for papers...
                            </p>
                        </div>
                    </div>
                )}

                {/* No Results States */}
                {!loading.papers && filteredPapers.length === 0 && searchTerm && (
                    <div style={{
                        textAlign: 'center',
                        minHeight: '200px',
                        display: 'flex',
                        flexDirection: 'column',
                        justifyContent: 'center',
                        alignItems: 'center'
                    }}>
                        <div style={{ fontSize: '48px', marginBottom: '16px' }}>📄</div>
                        <h3 style={{
                            fontSize: '18px',
                            fontWeight: '600',
                            color: 'var(--text-primary)',
                            marginBottom: '8px'
                        }}>
                            No papers found
                        </h3>
                        <p style={{ color: 'var(--text-secondary)' }}>
                            No papers found for "{searchTerm}". Try different keywords or adjust your filters.
                        </p>
                    </div>
                )}

                {!loading.papers && filteredPapers.length === 0 && !searchTerm && (
                    <div style={{
                        textAlign: 'center',
                        minHeight: '200px',
                        display: 'flex',
                        flexDirection: 'column',
                        justifyContent: 'center',
                        alignItems: 'center'
                    }}>
                        <div style={{ fontSize: '48px', marginBottom: '16px' }}>🔍</div>
                        <h3 style={{
                            fontSize: '18px',
                            fontWeight: '600',
                            color: 'var(--text-primary)',
                            marginBottom: '8px'
                        }}>
                            Start Your Search
                        </h3>
                        <p style={{ color: 'var(--text-secondary)' }}>
                            Enter a search term above to find relevant research papers.
                        </p>
                    </div>
                )}

                {/* Paper Cards */}
                {!loading.papers && filteredPapers.length > 0 && (
                    <div className="animate-fade-in">
                        {filteredPapers.map((paper, index) => (
                            <EnhancedPaperCard
                                key={paper.id || paper.title || index}
                                paper={paper}
                                onAddToKB={handleAddPaperToKB}
                                onViewDetails={(paperId) => {
                                    // TODO: Implement paper details modal
                                    console.log(`View details for paper ${paperId}`);
                                }}
                                currentKB={currentKB}
                                loading={loading.action}
                            />
                        ))}
                    </div>
                )}
            </div>

            {/* Collapsible Filter Panel */}
            <CollapsibleFilterPanel
                isExpanded={isFilterPanelExpanded}
                onToggle={() => setIsFilterPanelExpanded(!isFilterPanelExpanded)}
                filters={filters}
                onFiltersChange={setFilters}
                sortOption={sortOption}
                onSortChange={setSortOption}
                paperCount={filteredPapers.length}
            />
        </div>
    );

    switch (resultAreaView) {
        case 'chat':
            return renderChatView();
        case 'kbPapers':
            return renderKBPapersView();
        case 'paperSearchResults':
            return renderPaperSearchView();
        default:
            return renderChatView();
    }
}

export default ResultArea;
