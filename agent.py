#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
agent.py
========
Local general-purpose AI assistant powered by Open models with
Model-Context-Protocol-style tooling.
'''

from __future__ import annotations

# Core imports
import os
import sys # Added for potential path manipulation if needed for modules
from pathlib import Path

from core.config import TOOL_CALL_PATTERN # Check if Orchestrator needs this directly or gets it via a method

from core.orchestrator import Orchestrator


def main():
    try:
        # Ensure the current working directory is in sys.path for module resolution,
        # if running scripts from subdirectories or in certain environments.
        # This is often handled by Python automatically but can be explicit if issues arise.
        # current_dir = str(Path(__file__).resolve().parent)
        # if current_dir not in sys.path:
        #     sys.path.insert(0, current_dir)
            
        orchestrator = Orchestrator()
    except ValueError as e:
        print(f"Failed to initialize Orchestrator: {e}")
        print("Please ensure OPENROUTER_API_KEY is set as an environment variable or in a .env file.")
        return
    except ImportError as e:
        print(f"Failed to import necessary modules: {e}")
        print("Please ensure all dependencies are installed and the project structure is correct.")
        print("Relevant paths might need to be added to PYTHONPATH or sys.path if running in an unusual way.")
        return
        
    print("\n🤖 JARVIS ready! (type 'exit' or press Ctrl+D to quit)\n")

    while True:
        try:
            user_in = input("User: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting JARVIS.")
            break

        if user_in.lower() in {"exit", "quit"}:
            print("\nExiting JARVIS.")
            break
        
        if not user_in:
            continue

        assistant_response = orchestrator.chat(user_in)
        print(f"JARVIS: {assistant_response}\n")


if __name__ == "__main__":
    main()
