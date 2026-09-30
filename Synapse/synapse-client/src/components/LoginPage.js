import React from 'react';
import AuthForm from './AuthForm';

function LoginPage({ setCurrentPage, onLoginSuccess }) {
    return (
        <AuthForm 
            isLogin={true} 
            setCurrentPage={setCurrentPage} 
            onLoginSuccess={onLoginSuccess} 
        />
    );
}

export default LoginPage;
