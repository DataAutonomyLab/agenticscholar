
## Part 1: Project Structure
This part provides a high-level overview of the directory and file structure for the **Synapse** project.

---

### 📂 Root Directory

The root directory contains the main configuration files and the primary directories for each component of the application.

-   **`src/`**: The core of the application.
-   **`synapse-client/`**: The frontend application, built using React.
-   **`synapse-server/`**: A separate Node.js server, likely responsible for user authentication and management.
-   **`data/`**: Contains data-related files, most importantly the Docker setup for the Weaviate database.
-   **`external/`**: Contains external code dependencies managed as Git submodules, such as `synapse_searcher`.
-   **`requirements.txt`**: A list of the Python packages required for the backend.
-   **`setup.py`**: A script that makes the `src` directory installable as a Python package.
-   **`.gitmodules`**: Defines the Git submodules used in the project.
-   **`resources`**: Contains other relevant scripts or documents.

---

### 🐍 `src/` - The Python Backend

-   **`server.py`**: The main entry point for web server. This file defines the API endpoints that the frontend will communicate with.
-   **`load_entry.py`**: The main entry point to handle new inserted papers to our system.
-   **`qa_entry.py`**: The main entry point to handle users' queries.
-   **`routing/`**: This module is responsible for interpreting the user's request and creating a plan of action.
    -   `select_plan.py`: Selects a pre-defined plan based on the user's query.
    -   `*.json`: Configuration files that map task names to descriptions and plans.
-   **`executor/`**: Once a plan is created by the `routing` module, the `executor` carries it out.
    -   `executor.py`: The core execution logic that runs the steps in a plan.
    -   `dependency_graph.py`: Manages the dependencies between different tasks in a plan.
-   **`parser/`**: This module is responsible for parsing and understanding input documents.
    -   `parser_minerU/`: A sophisticated parser that can handle complex documents like PDFs, extract text, tables, and figures, and convert them into a structured JSON format. 
-   **`prompts/`**: This directory contains the templates for the prompts that are sent to the Large Language Models (LLMs).
    -   `templates/*.yaml`: A large collection of YAML files, each defining a specific prompt template for tasks like summarization, extraction, and question-answering.
    -   `*.py`: Defines the handlers to answer incoming queries.
-   **`index/`**: Manages the connection to the Weaviate vector database.
    -   `weaviate_instance.py`: Contains the code for initializing and interacting with the Weaviate client.
-   **`paper_search_in_kb/`**: A module dedicated to searching for academic papers within the knowledge base.

---

### ⚛️ `synapse-client/` - The React Frontend

This directory contains all the code for the user interface.

-   **`src/`**: The main source code for the React application.
    -   `App.js`: The root component of the React application.
    -   `components/`: A directory containing reusable React components that make up the UI (e.g., `Sidebar.js`, `InputArea.js`, `ResultArea.js`).
    -   `api/`: Contains functions for making API calls to the backend.
-   **`public/`**: Static assets that are served directly, such as `index.html`, logos, and the `manifest.json` file.
-   **`package.json`**: Lists all the Node.js dependencies required for the frontend, such as React, Tailwind CSS, and other libraries.

---

### 🔐 `synapse-server/` - The Node.js Auth Server

This is a small, dedicated server that handles user authentication. Separating it from the main backend is a common security practice.

-   **`server.js`**: The main file for the Express.js server. It defines the API endpoints for user login, signup, and session management.
-   **`package.json`**: Lists the Node.js dependencies for this server, such as `express`, `jsonwebtoken`, and `cors`.


## Part 2: Set Up Synapse Running Environment

In the following instructions, **`$PROJECT_ROOT`** refers to the root directory of your Synapse project.

---

### Step 1: Pull External Search Project
Initialize and update the submodules under **`$PROJECT_ROOT`** :
```bash
git submodule update --init --recursive
```

If the remote submodule has been updated, run the following command to update
```bash
git submodule update --remote --merge
```

---

### Step 2: Install Python Environment

#### Option A: Using Conda
Create the environment from `environment.yml` under **`$PROJECT_ROOT`** :
```bash
conda env create -f environment.yml
```

To specify a custom environment name:
```bash
conda env create -f environment.yml -n new_env_name
```

Activate the environment:
```bash
conda activate env_name
```

#### Option B: Using uv (Recommended)
**Prerequisites**: Install uv first if you haven't:
```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or using pip (recommended)
pip install uv
```

**Install dependencies**:
```bash
# Navigate to project root
cd $PROJECT_ROOT

# Install all dependencies
uv sync
```

**Activate the environment**:
```bash
# Activate the virtual environment
source .venv/bin/activate

# and run commands directly
uv run python src/server.py
```

**Optional**: If you want to use **MinerU** for paper parsing, go to the **`$PROJECT_ROOT`** `/resources/` directory and run:
```bash
python download_models_hf.py
```
*(This script downloads the required models.)*

---

### Step 3: Install and Start Weaviate
1. Ensure Docker is installed on your system:  
   🔗 [Docker Installation Guide](https://docs.docker.com/engine/install/)

2. Create a `db` directory inside `$PROJECT_ROOT/data`:
   ```bash
   mkdir -p $PROJECT_ROOT/data/db
   ```

3. Copy the `docker-compose.yaml` file from `$PROJECT_ROOT/resources/` to `$PROJECT_ROOT/data/db`:
   ```bash
   cp $PROJECT_ROOT/resources/docker-compose.yaml $PROJECT_ROOT/data/db/
   ```

4. Start the Weaviate server:
   ```bash
   cd $PROJECT_ROOT/data/db
   docker compose up -d

   docker compose down (to stop the server)
   ```

---

### Step 4: Set Up Backend Server
1. Set up LLM information
(1) create a file named `.env` in `$PROJECT_ROOT/src/config/`
(2) write your private API keys in it in the form of
```
OPENAI_API_KEY="your_own_key"
GEMINI_API_KEY="your_own_key"
MISTRALAI_API_KEY="your_own_key"
```

2. Go to root directory of the project:

```bash
pip install -e .
python -m src.server
```

---

### Step 5: Install Node.js and Set Up the Web Interface

1. Install NVM (Node Version Manager) and the latest LTS Node.js:
```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.5/install.sh | bash
nvm install --lts
nvm use --lts
```

2. Start the Synapse server:
```bash
cd $PROJECT_ROOT/src/synapse-server
npm install
npm start
```

3. Start the Synapse client:
```bash
cd $PROJECT_ROOT/src/synapse-client
npm install
npm start
```

