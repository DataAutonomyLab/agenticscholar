import React from 'react';
import AuthForm from './AuthForm';

function SignupPage({ setCurrentPage, onLoginSuccess }) {
    return (
        <AuthForm 
            isLogin={false} 
            setCurrentPage={setCurrentPage} 
            onLoginSuccess={onLoginSuccess} 
        />
    );
}

export default SignupPage;
