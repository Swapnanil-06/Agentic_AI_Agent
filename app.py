from dotenv import load_dotenv
from openai import OpenAI
import json
import os
import requests
from pathlib import Path
from pypdf import PdfReader
import gradio as gr
from profile_facts import education_context, factual_reply
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env", override=False)
GROQ_API_KEY = os.getenv("GROQ_API_KEY")


def push(text):
    requests.post(
        "https://api.pushover.net/1/messages.json",
        data={
            "token": os.getenv("PUSHOVER_TOKEN"),
            "user": os.getenv("PUSHOVER_USER"),
            "message": text,
        }
    )


def record_user_details(email, name="Name not provided", notes="not provided"):
    push(f"Recording {name} with email {email} and notes {notes}")
    return {"recorded": "ok"}

def record_unknown_question(question):
    push(f"Recording {question}")
    return {"recorded": "ok"}

record_user_details_json = {
    "name": "record_user_details",
    "description": "Use this tool to record that a user is interested in being in touch and provided an email address",
    "parameters": {
        "type": "object",
        "properties": {
            "email": {
                "type": "string",
                "description": "The email address of this user"
            },
            "name": {
                "type": "string",
                "description": "The user's name, if they provided it"
            }
            ,
            "notes": {
                "type": "string",
                "description": "Any additional information about the conversation that's worth recording to give context"
            }
        },
        "required": ["email"],
        "additionalProperties": False
    }
}

record_unknown_question_json = {
    "name": "record_unknown_question",
    "description": "Always use this tool to record any question that couldn't be answered as you didn't know the answer",
    "parameters": {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "The question that couldn't be answered"
            },
        },
        "required": ["question"],
        "additionalProperties": False
    }
}

tools = [{"type": "function", "function": record_user_details_json},
        {"type": "function", "function": record_unknown_question_json}]


class Me:

    def __init__(self):
        self.openai = OpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")
        self.name = "Swapnanil Chattopadhyay"
        reader = PdfReader(BASE_DIR / "me" / "NEW_CV__.pdf")
        self.linkedin = ""
        for page in reader.pages:
            text = page.extract_text()
            if text:
                self.linkedin += text
        with open(BASE_DIR / "me" / "summary.txt", "r", encoding="utf-8") as f:
            self.summary = f.read()

    def convert_gradio_history(self, history):
        """Convert Gradio message history to OpenAI format"""
        messages = []
        if history:
            for msg in history:
                if isinstance(msg, dict):
                    # Handle message dict format
                    if msg.get('role') == 'user':
                        messages.append({"role": "user", "content": msg.get('content', '')})
                    elif msg.get('role') == 'assistant':
                        messages.append({"role": "assistant", "content": msg.get('content', '')})
                elif isinstance(msg, (list, tuple)) and len(msg) >= 2:
                    # Handle [user_msg, assistant_msg] format
                    if msg[0]:  # user message
                        messages.append({"role": "user", "content": str(msg[0])})
                    if msg[1]:  # assistant message
                        messages.append({"role": "assistant", "content": str(msg[1])})
        return messages

    def handle_tool_call(self, tool_calls):
        results = []
        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            print(f"Tool called: {tool_name}", flush=True)
            tool = globals().get(tool_name)
            result = tool(**arguments) if tool else {}
            results.append({"role": "tool","content": json.dumps(result),"tool_call_id": tool_call.id})
        return results
    
    def system_prompt(self):
        return (
            f"You are the AI assistant for {self.name}, answering questions about his career, projects, skills and education. "
            "Be concise, professional and factual. Speak about Swapnanil in the third person; do not pretend to be him. "
            "Use this source priority: checked education facts first, current summary second, supplementary CV third. "
            "Previous assistant messages are conversation, not evidence: correct an earlier mistake rather than repeating it. "
            "Never infer current study year from the four-year degree duration or graduation date. "
            "The 2026–2027 industry placement is Year 3. The final academic year is 2027–2028, after the placement. "
            "Do not call him a fourth-year student during the placement, even if an older source or prior assistant message does. "
            "If a substantive fact is missing, use record_unknown_question rather than inventing it. "
            "Only record contact details when the visitor voluntarily provides them to get in touch; do not promise a personal reply or pressure them for an email. "
            f"\n\n## Checked education facts — authoritative\n{education_context()}"
            f"\n\n## Current summary\n{self.summary}"
            f"\n\n## Supplementary CV — defer to checked facts if anything conflicts\n{self.linkedin}"
            f"\n\n## Final factual check\n{education_context()}"
        )

    def chat(self, message, history):
        try:
            checked_reply = factual_reply(message)
            if checked_reply is not None:
                return checked_reply

            # Simple greetings remain useful even if the model service is unavailable.
            if message.strip().lower().strip(" !.,?") in {"hi", "hello", "hey", "hiya"}:
                return "Hi! I’m Swapnanil’s AI assistant. What would you like to know about my experience or projects?"

            # Convert Gradio history to OpenAI format
            converted_history = self.convert_gradio_history(history)
            
            # Build messages array
            messages = [{"role": "system", "content": self.system_prompt()}] \
                       + converted_history \
                       + [{"role": "user", "content": message}]
            
            print(f"DEBUG: Processing message: {message}", flush=True)
            print(f"DEBUG: History length: {len(converted_history)}", flush=True)
            
            done = False
            final_response = None
            
            while not done:
                response = self.openai.chat.completions.create(
                    model="openai/gpt-oss-120b",
                    messages=messages,
                    tools=tools,
                    max_tokens=1000,
                    temperature=0.2
                )

                if response.choices[0].finish_reason == "tool_calls":
                    message_obj = response.choices[0].message
                    tool_calls = message_obj.tool_calls
                    
                    # Store the assistant's response if it exists (this is the user-facing message)
                    if message_obj.content:
                        final_response = message_obj.content
                    
                    results = self.handle_tool_call(tool_calls)
                    
                    # Convert message_obj to dict format for messages list
                    messages.append({
                        "role": "assistant",
                        "content": message_obj.content,
                        "tool_calls": [
                            {
                                "id": tc.id,
                                "type": tc.type,
                                "function": {
                                    "name": tc.function.name,
                                    "arguments": tc.function.arguments
                                }
                            } for tc in tool_calls
                        ]
                    })
                    messages.extend(results)
                    
                    # Continue the conversation to get the final response after tool calls
                    continue
                else:
                    done = True
                    final_response = response.choices[0].message.content

            # Return the final response
            response_content = final_response or "I'm not sure how to respond."
            print(f"DEBUG: Response: {response_content}", flush=True)
            return response_content
        
        except Exception as e:
            error_text = f"Chatbot failed.\nUser asked: {message}\nError: {str(e)}"
            print(f"ERROR: {error_text}", flush=True)

            # A service failure is not an unknown question, and notification may fail too.
            return "Sorry, the assistant is temporarily unavailable. Please try again later or email swapnanilchattopadhyay06@gmail.com."


    

if __name__ == "__main__":
    me = Me()
    gr.ChatInterface(me.chat, type="messages").launch()
