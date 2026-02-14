import os
import random
import re
from typing import Dict, List

import requests
from flask import Flask, jsonify, render_template, request


def _transform_text(text: str) -> str:
	if not text:
		return text

	replacements: Dict[str, str] = {
		"hello": "yo",
		"hi": "yo",
		"hey": "yo",
		"friend": "bestie",
		"friends": "besties",
		"cool": "slay",
		"awesome": "slay",
		"amazing": "slay",
		"good": "valid",
		"great": "fire",
		"bad": "mid",
		"boring": "mid",
		"crazy": "wild",
		"really": "fr",
		"very": "so",
		"yes": "bet",
		"no": "nah",
		"okay": "okok",
		"ok": "okok",
		"awesome": "fire",
		"bro": "bruh",
		"dude": "bruh",
		"money": "rizz",
		"talk": "yap",
		"talking": "yapping",
		"talked": "yapped",
		"laugh": "lol",
		"laughing": "lol",
		"hilarious": "lol",
	}

	emotes: List[str] = ["no cap", "fr", "ngl", "lowkey", "highkey", "slay"]

	def _swap(match: re.Match) -> str:
		word = match.group(0)
		lower = word.lower()
		replacement = replacements.get(lower)
		if not replacement:
			return word
		if word.isupper():
			return replacement.upper()
		if word[0].isupper():
			return replacement.capitalize()
		return replacement

	transformed = re.sub(r"\b[A-Za-z']+\b", _swap, text)

	if random.random() < 0.5:
		transformed = f"{transformed} ({random.choice(emotes)})"

	if random.random() < 0.4:
		transformed = transformed.replace("!", "!!!")

	return transformed


def _ai_transform(text: str) -> str:
	api_key = os.getenv("HACKCLUB_API_KEY")
	if not api_key:
		raise RuntimeError("Missing HACKCLUB_API_KEY environment variable.")

	payload = {
		"model": "qwen/qwen3-32b",
		"messages": [
			{
				"role": "system",
				"content": (
					"Transform the user's text into playful Gen Alpha slang. "
					"Keep meaning intact, be short, and avoid hateful or sexual content."
				),
			},
			{"role": "user", "content": text},
		],
	}

	response = requests.post(
		"https://ai.hackclub.com/proxy/v1/chat/completions",
		headers={
			"Authorization": f"Bearer {api_key}",
			"Content-Type": "application/json",
		},
		json=payload,
		timeout=30,
	)
	response.raise_for_status()
	data = response.json()
	return data["choices"][0]["message"]["content"].strip()


def create_app() -> Flask:
	app = Flask(__name__)

	@app.get("/")
	def home():
		return render_template("index.html")

	@app.post("/transform")
	def transform():
		payload = request.form or {}
		text = payload.get("text", "")
		return render_template("index.html", output=_transform_text(text))

	@app.post("/ai-transform")
	def ai_transform():
		payload = request.get_json(silent=True)
		if payload is None:
			payload = request.form or {}
		text = payload.get("text", "")
		if not text:
			return render_template("index.html", error="text is required boomer")
		try:
			output = _ai_transform(text)
		except RuntimeError as exc:
			return render_template("index.html", error=str(exc))
		except requests.RequestException:
			return render_template("index.html", error="request failed, womp womp, holup i am fixing ts maybe")
		return render_template("index.html", output=output)

	return app


app = create_app()


if __name__ == "__main__":
	app.run(host="0.0.0.0", port=3000, debug=True)
