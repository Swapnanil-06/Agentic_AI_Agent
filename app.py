from dotenv import load_dotenv
from openai import OpenAI
import json
import os
import requests
from pypdf import PdfReader
import gradio as gr
load_dotenv(override=True)
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
        reader = PdfReader("me/NEW_CV__.pdf")
        self.linkedin = ""
        for page in reader.pages:
            text = page.extract_text()
            if text:
                self.linkedin += text
        with open("me/summary.txt", "r", encoding="utf-8") as f:
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
        system_prompt = f"You are acting as {self.name}. You are answering questions on {self.name}'s website, \
particularly questions related to {self.name}'s career, background, skills and experience. \
Your responsibility is to represent {self.name} for interactions on the website as faithfully as possible. \
You are given a summary of {self.name}'s background and LinkedIn profile which you can use to answer questions. \
Be professional and engaging, as if talking to a potential client or future employer who came across the website. \
If you don't know the answer to any question, use your record_unknown_question tool to record the question that you couldn't answer, even if it's about something trivial or unrelated to career. \
If the user is engaging in discussion, try to steer them towards getting in touch via email; ask for their email and record it using your record_user_details tool. "

        system_prompt += f"\n\n## Summary:\n{self.summary}\n\n## LinkedIn Profile:\n{self.linkedin}\n\n"
        system_prompt += f"With this context, please chat with the user, always staying in character as {self.name}."
        return system_prompt
    
    def chat(self, message, history):
        try:
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
                    model="llama-3.3-70b-versatile",
                    messages=messages,
                    tools=tools,
                    max_tokens=1000,
                    temperature=0.7
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

            # Push notification
            try:
                push(error_text)
            except Exception as push_err:
                print(f"Push notification failed: {push_err}", flush=True)

            # Record unknown question
            try:
                record_unknown_question(message)
            except Exception as log_err:
                print(f"Failed to log unknown question: {log_err}", flush=True)
                try:
                    push(f"Failed to log unknown question: {log_err}")
                except:
                    pass

            # Graceful fallback to user
            return "Sorry, I can't answer that right now. The owner has been notified and your question has been recorded."

    

if __name__ == "__main__":
    me = Me()
    gr.ChatInterface(me.chat, type="messages").launch()