# config.py - central place for feature flags and secrets fetch (from env)
import os

def get_env(name: str, default=None):
    return os.getenv(name, default)

def get_gemini_key():
    return os.getenv("GEMINI_API_KEY")
