# Matrix-client

A simple matrix API wrapper for python. I don't know why I didn't just use/wrap matrix-nio or something, but oh well, now I made this. I mean, I guess it supports message edits way better than nio and anything nio based? Cause they're a separate event type here, and with nio you gotta do a bit of magic fuckery to distinguish between messages and message edits? So that's kinda cool?

## Usage

```python
import os

from dotenv import load_dotenv

from matrix_client import Client, Context, MessageEvent


client = Client("https://matrix.org")


@client.on.message
async def on_message(ctx: Context[MessageEvent]) -> None:
    print(ctx.event)


if __name__ == "__main__":
    load_dotenv()
    client.run(
        os.getenv("MATRIX_USERNAME", ""),
        os.getenv("MATRIX_PASSWORD", ""),
    )
```
