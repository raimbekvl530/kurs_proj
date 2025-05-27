import os
import requests

NEUROSPACE_API_KEY = os.environ.get("OPENAI_API_KEY")  ,#ENV 

def ask_chatgpt(user_message):
    url = "https://api.neurospace.pro/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {NEUROSPACE_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "user", "content": user_message}
        ]
    }
    response = requests.post(url, json=data, headers=headers)

    if response.status_code == 200:
        result = response.json()
        return result["choices"][0]["message"]["content"]
    else:
        return f"Ошибка API: {response.status_code} {response.text}"


    
