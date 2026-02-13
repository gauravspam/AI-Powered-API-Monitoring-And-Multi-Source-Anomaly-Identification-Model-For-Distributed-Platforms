import React, { createContext, useState, useEffect, useContext } from 'react';

// Export Context
export const AuthContext = createContext(null);

// Export Provider
export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState({ name: "Dev User", role: "admin" });
    const [isAuthenticated, setIsAuthenticated] = useState(true);
    const [isLoading, setIsLoading] = useState(false);

    const login = async () => {
        setIsAuthenticated(true);
        return { success: true };
    };

    const logout = async () => {
        setIsAuthenticated(false);
    };

    return (
        <AuthContext.Provider value={{ user, isAuthenticated, isLoading, login, logout }}>
            {children}
        </AuthContext.Provider>
    );
};

// Export Hook
export const useAuth = () => {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};
