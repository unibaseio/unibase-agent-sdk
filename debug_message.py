import sys
import os
sys.path.append(os.getcwd())
from a2a.types import Message

try:
    msg = Message.user("hello")
    print(f"Message ID: {msg.message_id}")
    print(f"Dump: {msg.model_dump(by_alias=True, exclude_none=True)}")
except Exception as e:
    print(f"Error: {e}")

print(f"Has user method: {hasattr(Message, 'user')}")
