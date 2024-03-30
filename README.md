# Matrix-client

A simple matrix API wrapper for python. I don't know why I didn't just use/wrap matrix-nio or something, but oh well, now I made this. I mean, I guess it supports message edits way better than nio and anything nio based? Cause they're a separate event type here, and with nio you gotta do a bit of magic fuckery to distinguish between messages and message edits? So that's kinda cool?

## Installing

Because `matrix-client` is already taken on pypi, because I lack creativity and because I don't think this project is large enough to publish there as of yet, you can only install it directly from github:

```python
pip install git+https://github.com/rizerphe/matrix-client.git
```

## Usage

```python
import os

from dotenv import load_dotenv

from matrix_client import Client, MessageEvent


client = Client("https://matrix.org")


@client.on.message
async def on_message(message: MessageEvent) -> None:
    print(message)


if __name__ == "__main__":
    load_dotenv()
    client.run(
        os.getenv("MATRIX_USERNAME", ""),
        os.getenv("MATRIX_PASSWORD", ""),
    )
```
