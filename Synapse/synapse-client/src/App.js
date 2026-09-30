import React, { useState, useEffect } from 'react';
import LoginPage from './components/LoginPage';
import SignupPage from './components/SignupPage';
import MainAppPage from './components/MainAppPage';

function App() {
    const [currentPage, setCurrentPage] = useState('login');
    const [currentUser, setCurrentUser] = useState(null);
    const [userId, setUserId] = useState(null);

    useEffect(() => {
        const storedUser = localStorage.getItem('synapseUser');
        if (storedUser) {
            try {
                const parsedUser = JSON.parse(storedUser);
                if (parsedUser && parsedUser.id && parsedUser.email) {
                    handleLoginSuccess(parsedUser);
                } else {
                    localStorage.removeItem('synapseUser');
                    setCurrentPage('login');
                }
            } catch (e) {
                console.error("Error parsing stored user:", e);
                localStorage.removeItem('synapseUser');
                setCurrentPage('login');
            }
        } else {
            setCurrentPage('login');
        }
    }, []);

    const handleLoginSuccess = (userData) => {
        setCurrentUser(userData);
        setUserId(userData.id);
        localStorage.setItem('synapseUser', JSON.stringify(userData));
        setCurrentPage('main');
    };

    const handleLogout = () => {
        setCurrentUser(null);
        setUserId(null);
        localStorage.removeItem('synapseUser');
        setCurrentPage('login');
        console.log("User logged out, session cleared.");
    };

    switch (currentPage) {
        case 'login':
            return <LoginPage setCurrentPage={setCurrentPage} onLoginSuccess={handleLoginSuccess} />;
        case 'signup':
            return <SignupPage setCurrentPage={setCurrentPage} onLoginSuccess={handleLoginSuccess} />;
        case 'main':
            return currentUser && userId ? (
                <MainAppPage
                    currentUser={currentUser}
                    userId={userId}
                    onLogout={handleLogout}
                />
            ) : (
                <LoginPage setCurrentPage={setCurrentPage} onLoginSuccess={handleLoginSuccess} />
            );
        default:
            return <LoginPage setCurrentPage={setCurrentPage} onLoginSuccess={handleLoginSuccess} />;
    }
}

export default App;
