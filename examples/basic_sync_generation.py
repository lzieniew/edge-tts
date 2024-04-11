#!/usr/bin/env python3

"""
Basic example of edge_tts usage in synchronous function
"""

import asyncio

import edge_tts

TEXT = "Hello World!"
VOICE = "en-GB-SoniaNeural"
OUTPUT_FILE = "test.mp3"


def main() -> None:
    """Main function"""
    communicate = edge_tts.Communicate(TEXT, VOICE)
    communicate.sync_save(OUTPUT_FILE)


if __name__ == "__main__":
    main()
