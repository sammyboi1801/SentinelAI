<img width="1065" height="226" alt="image" src="https://github.com/user-attachments/assets/d8c6fede-1cd8-4517-b626-2deb2d9bd9c5" />

> **Your proactive OS assistant.** Sentinel is a terminal-based autonomous agent that integrates deeply with your local operating system, files, and cloud services to execute complex workflows via natural language.

---

## 📖 Table of Contents

* [Overview](#-overview)
* [Key Features](#-key-features)
* [System Architecture](#-system-architecture)
* [Installation & Setup](#-installation--setup)
* [Configuration](#-configuration)
* [Usage Guide](#-usage-guide)
* [Available Tools](#-available-tools)
* [Contributing](#-contributing)
* [Safety & Privacy](#-safety--privacy)

---

## 🔭 Overview

Sentinel is not just a chatbot; it is an **Action Engine**. Unlike web-based LLMs that live in a sandbox, Sentinel runs locally on your machine with access to your file system, applications, and peripherals.

It operates on a **Think-Plan-Act** loop:

1.  **Perceives** user intent via natural language.
2.  **Retrieves** context from its long-term vector memory and local SQL file index.
3.  **Selects** specific tools from a registry (e.g., "Send Email", "Search Files", "Analyze Screen").
4.  **Executes** the action safely (asking for permission when necessary).
5.  **Learns** from the interaction to build a persistent user profile.

---

## ✨ Key Features

*   **🧠 Multi-Brain Support:** Powered by `litellm`, Sentinel can seamlessly switch between **OpenAI**, **Anthropic**, **Groq**, or run locally with **Ollama**.
*   **💾 Hybrid Memory Architecture:**
    *   **Vector Database (ChromaDB):** Stores semantic memories, facts, and user preferences for long-term recall.
    *   **SQL Index (SQLite):** Maintains a lightning-fast index of your local filesystem for rapid file retrieval.
*   **🔌 Deep OS Integration:**
    *   Launch/close apps, manage processes, and control system volume/brightness.
    *   Organize messy folders, bulk rename files, and create documents.
    *   "Digital Twin" context awareness (knows what app you are using).
*   **☁️ Google Workspace Native:**
    *   Full 2-way sync with **Google Calendar** and **Gmail**.
    *   Natural language scheduling ("Clear my afternoon", "Draft an email to Bob").
*   **👀 Computer Vision:** Analyze your screen or webcam feed using Vision-capable models (GPT-4o, Claude 3.5 Sonnet).
*   **🛡️ Safety First:** "Human-in-the-loop" protocols require user approval for high-risk actions like deleting files, sending emails, or executing shell commands.

---

## 🏗 System Architecture

Sentinel is built on a modular Python architecture designed for extensibility.

### Core Components

*   **`main.py`**: The entry point. Handles CLI arguments using `typer` and initiates the boot sequence.
*   **`core/agent.py`**: The main agent loop. Manages the context window, parses JSON responses from the LLM, and triggers tools.
*   **`core/llm.py`**: A unified wrapper for different API providers (via `litellm`) that handles model selection, streaming, and error recovery.
*   **`core/registry.py`**: The "Tool Belt." Maps natural language tool descriptions to actual Python functions and injects safety wrappers like `ask_permission`.
*   **`tools/`**: A directory containing isolated modules for specific capabilities (e.g., `browser.py`, `file_ops.py`, `vision.py`).

---

## 🚀 Installation & Setup

### Prerequisites

*   Python 3.9 or higher.
*   (Optional) **Ollama** installed for local offline inference.
*   (Optional) A Google Cloud Console project for Gmail/Calendar integration.

### Step 1: Install from PyPI

As a published package, you can install Sentinel directly using pip:
```bash
pip install sentinel-ai
```

### Step 2: System Boot & Configuration

Run the initial setup wizard. This will guide you through setting your name, location, and API keys, which are stored securely using the `keyring` library.

```bash
sentinel config
```

### Step 3: Google Authentication (Optional but Recommended)

To enable Calendar and Gmail features:

1.  Download your OAuth 2.0 Client ID JSON from your Google Cloud Console project.
2.  Rename it to `credentials.json` and place it in the directory where you run Sentinel.
3.  Run the auth repair tool. This will open a browser window to authorize Sentinel.

```bash
sentinel auth
```

---

## ⚙ Configuration

Sentinel stores its primary configuration in `config.json` and sensitive API keys in your OS's secure credential manager.

**Supported Services:**

*   **Primary Brains:** OpenAI, Anthropic, Groq, Ollama
*   **Search Tools:** Tavily (recommended for RAG), DuckDuckGo
*   **Navigation:** Google Maps API

To view or update keys after the initial setup, you can re-run the configuration wizard:
```bash
sentinel config
```

---

## 🎮 Usage Guide

Start the agent's interactive shell:

```bash
sentinel
```

Or, start with a daily briefing (Weather, Calendar, Email summary):

```bash
sentinel --briefing
```

### Interactive CLI

Once inside the Sentinel shell, you can communicate with the agent using natural language.

### Example Natural Language Prompts

*   *"Find all PDF files on my Desktop modified last week and move them to a folder named Reports."*
*   *"Summarize the last 5 emails from my boss."*
*   *"Take a screenshot and tell me what code is visible."*
*   *"Plan a trip to New York for next weekend, check flights, and add it to my calendar."*

---

## 🛠 Available Tools

Sentinel comes equipped with a vast array of tools, dynamically registered and made available to the LLM. Below is a summary of its capabilities.

### 📂 File System & Indexing

*   **Smart Search:** Uses SQLite `fts5` for fast filename search and a Vector index for semantic content search ("Find that document about the project budget").
*   **File Operations:** Full CRUD (Create, Read, Write) for files.
*   **Code Drafts:** Safely drafts code to a `drafts/` directory for user review, never executing it directly.
*   **Organization:** Bulk rename files or sort them into folders based on date, extension, or other criteria.
*   **Document Factory:** Create Word (`.docx`) and Excel (`.xlsx`) files from scratch.

### 🌐 Web & Knowledge

*   **Deep Research:** Uses Tavily API to browse the web, scrape content, and synthesize answers.
*   **Browser Automation:** Can open URLs and extract text from webpages.
*   **Flight Search:** Find flight information via the SerperDev API.

### 🖥️ Desktop Automation & OS

*   **App Launcher:** Intelligent fuzzy matching to launch and close applications.
*   **System Control:** Set volume, brightness, or execute shell commands (with permission).
*   **Process Management:** List and kill running processes.
*   **Macros:** Execute pre-defined sequences of actions.

### 👀 Perception & Vision

*   **Screen Analysis:** `analyze_screen` allows the agent to "see" and understand the content on your display.
*   **Webcam Capture:** Use the webcam to capture images for analysis.
*   **Speech I/O:** `listen` to user voice commands and `speak` to provide audio responses.
*   **Context Awareness:** Can identify the currently active application window.

### 🧠 Memory & Cognition

*   **Long-term Memory:** Stores facts and user preferences (e.g., "User prefers dark mode") in ChromaDB for future interactions.
*   **Note Taking:** A simple system for adding and retrieving categorized notes.
*   **Reflection:** Can look back at logs to provide continuity across sessions.

### 📅 Calendar & Email (Google Workspace)

*   **Full Calendar Control:** List, create, and query events on your Google Calendar.
*   **Gmail Integration:** Read and send emails through your Gmail account.

---

## 🤝 Contributing

We welcome contributions! Sentinel is designed to be easily extensible.

### Directory Structure

*   `sentinel/core/`: The brain. Modify this if you are improving the LLM loop, context management, or configuration.
*   `sentinel/tools/`: The hands. **This is the best place to start.** Add new capabilities here.

### How to Add a New Tool

1.  Create a new Python file in `sentinel/tools/` (e.g., `spotify.py`).
2.  Define your function(s) in that file.
3.  Import your function into `sentinel/core/registry.py`.
4.  Add the function to the `TOOLS` dictionary in `registry.py`, wrapping it in `ask_permission` if it's a high-risk action.
5.  Add a description of the tool and its arguments to the `SYSTEM_PROMPT` in `registry.py` so the LLM knows how to use it.

---

## 🛡 Safety & Privacy

Because Sentinel has deep access to your system, safety is a core design principle.

1.  **Permission Gate:** Critical tools (File Deletion, Shell Commands, Sending Email, etc.) are wrapped in the `ask_permission` function. The agent's execution pauses until you explicitly approve the action by typing `y`.
2.  **Safe Code Drafting:** Sentinel never executes code it generates. It uses the `draft_code` tool to save scripts to a `drafts/` directory, allowing you to review them before manual execution.
3.  **Command Guardrails:** The `run_cmd` tool has extra checks to prevent accidental use of destructive commands like `rm` or `format`.
4.  **Local First:** All file indexes (SQL and ChromaDB) are stored locally in your user directory. No file data is sent to the cloud except for the specific text chunks required by the LLM API for a given task. Your API keys are stored securely in your operating system's native credential manager.

---

**Disclaimer:** *Sentinel is an autonomous agent. While many safety checks are in place, always review the actions it proposes before approving them, especially those involving file modification or shell command execution.*
