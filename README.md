# E-commerce Support Agent Grader

This project is a complete, interactive web application for the comparative evaluation of AI-powered e-commerce support agents. It allows users to enter any customer query, dynamically generates a realistic test case, and evaluates two different agent personas ("Concise" vs. "Empathetic") using the actual `judgeval` library.

The application sends real traces and evaluation data to your Judgment Labs portal, providing a tangible demonstration of how to rigorously test, monitor, and improve agent systems before deployment.

## ✨ Features

* **Interactive Web UI:** A clean, easy-to-use frontend built with HTML and Tailwind CSS.
* **Dynamic Test Case Generation:** Enter any customer query, and the application's AI will generate a plausible "Company Policy" (retrieval context) and a "Golden Answer" (expected output) on the fly.
* **Live Comparative Evaluation:** Pits a "Concise" agent against an "Empathetic" agent in real-time.
* **Real `judgeval` Integration:** Utilizes a Python backend to run actual `judgeval` scorers, including built-in scorers and a custom `EmpathyScorer`.
* **Direct-to-Portal Tracing:** All agent interactions and evaluations are sent as traces to your specified project in the Judgment Labs portal.
* **Real-time Score Display:** The frontend immediately displays the actual scores returned by the `judgeval` evaluation for instant feedback.
* **E-commerce Guardrails:** Includes a basic AI-powered guardrail to ensure test queries are relevant to an e-commerce context.

## About `judgeval`

This project is powered by `judgeval`, an open-source toolkit from Judgment Labs designed for the post-building phase of agent development. It provides the essential tools for tracing and evaluating autonomous, stateful agents.

The core idea is to capture runtime data from agent-environment interactions to enable continuous learning and self-improvement. By tracing every input, output, and tool call, developers can debug agent runs, collect data, and pinpoint performance bottlenecks.

This application specifically uses `judgeval` for two key purposes:

1.  **Tracing:** The `@judgment.observe` decorator automatically traces every agent run, capturing the full context for debugging and analysis in the Judgment Cloud.
2.  **Evals:** We use `judgeval`'s powerful evaluation framework to run a suite of scorers on each agent's response. This includes built-in scorers like `AnswerCorrectnessScorer` and `FaithfulnessScorer`, as well as a custom-built `EmpathyScorer` that uses an LLM-as-a-judge to measure a more subjective quality.

## ⚙️ How It Works

This application uses a client-server architecture:

1.  **Frontend (`index.html`):** A static web page that runs in the user's browser. It captures the user's query and communicates with the backend.
2.  **Backend (`app.py`):** A lightweight Python server built with Flask. It receives requests from the frontend, runs all the AI and `judgeval` logic, and sends the results back. This is where the real `judgeval` library is used.

## 🚀 Setup and Installation

Follow these steps to get the application running on your local machine.

### 1. Prerequisites

* Python 3.8+
* An active OpenAI API Key
* Your Judgment Labs API Key and Organization ID

### 2. Clone the Repository

First, clone the project repository to your local machine.

```bash
git clone <your-repository-url>
cd <repository-name>
```

### 3. Create a Virtual Environment

It's highly recommended to use a virtual environment to manage dependencies.

```bash
# Create the virtual environment
python -m venv venv

# Activate it
# On macOS/Linux:
source venv/bin/activate
# On Windows:
.\venv\Scripts\activate
```

### 4. Install Dependencies

Install the required Python libraries from the `requirements.txt` file.

```bash
pip install -r requirements.txt
```

### 5. Set Environment Variables

The application requires three environment variables to connect to the OpenAI and Judgment Labs APIs.

```bash
# On macOS/Linux
export OPENAI_API_KEY="sk-..."
export JUDGMENT_API_KEY="..."
export JUDGMENT_ORG_ID="..."

# On Windows (Command Prompt)
set OPENAI_API_KEY="sk-..."
set JUDGMENT_API_KEY="..."
set JUDGMENT_ORG_ID="..."
```

## ▶️ Running the Application

The application requires two components to be running simultaneously: the Python backend and the HTML frontend.

### 1. Start the Python Backend

In your terminal (with the virtual environment activated and environment variables set), run the following command:

```bash
python app.py
```

You should see output indicating that the server is running, something like:
`* Running on http://127.0.0.1:5001`

**Keep this terminal window open.**

### 2. Open the Frontend

In your file explorer, find the `index.html` file and open it with your preferred web browser (e.g., Chrome, Firefox, Safari).

You can now use the application! Enter a query, click "Run Test", and see the results appear in the UI and in your Judgment Labs portal.

## 📦 Git Repository Contents

To make this project shareable and reproducible, your Git repository should contain the following files:

#### `app.py`

The core Python Flask server that contains all backend logic, agent definitions, and `judgeval` integration.

#### `index.html`

The interactive user interface that runs in the browser and communicates with the `app.py` backend.

#### `requirements.txt`

This file lists all the Python dependencies required to run the backend server. This allows others to install the exact same libraries you used.

```text
Flask
Flask-Cors
openai
judgeval[openai]
```

#### `README.md`

This file! It provides all the necessary information for another person to understand, set up, and run your project.

#### `.gitignore`

This is a standard file that tells Git which files and folders to ignore. It's important for keeping the repository clean of temporary files and sensitive information.

```text
# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
venv/

# IDE files
.idea/
.vscode/

# Environment files
.env
