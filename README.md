# Personal AI Agent

An intelligent AI-powered chatbot that represents me, answering questions about my career, skills, and experience using my CV and LinkedIn profile data.

🌐 Live Demo
Try it out live: https://huggingface.co/spaces/Swap-069/Agentic_AI_Agent
The application is hosted on Hugging Face Spaces for easy access and demonstration.


## 🚀 Features

- **Intelligent Conversations**: Powered by Groq's LLaMA 3.3 70B model for natural, context-aware responses
- **Personal Representation**: Acts as my digital representative, answering career and background questions
- **Lead Generation**: Automatically captures interested users' contact information
- **Error Tracking**: Records unanswered questions for continuous improvement
- **Push Notifications**: Real-time notifications for new leads and system errors
- **Web Interface**: Clean, user-friendly Gradio interface

## 🏗️ Architecture

The system follows a multi-layered architecture with robust error handling:

System Flow Diagram
![WhatsApp Image 2025-09-15 at 09 00 08_b5aad897](https://github.com/user-attachments/assets/60a311af-0f3f-4e83-81af-c2ce16e01d46)


### Flow Overview:
1. **User Interface**: Gradio-powered chat interface for seamless user interaction
2. **Gradio App Layer**: Handles message processing and response display
3. **Groq API Engine**: LLaMA model processes queries and generates responses
4. **Error Handling**: Comprehensive error tracking with push notifications and safe fallbacks

## 🛠️ Tech Stack

- **Backend**: Python 3.12
- **AI Model**: Groq LLaMA 3.3 70B Versatile
- **Web Interface**: Gradio
- **PDF Processing**: PyPDF for CV parsing
- **Notifications**: Pushover API
- **Environment Management**: python-dotenv

## 📋 Prerequisites

- Python 3.12
- Groq API key
- Pushover account (optional, for notifications)

## 📁 Project Structure

```
Agentic_AI_Agent/
├── app.py                 # Main application file
├── me/
│   ├── NEW_CV__.pdf      # Your CV/resume
│   └── summary.txt       # Background summary
├── .env                 # Environment variables (not in repo)
├── .gitignore          # Git ignore rules
└── README.md          # This file
```

## 🔒 Privacy & Security

- **Environment Variables**: Sensitive API keys are stored in `.env` (excluded from version control)
- **Data Handling**: Personal information is only used for responses, not stored permanently
- **Error Logging**: Only questions and basic interaction data are logged

## 📱 Notifications

When configured with Pushover:
- Get notified when users provide contact information
- Receive alerts for system errors
- Track questions the agent couldn't answer


## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

🎓 Inspiration & Credits
This project is heavily inspired by Ed Donner's Complete Agentic AI Engineering Course on Udemy. The course provided excellent guidance on building intelligent AI agents with function calling capabilities and practical implementation patterns.
Course: Complete Agentic AI Engineering Course by Ed Donner
Instructor: Ed Donner - Co-Founder and CTO at AI startup Nebula.io
Special thanks to Ed for the comprehensive course content that made this project possible!

---

**Note**: This agent represents my personal and professional background. Feel free to adapt the code for your own use case!
