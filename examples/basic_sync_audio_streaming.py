#!/usr/bin/env python3

"""
Basic audio streaming example.

This example shows how to stream the audio data from the TTS engine,
and how to get the WordBoundary events from the engine (which could
be ignored if not needed).

The example streaming_with_subtitles.py shows how to use the
WordBoundary events to create subtitles using SubMaker.
"""

import asyncio
import edge_tts

TEXT = "Hello World!"
VOICE = "en-GB-SoniaNeural"
OUTPUT_FILE = "test.mp3"


def sync_stream():
    """Synchronous wrapper for the asynchronous stream generator."""
    communicate = edge_tts.Communicate(TEXT, VOICE)
    loop = asyncio.get_event_loop()
    async_gen = communicate.stream()

    while True:
        try:
            chunk = loop.run_until_complete(async_gen.__anext__())
            yield chunk
        except StopAsyncIteration:
            break
        except Exception as e:
            print(f"An error occurred: {e}")
            break


def main() -> None:
    """Main function to process audio and metadata synchronously."""
    with open(OUTPUT_FILE, "wb") as file:
        for chunk in sync_stream():
            if chunk["type"] == "audio":
                file.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                print(f"WordBoundary: {chunk}")


if __name__ == "__main__":
    main()
