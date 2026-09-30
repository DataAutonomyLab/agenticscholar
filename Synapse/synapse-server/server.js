// server.js (Node.js/Express API Gateway)

// --- 1. Import Dependencies ---
const express = require('express');
const cors = require('cors');
const bcrypt = require('bcryptjs'); 
const jwt = require('jsonwebtoken');
const axios = require('axios'); 
const multer = require('multer'); // For handling file uploads
const path = require('path'); // For working with file paths
const fs = require('fs'); // For file system operations
const FormData = require('form-data'); // To send multipart/form-data to Python

// --- Multer Configuration ---
const UPLOADS_DIR = path.join(__dirname, 'uploads_node'); // Renamed to avoid conflict if on same machine
if (!fs.existsSync(UPLOADS_DIR)){
    fs.mkdirSync(UPLOADS_DIR, { recursive: true });
}

const storage = multer.diskStorage({
    destination: function (req, file, cb) {
        cb(null, UPLOADS_DIR); 
    },
    filename: function (req, file, cb) {
        cb(null, Date.now() + '-' + file.originalname.replace(/\s/g, '_')); // Sanitize filename a bit
    }
});
const upload = multer({ storage: storage });


// --- 2. Initialize Express App ---
const app = express();
const NODE_PORT = process.env.NODE_PORT || 3001;
const PYTHON_API_URL = process.env.PYTHON_API_URL || 'http://localhost:5002/api/internal';

const JWT_SECRET = 'your-very-secure-and-long-secret-key-nodejs'; 

// --- 3. Middleware ---
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// --- 4. API Routes ---

// POST /api/auth/signup 
app.post('/api/auth/signup', async (req, res) => {
    const { email, password, name } = req.body;
    if (!email || !password || !name) {
        return res.status(400).json({ message: 'Email, password, and name are required.' });
    }
    try {
        const pythonResponse = await axios.post(`${PYTHON_API_URL}/users/create`, { email, password, name });
        const { user: createdUser, message: pythonMessage } = pythonResponse.data;
        if (!createdUser || !createdUser.id) {
            return res.status(pythonResponse.status || 500).json({ message: pythonMessage || 'User creation failed in Python service.' });
        }
        const token = jwt.sign({ userId: createdUser.id, email: createdUser.email }, JWT_SECRET, { expiresIn: '36h' });
        res.status(201).json({ message: pythonMessage || 'User created successfully', user: { id: createdUser.id, email: createdUser.email, name: createdUser.name }, token });
    } catch (error) {
        console.error('Node.js Signup error (calling Python service):'); 
        if (error.response) {
            console.error('Data:', error.response.data); console.error('Status:', error.response.status);
            const status = error.response.status;
            const message = (error.response.data && error.response.data.message) ? error.response.data.message : 'Error response from Python service.';
            res.status(status).json({ message });
        } else if (error.request) {
            console.error('No response received from Python service:', error.code);
            res.status(500).json({ message: `No response from Python service. Is it running at ${PYTHON_API_URL}? Details: ${error.code}` });
        } else {
            console.error('Error setting up request to Python service:', error.message);
            res.status(500).json({ message: `Error setting up request to Python: ${error.message}` });
        }
    }
});

// POST /api/auth/login 
app.post('/api/auth/login', async (req, res) => {
    const { email, password } = req.body;
    if (!email || !password) {
        return res.status(400).json({ message: 'Email and password are required.' });
    }
    try {
        const pythonResponse = await axios.post(`${PYTHON_API_URL}/users/validate_login`, { email, password });
        const { user, message: pythonMessage } = pythonResponse.data;
        if (!user || !user.id) {
            return res.status(pythonResponse.status || 401).json({ message: pythonMessage || 'Invalid credentials (Python service).' });
        }
        const token = jwt.sign({ userId: user.id, email: user.email }, JWT_SECRET, { expiresIn: '36h' });
        res.status(200).json({ message: 'Login successful', user: { id: user.id, email: user.email, name: user.name }, token });
    } catch (error) {
        console.error('Node.js Login error (calling Python service):');
        if (error.response) {
            console.error('Data:', error.response.data); console.error('Status:', error.response.status);
            const status = error.response.status;
            const message = (error.response.data && error.response.data.message) ? error.response.data.message : 'Error response from Python service.';
            res.status(status).json({ message });
        } else if (error.request) {
            console.error('No response received from Python service:', error.code);
            res.status(500).json({ message: `No response from Python service. Is it running at ${PYTHON_API_URL}? Details: ${error.code}` });
        } else {
            console.error('Error setting up request to Python service:', error.message);
            res.status(500).json({ message: `Error setting up request to Python: ${error.message}` });
        }
    }
});

const authenticateToken = (req, res, next) => {
    const authHeader = req.headers['authorization'];
    const token = authHeader && authHeader.split(' ')[1];
    if (token == null) return res.sendStatus(401);
    // jwt.verify(token, JWT_SECRET, (err, userPayload) => {
    //     if (err) { console.error('JWT verification error:', err.message); return res.sendStatus(403); }
    //     req.user = userPayload; 
    //     next();
    // });
    try {
        // 👇 decode without verifying signature or expiration
        const userPayload = jwt.decode(token); 
        if (!userPayload) return res.status(400).json({ message: "Failed to decode token." });

        req.user = userPayload;
        next();
    } catch (err) {
        console.error("Token decode error:", err.message);
        return res.status(400).json({ message: "Token decoding failed." });
    }
};

// GET /api/users/:userId/:sessionId/messages
app.get('/api/users/:userId/:sessionId/messages', authenticateToken, async (req, res) => {
    const requestedUserId = req.params.userId;
    const requestedSessionId = req.params.sessionId;
    if (req.user.userId !== requestedUserId) {
        return res.status(403).json({ message: 'Forbidden: You can only access your own session chat.' });
    }
    try {
        const pythonResponse = await axios.get(`${PYTHON_API_URL}/users/${requestedUserId}/${requestedSessionId}/messages`);
        res.status(pythonResponse.status).json(pythonResponse.data);
    } catch (error) {
        console.error(`Node.js Error fetching sessions for user ${requestedUserId}:`);
        if (error.response) {
            res.status(error.response.status).json(error.response.data || {message: 'Error from Python service.'});
        } else if (error.request) {
            res.status(500).json({ message: `No response from Python service for sessions. Details: ${error.code}` });
        } else {
            res.status(500).json({ message: `Error setting up request for sessions: ${error.message}` });
        }
    }
});

// GET /api/users/:userId/session 
app.get('/api/users/:userId/sessions', authenticateToken, async (req, res) => {
    const requestedUserId = req.params.userId;
    if (req.user.userId !== requestedUserId) {
        return res.status(403).json({ message: 'Forbidden: You can only access your own session chat.' });
    }
    try {
        const pythonResponse = await axios.get(`${PYTHON_API_URL}/users/${requestedUserId}/sessions`);
        res.status(pythonResponse.status).json(pythonResponse.data);
    } catch (error) {
        console.error(`Node.js Error fetching sessions for user ${requestedUserId}:`);
        if (error.response) {
            res.status(error.response.status).json(error.response.data || {message: 'Error from Python service.'});
        } else if (error.request) {
            res.status(500).json({ message: `No response from Python service for sessions. Details: ${error.code}` });
        } else {
            res.status(500).json({ message: `Error setting up request for sessions: ${error.message}` });
        }
    }
});

// GET /api/users/:userId/kbs 
app.get('/api/users/:userId/kbs', authenticateToken, async (req, res) => {
    const requestedUserId = req.params.userId;
    if (req.user.userId !== requestedUserId) {
        return res.status(403).json({ message: 'Forbidden: You can only access your own knowledge bases.' });
    }
    try {
        const pythonResponse = await axios.get(`${PYTHON_API_URL}/users/${requestedUserId}/kbs`);
        res.status(pythonResponse.status).json(pythonResponse.data);
    } catch (error) {
        console.error(`Node.js Error fetching KBs for user f ${requestedUserId}: ${error}`);
        //         for (const e of error.errors) {
        // if (e instanceof Error) {
        //     console.error("→", e.message);
        // } else {
        //     console.error("→", JSON.stringify(e));
        // }
        // }
        if (error.response) {
            res.status(error.response.status).json(error.response.data || {message: 'Error from Python service.'});
        } else if (error.request) {
            res.status(500).json({ message: `No response from Python service for KBs. Details: ${error.code}` });
        } else {
            res.status(500).json({ message: `Error setting up request for KBs: ${error.message}` });
        }
    }
});

// GET /api/users/:userId/kbs/:kbs_id/papers
app.get('/api/users/:userId/kbs/:kbsId/papers', authenticateToken, async (req, res) => {
    const requestedUserId = req.params.userId;
    const requestedKbsId = req.params.kbsId;
    if (req.user.userId !== requestedUserId) {
        return res.status(403).json({ message: 'Forbidden: You can only access your own knowledge bases.' });
    }
    try {
        const pythonResponse = await axios.get(`${PYTHON_API_URL}/users/${requestedUserId}/kbs/${requestedKbsId}/papers`);
        res.status(pythonResponse.status).json(pythonResponse.data);
    } catch (error) {
        console.error(`Node.js Error fetching KBs papers for user ${requestedUserId}:`);
        if (error.response) {
            res.status(error.response.status).json(error.response.data || {message: 'Error from Python service.'});
        } else if (error.request) {
            res.status(500).json({ message: `No response from Python service for KBs papers. Details: ${error.code}` });
        } else {
            res.status(500).json({ message: `Error setting up request for KBs papers: ${error.message}` });
        }
    }
});
app.delete('/api/users/:userId/kbs/:kbsId/papers/:paperId', authenticateToken, async (req, res) => {
    const requestedUserId = req.params.userId;
    const requestedKbsId = req.params.kbsId;
    const requestedPaperId = req.params.paperId;
    if (req.user.userId !== requestedUserId) {
        return res.status(403).json({ message: 'Forbidden: You can only access your own knowledge bases.' });
    }
    try {
        const pythonResponse = await axios.delete(`${PYTHON_API_URL}/users/${requestedUserId}/kbs/${requestedKbsId}/papers/${requestedPaperId}`);
        res.status(pythonResponse.status).json(pythonResponse.data);
    } catch (error) {
        console.error(`Node.js Error deleting KBs papers for user ${requestedUserId}:`);
        if (error.response) {
            res.status(error.response.status).json(error.response.data || {message: 'Error from Python service.'});
        } else if (error.request) {
            res.status(500).json({ message: `No response from Python service for deleting KBs papers. Details: ${error.code}` });
        } else {
            res.status(500).json({ message: `Error setting up request for deleting KBs papers: ${error.message}` });
        }
    }
});

// POST /api/users/:userId/kbs 
app.post('/api/users/:userId/kbs', authenticateToken, async (req, res) => {
    const requestedUserId = req.params.userId;
    const { name } = req.body; 
    if (req.user.userId !== requestedUserId) {
        return res.status(403).json({ message: 'Forbidden' });
    }
    if (!name) {
        return res.status(400).json({ message: 'Knowledge base name is required.' });
    }
    try {
        const pythonResponse = await axios.post(`${PYTHON_API_URL}/users/${requestedUserId}/kbs`, { name });
        res.status(pythonResponse.status).json(pythonResponse.data);
    } catch (error) {
        console.error(`Node.js Error creating KB for user ${requestedUserId}:`);
        if (error.response) {
            res.status(error.response.status).json(error.response.data || {message: 'Error from Python service.'});
        } else if (error.request) {
            res.status(500).json({ message: `No response from Python service for creating KB. Details: ${error.code}` });
        } else {
            res.status(500).json({ message: `Error setting up request for creating KB: ${error.message}` });
        }
    }
});


// --- File Upload Route ---
// POST /api/users/:userId/kbs/:kbId/files/upload
app.post('/api/users/:userId/kbs/:kbId/files/upload', authenticateToken, upload.single('file'), async (req, res) => {
    const requestedUserId = req.params.userId;
    const kbId = req.params.kbId;

    if (req.user.userId !== requestedUserId) {
        if (req.file) fs.unlinkSync(req.file.path); // Delete temp file
        return res.status(403).json({ message: 'Forbidden: You can only upload files to your own knowledge bases.' });
    }

    if (!req.file) {
        return res.status(400).json({ message: 'No file uploaded.' });
    }

    console.log(`File received by Node.js for user ${requestedUserId}, KB ${kbId}. Path: ${req.file.path}`);
    
    const tempFilePath = req.file.path;

    try {
        const formData = new FormData();
        formData.append('file', fs.createReadStream(tempFilePath), req.file.originalname);
        // If Python needs kbId or userId in form-data, append them:
        // formData.append('kb_id', kbId); 
        // formData.append('user_id', requestedUserId);

        console.log(`Node.js: Forwarding file ${req.file.originalname} to Python service for KB ${kbId}...`);
        
        const pythonUploadUrl = `${PYTHON_API_URL}/users/${requestedUserId}/kbs/${kbId}/upload_file_for_processing`;
        const pythonResponse = await axios.post(pythonUploadUrl, formData, {
            headers: {
                ...formData.getHeaders(), // Important for axios to set correct multipart boundary
            },
            maxContentLength: Infinity, // Handle large files if necessary
            maxBodyLength: Infinity
        });

        fs.unlinkSync(tempFilePath); // Delete temporary file from Node.js server after successful forward

        console.log('Python service response for file upload:', pythonResponse.data);
        res.status(pythonResponse.status).json(pythonResponse.data);

    } catch (error) {
        console.error(`Node.js Error forwarding file to Python for KB ${kbId}:`);
        fs.unlinkSync(tempFilePath); // Ensure cleanup even on error

        if (error.response) { 
            console.error('Python Service Error Data:', error.response.data);
            console.error('Python Service Error Status:', error.response.status);
            res.status(error.response.status).json(error.response.data || {message: 'Error from Python service during file processing.'});
        } else if (error.request) { 
            console.error('No response from Python service for file processing:', error.code);
            res.status(500).json({ message: `No response from Python for file processing. Details: ${error.code}` });
        } else { 
            console.error('Error setting up file forward request to Python:', error.message);
            res.status(500).json({ message: `Error setting up file forward: ${error.message}` });
        }
    }
});


app.post('/api/chat/:sessionId/users/:userId/kbs/:targetKbId', authenticateToken, async (req, res) => {
    const requestedUserId = req.params.userId;
    const requestedSessionID = req.params.sessionId;
    const targetKbId = req.params.targetKbId;

    if (req.user.userId !== requestedUserId) {
        return res.status(403).json({ message: 'Forbidden: You can only access your own knowledge bases.' });
    }

    try {
        const { message } = req.body;
        const pythonResponse = await axios.post(`${PYTHON_API_URL}/${requestedSessionID}/users/${requestedUserId}/kbs/${targetKbId}/chat`, { msg: message }, { headers: { 'Content-Type': 'application/json' }});
        res.status(pythonResponse.status).json(pythonResponse.data);
    } catch (error) {
        console.error(error);
        if (error.response) {
            res.status(error.response.status).json(error.response.data || {message: 'Error from Python service.'});
        } else if (error.request) {
            res.status(500).json({ message: `No response from Python service for KBs. Details: ${error.code}` });
        } else {
            res.status(500).json({ message: `Error setting up request for KBs: ${error.message}` });
        }
    }

});

// --- Paper Search Routes ---
app.post('/api/paper_search/', async (req, res) => {
    try {
        const { message } = req.body;
        const pythonResponse = await axios.post(`${PYTHON_API_URL}/paper_search`, { msg: message }, { headers: { 'Content-Type': 'application/json' }});
        res.status(pythonResponse.status).json(pythonResponse.data);
    } catch (error) {
        console.error(error);
        if (error.response) {
            res.status(error.response.status).json(error.response.data || {message: 'Error from Python service.'});
        } else if (error.request) {
            res.status(500).json({ message: `No response from Python service for paper search. Details: ${error.code}` });
        } else {
            res.status(500).json({ message: `Error setting up request for paper search: ${error.message}` });
        }
    }
});

// Get real-time search progress (no auth needed for status check)
app.get('/api/search_status', async (req, res) => {
    try {
        const pythonResponse = await axios.get(`${PYTHON_API_URL}/search_status`);
        res.json(pythonResponse.data);
    } catch (error) {
        console.error('Error fetching search status:', error);
        res.status(500).json({ current_step: "idle", error: "Failed to get status" });
    }
});

app.post('/api/users/:userId/kbs/:kbId/upload_paper', authenticateToken, async (req, res) => {
    const requestedUserId = req.params.userId;
    const kbId = req.params.kbId;
    const { paper } = req.body;

    if (req.user.userId !== requestedUserId) {
        return res.status(403).json({ message: 'Forbidden: You can only upload paper to your own knowledge bases.' });
    }

    try {
        console.log(`Node.js: Forwarding paper ${paper["title"]} to Python service for KB ${kbId}...`);
        
        const pythonUploadPaperUrl = `${PYTHON_API_URL}/users/${requestedUserId}/kbs/${kbId}/upload_paper`;
        const pythonResponse = await axios.post(pythonUploadPaperUrl, { paper: paper }, { headers: { 'Content-Type': 'application/json' }});

        // console.log('Python service response for file upload:', pythonResponse.data);
        res.status(pythonResponse.status).json(pythonResponse.data);

    } catch (error) {
        console.error(`Node.js Error forwarding paper to Python for upload_paper ${kbId}:`);

        if (error.response) { 
            console.error('Python Service Error Data:', error.response.data);
            console.error('Python Service Error Status:', error.response.status);
            res.status(error.response.status).json(error.response.data || {message: 'Error from Python service during paper processing.'});
        } else if (error.request) { 
            console.error('No response from Python service for paper processing:', error.code);
            res.status(500).json({ message: `No response from Python for paper processing. Details: ${error.code}` });
        } else { 
            console.error('Error setting up paper forward request to Python:', error.message);
            res.status(500).json({ message: `Error setting up paper forward: ${error.message}` });
        }
    }
});
app.listen(NODE_PORT, () => {
    console.log(`Node.js API Gateway server running on http://localhost:${NODE_PORT}`);
});