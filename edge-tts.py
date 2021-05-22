#!/usr/bin/env python3
import sys
import json
import uuid
import signal
import argparse
import urllib.request
import asyncio
import ssl
import websockets
import unicodedata
from email.utils import formatdate
from xml.sax.saxutils import escape

trustedClientToken = '6A5AA1D4EAFF4E9FB37E23D68491D6F4'
ssl_context = ssl.create_default_context()
voiceList = 'https://speech.platform.bing.com/consumer/speech/synthesize/readaloud/voices/list?trustedclienttoken=' + trustedClientToken
wsUrl = 'wss://speech.platform.bing.com/consumer/speech/synthesize/readaloud/edge/v1?TrustedClientToken=' + trustedClientToken

def debug(msg, fd=sys.stderr):
	if DEBUG: print(msg, file=fd)
def terminator(signo, stack_frame): sys.exit()
signal.signal(signal.SIGINT, terminator)
signal.signal(signal.SIGTERM, terminator)
def connectId(): return str(uuid.uuid4()).replace("-", "")
def removeIncompatibleControlChars(s): return "".join(ch for ch in s if unicodedata.category(ch)[0]!="C")

def list_voices():
	with urllib.request.urlopen(voiceList) as url:
		debug("Loading json from %s" % voiceList)
		data = json.loads(url.read().decode())
		debug("JSON Loaded")
		for voice in data:
			print()
			for key in voice.keys():
				debug("Processing key %s" % key)
				if key in ["Name", "SuggestedCodec", "FriendlyName", "Status"]:
					debug("Key %s skipped" % key)
					continue
				print("%s: %s" % ("Name" if key == "ShortName" else key, voice[key]))
	print()

async def run_tts():
	async with websockets.connect(wsUrl, ssl=ssl_context) as ws:
		message='X-Timestamp:'+formatdate()+'\r\nContent-Type:application/json; charset=utf-8\r\nPath:speech.config\r\n\r\n'
		message+='{"context":{"synthesis":{"audio":{"metadataoptions":{"sentenceBoundaryEnabled":"'+sentenceBoundaryEnabled+'","wordBoundaryEnabled":"'+wordBoundaryEnabled+'"},"outputFormat":"' + codec + '"}}}}\r\n'
		await ws.send(message)
		debug("> %s" % message)
		message='X-RequestId:'+connectId()+'\r\nContent-Type:application/ssml+xml\r\n'
		message+='X-Timestamp:'+formatdate()+'Z\r\nPath:ssml\r\n\r\n'
		message+="<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='en-US'>"
		message+="<voice  name='" + voice + "'>" + "<prosody pitch='" + pitchString + "' rate ='" + rateString + "' volume='" + volumeString + "'>" + escape(text) + '</prosody></voice></speak>'
		await ws.send(message)
		debug("> %s" % message)
		while True:
			recv = await ws.recv()
			recv = recv.encode() if type(recv) is not bytes else recv
			debug("< %s" % recv)
			if b'turn.end' in recv:
				break
			elif b'Path:audio\r\n' in recv:
				sys.stdout.buffer.write(recv.split(b'Path:audio\r\n')[1])

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Microsoft Edge's Online TTS Reader")
	group = parser.add_mutually_exclusive_group(required=True)
	group.add_argument('-t', '--text', help='what TTS will say')
	group.add_argument('-f', '--file', help='same as --text but read from file')
	parser.add_argument('-v', '--voice', help='voice for TTS. Default: en-US-AriaNeural', default='en-US-AriaNeural')
	parser.add_argument('-c', '--codec', help="codec format. Default: audio-24khz-48kbitrate-mono-mp3. Another choice is webm-24khz-16bit-mono-opus", default='audio-24khz-48kbitrate-mono-mp3')
	group.add_argument('-l', '--list-voices', help="lists available voices. Edge's list is incomplete so check https://bit.ly/2SFq1d3", action='store_true')
	parser.add_argument('-p', '--pitch', help="set TTS pitch. Default +0Hz, For more info check https://bit.ly/3eAE5Nx", default="+0Hz")
	parser.add_argument('-r', '--rate', help="set TTS rate. Default +0%%. For more info check https://bit.ly/3eAE5Nx", default="+0%")
	parser.add_argument('-V', '--volume', help="set TTS volume. Default +0%%. For more info check https://bit.ly/3eAE5Nx", default="+0%")
	parser.add_argument('-s', '--enable-sentence-boundary', help="enable sentence boundary (not implemented but set)", action='store_true')
	parser.add_argument('-w', '--disable-word-boundary', help="disable word boundary (not implemented but set)", action='store_false')
	parser.add_argument('-D', '--debug', help="some debugging", action='store_true')
	args = parser.parse_args()
	DEBUG = args.debug

	if (args.text or args.file) is not None:
		if args.file is not None:
			# we need to use sys.stdin.read() because some devices
			# like Windows and Termux don't have a /dev/stdin.
			if args.file == "/dev/stdin":
				debug("stdin detected, reading natively from stdin")
				args.text = sys.stdin.read()
			else:
				debug("reading from %s" % args.file)
				with open(args.file, 'r') as file:
					args.text = file.read()
		codec = args.codec
		voice = args.voice
		pitchString = args.pitch
		rateString = args.rate
		volumeString = args.volume
		sentenceBoundaryEnabled = 'true' if args.enable_sentence_boundary else 'false'
		wordBoundaryEnabled = 'true' if args.disable_word_boundary else 'false'
		text = removeIncompatibleControlChars(args.text)
		asyncio.get_event_loop().run_until_complete(run_tts())
	elif args.list_voices:
		list_voices()
