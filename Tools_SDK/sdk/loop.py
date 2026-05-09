#!/usr/bin/env python3
import os
import time
from dotenv import load_dotenv

load_dotenv()

def run_agent_loop(interval=300):
    """Simple agent loop placeholder for Python"""
    print(f"ODIN Agent Loop active. Interval: {interval} seconds.")
    # This loop is now implemented in M3/main.py and root/odin_controller.py
    # We keep this for backward compatibility with SDK calls.
    pass

if __name__ == "__main__":
    run_agent_loop()
