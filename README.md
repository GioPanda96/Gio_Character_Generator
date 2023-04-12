# Gio's D&D 5e Character Generator

An AI based character sheet generator for D&D 5e.
Currently running here: https://giovannipanda.pythonanywhere.com

The code takes a character description in conversational english and outputs a full and editable D&D 5e character sheet, complete of everything you might need to play.
The generator uses OpenAI models for the text content and DeepAI for the character image.

<sub>Note: the OpenAI API key is taken as an input in the home page of the website, while the DeepAI key is hard coded in for REASONS. Since I obviously don't want to share my personal key, it has been removed from script.py, and has to be put in manually if you want to try the code outside the website.
```
deepai_api_key = 'DEEPAI_KEY'
```
</sub>

## How do I use this?

The tool is very simple to use, just follow these steps:

**1 - Go to the website**: https://giovannipanda.pythonanywhere.com

**2 - Get yourself an OpenAI Key**. You will need an OpenAI API key to use the tool, since the generation costs a very small amount of money (just a few cents). The money doesn't go to me, it goes to OpeanAI to allow us to use their model.
What you need to do is create an OpenAI account, add a billing method and then go to the link below to get your API key.
https://platform.openai.com/account/api-keys

**3 - Describe your character!** Describe your character in plain english. You can add as much or as little detail as you want: everything that you omit will (hopefully) be filled in by the AI.
If you feel like you have no imagination, you can always click "Randomize". That's not an AI call, so you can do it as many times as you want for free.
Description Example: "Sasha is a level 13 rogue assassin, with a passion for coffee and a beloved kitten named Burger"

**4 - Choose your model**. Choose the model used to generate your character. If you don't know what a model is, check the info below.

## What model do I choose?

**GPT-3.5 Turbo**: This model is very fast, fairly reliable, and produces mid to decent character sheets. Its best feature is cost: a complete character sheet generation will cost about 0.02$, however the quality of the final character sheet is not fantastic: it will require some work to make it play ready. Great if you just need to generate some NPCs, but I'd use gpt-4 for my own playable characters.

**GPT-4**: This model is a bit slower, and it costs way more at about 0.4$ per character, but it almost never fails, and produces very high quality character sheets, with more detailed racial and class traits, as well as more interesting backstories. It's also way less prone to hallucinations, meaning your characters will always "make sense".

**NOTE: GPT-4 is currently in closed beta, so if you want to use it you'll have to opt in here and wait for OpenAI to accept you:**
https://openai.com/waitlist/gpt-4-api
