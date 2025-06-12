# Memory Chat - AI Chatbot with Long-Term Memory

A sophisticated AI chatbot application that maintains conversation history in PostgreSQL, enabling natural and context-aware interactions across chat sessions.

## 📋 Overview

Memory Chat combines Google's Gemini API for natural language processing with PostgreSQL for persistent memory. The application summarizes older messages to maintain context without exceeding token limits, delivering a seamless chat experience that remembers past interactions.

## ✨ Features

- **Long-term memory** powered by PostgreSQL database
- **Context summarization** to handle lengthy conversation histories
- **Session management** for multiple independent conversations
- **Clean, responsive UI** built with Streamlit
- **Docker-based deployment** for seamless setup and scalability
- **Database administration** through pgAdmin web interface

## 🛠️ Tech Stack

- **Backend:** Python 3.13+
- **AI:** Google Gemini 2.0 Flash, GPT4.1-mini
- **Database:** PostgreSQL 15
- **UI:** Streamlit
- **Containers:** Docker & Docker Compose
- **Database Management:** pgAdmin 4

## 📦 Installation

### Prerequisites
- Docker and Docker Compose
- Python 3.8 or higher
- Google Gemini API key

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/memory_chat.git
   cd memory_chat
