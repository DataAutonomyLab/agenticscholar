import React, { useState, useEffect, useRef, useCallback } from 'react';
import { simulateApiCall, generateId } from '../api/mockApi'; 
import Sidebar from './Sidebar';
import Header from './Header';
import ResultArea from './ResultArea';
import InputArea from './InputArea';
import Modal from './Modal';
import EmbeddedProgressPanel from './EmbeddedProgressPanel';
import { X } from 'lucide-react'; 

const NODE_API_URL = 'http://localhost:3001/api'; 
const getToken = () => localStorage.getItem('synapseToken');

const authenticatedFetch = async (url, options = {}) => {
    const token = getToken();
    const headers = { ...options.headers }; 

    if (!(options.body instanceof FormData)) { 
        headers['Content-Type'] = 'application/json';
    }

    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(url, { ...options, headers });
    
    let data;
    const contentType = response.headers.get("content-type");
    if (contentType && contentType.indexOf("application/json") !== -1) {
        data = await response.json();
    } else {
        data = response.status === 204 ? {} : { message: await response.text() };
    }

    if (!response.ok) {
        if (response.status === 401 || response.status === 403) {
            console.error("Authentication error:", data.message || "Unauthorized/Forbidden");
        }
        throw new Error(data.message || `HTTP error! status: ${response.status}`);
    }
    return data;
};

function MainAppPage({ currentUser, userId, onLogout }) {
    const [isSidebarOpen, setIsSidebarOpen] = useState(true);
    const [isKbDropdownOpen, setIsKbDropdownOpen] = useState(false);
    const [knowledgeBases, setKnowledgeBases] = useState([]);
    const [currentKB, setCurrentKB] = useState(null);
    const [chatSessions, setChatSessions] = useState([]);
    const [currentSession, setCurrentSession] = useState(null);
    const [messages, setMessages] = useState([]);
    const [resultAreaView, setResultAreaView] = useState('chat');
    const [papersInView, setPapersInView] = useState([]);
    const [searchTerm, setSearchTerm] = useState('');
    const [chatInput, setChatInput] = useState('');
    const [showCreateKbModal, setShowCreateKbModal] = useState(false);
    const [newKbName, setNewKbName] = useState('');
    const [genericModal, setGenericModal] = useState({ isOpen: false, title: '', message: '', onConfirm: null, showCancel: false });
    const [loading, setLoading] = useState({ kbs: false, sessions: false, messages: false, papers: false, action: false, fileUpload: false });
    const [searchProgress, setSearchProgress] = useState({ isVisible: false, status: 'idle', progressData: null, searchQuery: '', startTime: null });
    const [progressPollInterval, setProgressPollInterval] = useState(null);

    const fileInputRef = useRef(null); 
    const kbDropdownRef = useRef(null);

    const closeGenericModal = useCallback(() => {
        setGenericModal({ isOpen: false, title: '', message: '', onConfirm: null, showCancel: false });
    }, []);

    const showGenericModal = useCallback((title, message, onConfirmCallback, showCancelButton = false) => {
        setGenericModal({ 
            isOpen: true, 
            title, 
            message, 
            onConfirm: () => { 
                if (onConfirmCallback) onConfirmCallback(); 
                closeGenericModal(); 
            }, 
            showCancel: showCancelButton 
        });
    }, [closeGenericModal]);

    const fetchKBsFromApi = useCallback(async () => {
        if (!userId) return;
        setLoading(prev => ({ ...prev, kbs: true }));
        console.log(`FETCH_KBS: Called for userId: ${userId}, Timestamp: ${Date.now()}`);
        try {
            const kbsData = await authenticatedFetch(`${NODE_API_URL}/users/${userId}/kbs`);
            setKnowledgeBases(kbsData);
        } catch (error) {
            console.error("Error fetching KBs from API:", error);
            showGenericModal("Error", `Failed to fetch Knowledge Bases: ${error.message}`);
        } finally {
            setLoading(prev => ({ ...prev, kbs: false }));
        }
    }, [userId, showGenericModal]);

    const fetchSessionsFromApi = useCallback(async () => {
        if (!userId) return; 
        setLoading(prev => ({ ...prev, sessions: true }));
        console.log(`FETCH_SESSIONS: Called for userId: ${userId}, Current KB: ${currentKB?.name}, Timestamp: ${Date.now()}`);
        const sessionUrl = `${NODE_API_URL}/users/${userId}/sessions`;

        const ret_list = await authenticatedFetch(sessionUrl);
        let session_list = []
        for (const ses of ret_list){
            let session = {
                "id": ses["id"],
                "name": ses["name"],
                "kbIdUsed": ses["kb_id_used"],
                "kbNameUsed": ses["kb_name_used"],
                "userId": ses["user_id"],
                "lastMessageAt": ses["last_message_at"]
            }
            session_list.push(session)
        }
        session_list.sort((a,b) => new Date(b.lastMessageAt) - new Date(a.lastMessageAt));

        setChatSessions(session_list); 
        setLoading(prev => ({ ...prev, sessions: false }));
    }, [userId, currentKB, showGenericModal]);

    const fetchMessagesFromApi = useCallback(async (sessionId) => {
        if (!userId || !sessionId) return;
        setLoading(prev => ({ ...prev, messages: true }));
        console.log(`Fetching messages for session: ${sessionId}`);
        const sessionUrl = `${NODE_API_URL}/users/${userId}/${sessionId}/messages`;

        const ret_list = await authenticatedFetch(sessionUrl);
        let message_list = []
        for (const msg of ret_list){
            let message = {
                "id": msg["id"],
                "text": msg["text"],
                "sender": msg["sender"],
                "timestamp": msg["timestamp"]
            }
            message_list.push(message)
        }

        setMessages(message_list);
        setLoading(prev => ({ ...prev, messages: false }));
    }, [userId]);

    useEffect(() => { 
        if (userId) { 
            fetchKBsFromApi(); 
        }
    }, [userId, fetchKBsFromApi]);

    useEffect(() => {
        if (userId) { 
            fetchSessionsFromApi();
        }
    }, [userId, currentKB, fetchSessionsFromApi]); 

    useEffect(() => {
        if (knowledgeBases.length > 0) {
            const currentKBExists = currentKB && knowledgeBases.some(kb => kb.id === currentKB.id);
            if (!currentKBExists) { 
                const defaultKb = knowledgeBases.find(kb => kb.isDefault) || knowledgeBases[0];
                if (defaultKb && (!currentKB || defaultKb.id !== currentKB.id)) { 
                    setCurrentKB(defaultKb);
                }
            }
        } else if (knowledgeBases.length === 0 && currentKB !== null) { 
            setCurrentKB(null); 
        }
    }, [knowledgeBases, currentKB]); 

    useEffect(() => { 
        if (currentSession?.id) { 
            fetchMessagesFromApi(currentSession.id); 
        } else { 
            setMessages([]); 
        }
    }, [currentSession, fetchMessagesFromApi]);

    const handleCreateKB = useCallback(async () => {
        if (!userId || !newKbName.trim()) return;
        setLoading(prev => ({ ...prev, action: true }));
        try {
            const createdKb = await authenticatedFetch(`${NODE_API_URL}/users/${userId}/kbs`, { method: 'POST', body: JSON.stringify({ name: newKbName.trim() }), });
            setKnowledgeBases(prevKbs => [...prevKbs, createdKb]); 
            setNewKbName(''); setShowCreateKbModal(false);
            showGenericModal("KB Created", `Knowledge Base "${createdKb.name}" created successfully.`);
        } catch (error) { console.error("Error creating KB via API:", error); showGenericModal("Error", `Failed to create KB: ${error.message}`);
        } finally { setLoading(prev => ({ ...prev, action: false })); }
    }, [userId, newKbName, showGenericModal]); 
    
    const handleSelectActiveKBForOperations = useCallback((kb) => { setCurrentKB(kb); setIsKbDropdownOpen(false); }, []);
    
    const fetchPapersForKBFromApi = useCallback(async (kbIdToFetch) => {
        if (!userId || !kbIdToFetch) return;
        setLoading(prev => ({ ...prev, papers: true })); setPapersInView([]);
        console.log(`Fetching papers for KB: ${kbIdToFetch}`);

        const papersData = await authenticatedFetch(`${NODE_API_URL}/users/${userId}/kbs/${kbIdToFetch}/papers`);
        let papers_list = [];
        for (const p of papersData){
            let paper = {
                "id": p["id"],
                "title": p["title"],
                "abstract": p["abstract"],
                "source": p["source"],
                "addedAt": p["added_at"]
            }
            papers_list.push(paper)
        }

        setPapersInView(papers_list); setLoading(prev => ({ ...prev, papers: false }));
    }, [userId, currentKB, showGenericModal, knowledgeBases]); // Added knowledgeBases to ensure targetKB is up-to-date

    const handleViewKBPapers = useCallback((kb) => { setCurrentKB(kb); setResultAreaView('kbPapers'); fetchPapersForKBFromApi(kb.id); }, [fetchPapersForKBFromApi]);
    
    const handleDeletePaper = useCallback((kbIdForPaper, paperId, paperTitle) => {
        showGenericModal("Confirm Delete", `Are you sure you want to delete "${paperTitle}"?`, async () => {
            if (!userId || !kbIdForPaper || !paperId) return;
            setLoading(prev => ({ ...prev, action: true }));
            try { 

                await authenticatedFetch(`${NODE_API_URL}/users/${userId}/kbs/${kbIdForPaper}/papers/${paperId}`, { method: 'DELETE' });
                console.log(`Delete for paper ${paperId}`);

                await fetchPapersForKBFromApi(kbIdForPaper);

                showGenericModal("Success", `Paper "${paperTitle}" deleted.`);
            } catch (error) { showGenericModal("Error", `Failed to delete paper: ${error.message}`);
            } finally { setLoading(prev => ({ ...prev, action: false })); }
        }, true);
    }, [userId, showGenericModal, currentKB]);
    
    const handleNewChat = useCallback(async () => {
        if (!userId || !currentKB) { showGenericModal("Action Required", "Please select a KB first."); return; }
        setLoading(prev => ({ ...prev, action: true }));
        try {
            const createdSession = { id: `session_api_${generateId()}`, name: `Virtual API Chat ${chatSessions.length + 1}`, kbIdUsed: currentKB.id, kbNameUsed: currentKB.name, userId: userId, lastMessageAt: new Date().toISOString() };

            setCurrentSession(createdSession); setMessages([]); setResultAreaView('chat');
        } catch (error) { showGenericModal("Error", `Failed to start new chat: ${error.message}`);
        } finally { setLoading(prev => ({ ...prev, action: false })); }
    }, [userId, currentKB, chatSessions.length, showGenericModal]);

    const selectChatSession = useCallback((session) => {
        setCurrentSession(session);
        const kbForSession = knowledgeBases.find(kb => kb.id === session.kbIdUsed);
        setCurrentKB(kbForSession || currentKB); 
        setResultAreaView('chat');
    }, [knowledgeBases, currentKB]);




    const handleSendMessage = useCallback(async () => {
        if (!userId || !currentSession || !chatInput.trim() || !currentKB) return;
        setLoading(prev => ({ ...prev, action: true }));
        const userMessage = { id: generateId(), text: chatInput.trim(), sender: "user", timestamp: new Date().toISOString() };
        setMessages(prev => [...prev, userMessage]); setChatInput('');
        try {
            const targetKbId = currentKB.id
            const sessionId = currentSession.id
            const chatUrl = `${NODE_API_URL}/chat/${sessionId}/users/${userId}/kbs/${targetKbId}`;
            const model_ret = await authenticatedFetch(chatUrl, { method: 'POST', body: JSON.stringify({ message: userMessage.text })});

            // handle first msg
            const ret_session_id = model_ret["chat_session"]["id"]
            const ret_session_name = model_ret["chat_session"]["name"]
            if (sessionId !== ret_session_id){
                currentSession.id = ret_session_id
                currentSession.name = ret_session_name
                setChatSessions(prev => [currentSession, ...prev].sort((a,b) => new Date(b.lastMessageAt) - new Date(a.lastMessageAt)));
            }
            const aiMessage = {
                id: model_ret["answer"]["id"], 
                text: model_ret["answer"]["text"], 
                sender: "ai", 
                timestamp: model_ret["answer"]["timestamp"]
            }

            setMessages(prev => [...prev, aiMessage]);
        } catch (error) { showGenericModal("Error", `Failed to send message: ${error.message}`); setMessages(prev => prev.filter(m => m.id !== userMessage.id)); 
        } finally { setLoading(prev => ({ ...prev, action: false })); }
    }, [userId, currentSession, chatInput, currentKB, showGenericModal]);

    // Poll backend for real progress
    const pollSearchProgress = useCallback(async () => {
        try {
            // Use simple fetch for status check (no auth needed)
            const response = await fetch(`${NODE_API_URL}/search_status`);
            const statusResponse = await response.json();
            const currentStep = statusResponse.current_step;
            
            console.log('📊 Polling progress:', currentStep, statusResponse);
            
            if (currentStep === 'completed') {
                const duration = statusResponse.duration || 0;
                setSearchProgress(prev => ({
                    ...prev,
                    status: 'completed',
                    progressData: { 
                        currentStep,
                        duration,
                        resultsCount: prev.progressData?.resultsCount || 0,
                        steps: statusResponse.steps || prev.progressData?.steps || [],
                        totalSteps: statusResponse.total_steps || prev.progressData?.totalSteps || 5
                    }
                }));
                
                // Stop polling
                if (progressPollInterval) {
                    clearInterval(progressPollInterval);
                    setProgressPollInterval(null);
                }
            } else if (currentStep === 'failed') {
                setSearchProgress(prev => ({
                    ...prev,
                    status: 'failed',
                    progressData: { error: statusResponse.error || 'Search failed' }
                }));
                
                // Stop polling
                if (progressPollInterval) {
                    clearInterval(progressPollInterval);
                    setProgressPollInterval(null);
                }
            } else if (currentStep !== 'idle') {
                setSearchProgress(prev => ({
                    ...prev,
                    status: 'processing',
                    progressData: { 
                        currentStep,
                        steps: statusResponse.steps || [],
                        totalSteps: statusResponse.total_steps || 5
                    }
                }));
            }
        } catch (error) {
            console.error('Error polling search progress:', error);
        }
    }, [progressPollInterval]);

    // Cleanup polling on unmount
    useEffect(() => {
        return () => {
            if (progressPollInterval) {
                clearInterval(progressPollInterval);
            }
        };
    }, [progressPollInterval]);

    const handlePaperSearch = useCallback(async (seedPapers = null) => {
        if (!searchTerm.trim()) return;
        
        setLoading(prev => ({ ...prev, papers: true })); 
        setResultAreaView('paperSearchResults');
        
        // Record start time and start progress tracking
        const startTime = Date.now();
        
        // Get initial step structure
        try {
            const initialResponse = await fetch(`${NODE_API_URL}/search_status`);
            const initialStatus = await initialResponse.json();
            
            setSearchProgress({ 
                isVisible: true, 
                status: 'searching', 
                searchQuery: searchTerm.trim(),
                startTime,
                progressData: { 
                    currentStep: 'Starting...', 
                    steps: initialStatus.steps || [],
                    totalSteps: initialStatus.total_steps || 5
                }
            });
        } catch (error) {
            console.error('Error getting initial status:', error);
            setSearchProgress({ 
                isVisible: true, 
                status: 'searching', 
                searchQuery: searchTerm.trim(),
                startTime,
                progressData: { currentStep: 'Starting...' }
            });
        }

        // Start polling for real backend progress
        const interval = setInterval(pollSearchProgress, 1000); // Poll every 1 second for responsiveness
        setProgressPollInterval(interval);

        try {
            const paperSearchUrl = `${NODE_API_URL}/paper_search`;
            const search_ret = await authenticatedFetch(paperSearchUrl, { 
                method: 'POST', 
                body: JSON.stringify({ message: searchTerm.trim() })
            });
            
            // Search completed - calculate duration
            const endTime = Date.now();
            const duration = ((endTime - startTime) / 1000).toFixed(1);
            
            // Update with final results
            setPapersInView(search_ret);
            setSearchProgress(prev => ({ 
                ...prev, 
                status: 'completed',
                progressData: { 
                    currentStep: 'completed',
                    duration: parseFloat(duration),
                    resultsCount: search_ret?.length || 0
                }
            }));
            
            // Stop polling
            clearInterval(interval);
            setProgressPollInterval(null);
            
        } catch (error) {
            console.error('Paper search failed:', error);
            
            // Calculate duration even for failed searches
            const endTime = Date.now();
            const duration = ((endTime - startTime) / 1000).toFixed(1);
            
            let errorMessage = 'Unknown error occurred';
            if (error.message) {
                errorMessage = error.message;
                // Detect specific error types and provide helpful messages
                if (error.message.includes('cannot schedule new futures after interpreter shutdown')) {
                    errorMessage = 'Backend search engine crashed. This may be due to a complex query or system overload. Please try a simpler query.';
                } else if (error.message.includes('timeout')) {
                    errorMessage = 'Search timed out after 5 minutes. Please try a simpler query.';
                } else if (error.message.includes('500')) {
                    errorMessage = 'Internal server error. The search engine encountered an issue.';
                }
            } else if (error.response?.data?.error) {
                errorMessage = error.response.data.error;
            } else if (error.response?.data?.message) {
                errorMessage = error.response.data.message;
            } else if (error.response?.statusText) {
                errorMessage = `HTTP ${error.response.status}: ${error.response.statusText}`;
            }
            
            setSearchProgress({ 
                isVisible: true, 
                status: 'failed', 
                searchQuery: searchTerm.trim(),
                progressData: { 
                    error: errorMessage,
                    duration: parseFloat(duration)
                }
            });
            
            // Stop polling
            clearInterval(interval);
            setProgressPollInterval(null);
        } finally {
            setLoading(prev => ({ ...prev, papers: false }));
        }
    }, [searchTerm, pollSearchProgress]);

    const handleAddPaperToKB = useCallback(async (paper) => {
        if (!userId || !currentKB) { showGenericModal("Action Required", "Select a KB first."); return; }
        setLoading(prev => ({ ...prev, action: true }));
        try { 
            console.log("Add paper to KB:", paper.title);

            const paperUploadUrl = `${NODE_API_URL}/users/${userId}/kbs/${currentKB.id}/upload_paper`;
            const upload_ret = await authenticatedFetch(paperUploadUrl, { method: 'POST', body: JSON.stringify({ paper: paper })});

            const paper_id = upload_ret["paper_id"]
            const paper_count = upload_ret["paper_count"]

            paper.id = paper_id

            setKnowledgeBases(prevKBs => prevKBs.map(kb => kb.id === currentKB.id ? {...kb, paperCount: paper_count} : kb));
            if (currentKB) {
                setCurrentKB(prev => ({...prev, paperCount: paper_count}));
            }
            showGenericModal("Success", `Paper "${paper.title}" added to KB.`);
        } catch (error) { showGenericModal("Error", `Failed to add paper: ${error.message}`);
        } finally { setLoading(prev => ({ ...prev, action: false })); }
    }, [userId, currentKB, showGenericModal]);
    
    const handleChatFileUploadClick = useCallback(() => {
        console.log("handleChatFileUploadClick in MainAppPage called"); 
        if (fileInputRef.current) {
            console.log("fileInputRef.current (for chat) is:", fileInputRef.current); 
            fileInputRef.current.click();
        } else {
            console.error("fileInputRef.current is null for chat upload!"); 
        }
    }, []); 

    const handleTriggerKBFileUpload = useCallback(() => {
        console.log("handleTriggerKBFileUpload in MainAppPage called for KB:", currentKB?.name);
        if (!currentKB) {
            showGenericModal("Error", "No Knowledge Base selected to upload file to.");
            return;
        }
        if (fileInputRef.current) {
            console.log("fileInputRef.current (for KB) is:", fileInputRef.current);
            fileInputRef.current.click();
        } else {
            console.error("fileInputRef.current is null for KB upload!");
        }
    }, [currentKB, showGenericModal]); 

    const handleFileSelected = useCallback(async (event) => {
        const file = event.target.files[0];
        if (fileInputRef.current) { 
            fileInputRef.current.value = "";
        }
        if (!file) return;

        if (!currentKB || !currentKB.id) {
            showGenericModal("Error", "No Knowledge Base selected. Please select a KB before uploading.");
            return;
        }

        const targetKbId = currentKB.id; // Capture the KB ID at the time of selection

        console.log("File selected:", file.name, "Target KB:", currentKB.name, "ID:", targetKbId);
        setLoading(prev => ({ ...prev, fileUpload: true }));

        const formData = new FormData();
        formData.append('file', file); 
        
        try {
            const uploadUrl = `${NODE_API_URL}/users/${userId}/kbs/${targetKbId}/files/upload`;
            const responseData = await authenticatedFetch(uploadUrl, { method: 'POST', body: formData });
            showGenericModal("Success", responseData.message || `File "${file.name}" uploaded successfully to KB "${currentKB.name}".`);
            
            // Optimistically update paper count for the specific KB
            setKnowledgeBases(prevKBs => 
                prevKBs.map(kb => 
                    kb.id === targetKbId ? { ...kb, paperCount: (kb.paperCount || 0) + 1 } : kb
                )
            );
            if (currentKB && currentKB.id === targetKbId) {
                setCurrentKB(prev => ({ ...prev, paperCount: (prev.paperCount || 0) + 1 }));
            }

            // Refresh paper list if viewing the target KB
            if (resultAreaView === 'kbPapers' && currentKB && currentKB.id === targetKbId) {
                fetchPapersForKBFromApi(targetKbId); 
            } else if (currentSession && resultAreaView === 'chat') {
                const systemMessage = { id: generateId(), text: `File "${file.name}" processed for KB: ${currentKB.name}.`, sender: "system", timestamp: new Date().toISOString() };
                setMessages(prev => [...prev, systemMessage]);
            }

        } catch (error) {
            console.error("Error uploading file:", error);
            showGenericModal("Upload Error", `Failed to upload file "${file.name}": ${error.message}`);
        } finally {
            setLoading(prev => ({ ...prev, fileUpload: false }));
        }
    }, [userId, currentKB, currentSession, resultAreaView, showGenericModal, fetchPapersForKBFromApi]);

    return (
        <div className="flex h-screen app-layout overflow-hidden">
            <Sidebar 
                isSidebarOpen={isSidebarOpen} setIsSidebarOpen={setIsSidebarOpen} currentUser={currentUser} userId={userId} onLogout={onLogout} loading={loading}
                knowledgeBases={knowledgeBases} currentKB={currentKB} handleViewKBPapers={handleViewKBPapers}
                resultAreaView={resultAreaView} chatSessions={chatSessions} currentSession={currentSession}
                selectChatSession={selectChatSession} setResultAreaView={setResultAreaView}
                setSearchTerm={setSearchTerm} setPapersInView={setPapersInView} handleNewChat={handleNewChat}
            />
            
            {/* Progress Panel Column - Only show in paper search view */}
            {resultAreaView === 'paperSearchResults' && searchProgress && searchProgress.status !== 'idle' && (
                <div style={{
                    width: '350px',
                    flexShrink: 0,
                    backgroundColor: 'var(--bg-primary)',
                    borderRight: '1px solid var(--border-color)',
                    display: 'flex',
                    flexDirection: 'column',
                    overflow: 'hidden'
                }}>
                    <EmbeddedProgressPanel
                        searchStatus={searchProgress.status}
                        progressData={searchProgress.progressData}
                        searchQuery={searchProgress.searchQuery}
                    />
                </div>
            )}
            
            <div className="flex-1 flex flex-col overflow-hidden">
                {/* Hide Header on Paper Search page */}
                {resultAreaView !== 'paperSearchResults' && (
                    <Header 
                        isSidebarOpen={isSidebarOpen} setIsSidebarOpen={setIsSidebarOpen}
                        isKbDropdownOpen={isKbDropdownOpen} setIsKbDropdownOpen={setIsKbDropdownOpen}
                        kbDropdownRef={kbDropdownRef} currentKB={currentKB} knowledgeBases={knowledgeBases}
                        loading={loading} handleSelectActiveKBForOperations={handleSelectActiveKBForOperations}
                        setShowCreateKbModal={setShowCreateKbModal}
                        resultAreaView={resultAreaView}
                    />
                )}
                <main className="flex-1 overflow-y-auto p-4 md:p-6" style={{ backgroundColor: 'var(--bg-primary)' }}>
                    <ResultArea 
                        resultAreaView={resultAreaView} loading={loading} messages={messages}
                        currentSession={currentSession} handleNewChat={handleNewChat} currentKB={currentKB}
                        papersInView={papersInView} handleDeletePaper={handleDeletePaper}
                        searchTerm={searchTerm} setSearchTerm={setSearchTerm} handlePaperSearch={handlePaperSearch}
                        handleAddPaperToKB={handleAddPaperToKB}
                        onUploadFileToKBClick={handleTriggerKBFileUpload}
                        isSidebarOpen={isSidebarOpen} setIsSidebarOpen={setIsSidebarOpen}
                        searchProgress={searchProgress} setSearchProgress={setSearchProgress}
                    />
                </main>
                {resultAreaView === 'chat' && currentSession && ( 
                    <InputArea 
                        currentKB={currentKB} chatInput={chatInput} setChatInput={setChatInput}
                        loading={loading.action || loading.fileUpload} 
                        handleSendMessage={handleSendMessage}
                        handleChatFileUploadClick={handleChatFileUploadClick} 
                    />
                )}
            </div>
            <Modal 
                showCreateKbModal={showCreateKbModal} setShowCreateKbModal={setShowCreateKbModal}
                newKbName={newKbName} setNewKbName={setNewKbName}
                handleCreateKB={handleCreateKB} loading={loading.action} 
            />
            {genericModal.isOpen && (
                 <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-[100] p-4">
                    <div className="p-6 rounded-xl shadow-2xl w-full max-w-md" style={{ backgroundColor: 'var(--bg-secondary)', border: '1px solid var(--border-color)' }}>
                        <div className="flex justify-between items-center mb-1">
                            <h2 className="text-xl font-semibold" style={{ color: 'var(--primary-color)' }}>{genericModal.title}</h2>
                             <button 
                                onClick={closeGenericModal} 
                                className="p-1 rounded-md transition-colors"
                                style={{ color: 'var(--text-tertiary)' }}
                                onMouseOver={(e) => e.target.style.backgroundColor = 'var(--bg-tertiary)'}
                                onMouseOut={(e) => e.target.style.backgroundColor = 'transparent'}
                             >
                                <X className="h-5 w-5"/>
                            </button>
                        </div>
                        <p className="my-4" style={{ color: 'var(--text-secondary)' }}>{genericModal.message}</p>
                        <div className="flex justify-end space-x-3 mt-5">
                            {genericModal.showCancel && (
                                <button 
                                    onClick={closeGenericModal} 
                                    className="px-4 py-2 rounded-md transition"
                                    style={{
                                        color: 'var(--text-primary)',
                                        backgroundColor: 'var(--bg-tertiary)'
                                    }}
                                    onMouseOver={(e) => e.target.style.backgroundColor = 'var(--bg-muted)'}
                                    onMouseOut={(e) => e.target.style.backgroundColor = 'var(--bg-tertiary)'}
                                >
                                    Cancel
                                </button>
                            )}
                            <button 
                                onClick={() => { if(genericModal.onConfirm) genericModal.onConfirm(); else closeGenericModal(); }}
                                className="px-4 py-2 rounded-md transition text-white"
                                style={{ backgroundColor: 'var(--primary-color)' }}
                                onMouseOver={(e) => e.target.style.backgroundColor = 'var(--primary-dark)'}
                                onMouseOut={(e) => e.target.style.backgroundColor = 'var(--primary-color)'}
                            >
                                {genericModal.onConfirm ? (genericModal.showCancel ? "Confirm" : "OK") : "OK"}
                            </button>
                        </div>
                    </div>
                </div>
            )}
            <input 
                type="file" 
                ref={fileInputRef} 
                onChange={handleFileSelected} 
                className="hidden" 
                accept=".pdf,.txt,.md,.docx,.pptx,.html"
            />
            
        </div>
    );
}

export default MainAppPage;
