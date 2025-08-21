# Chatbot

Simple Flet-based chat application using Google's Gemini API with persistent chat history.

## Configuration

Create a `settings.json` file or use the settings dialog to provide your Gemini API key.

The app leverages the official `google-generativeai` client for talking to Gemini and
uses `duckduckgo-search` plus `beautifulsoup4` for its `/research` command.

## Running

```bash
python main.py
```

Use `/research <topic>` in the chat to gather and summarise web content.
