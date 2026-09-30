// --- Helper Functions ---
export const generateId = () => crypto.randomUUID();

// --- Mock API Call Simulation ---
// Simulates network delay
export const simulateApiCall = (data, delay = 500, shouldSucceed = true) => {
    return new Promise((resolve, reject) => {
        setTimeout(() => {
            if (shouldSucceed) {
                resolve(data);
            } else {
                reject(new Error("Simulated API Error: The operation failed."));
            }
        }, delay);
    });
};
