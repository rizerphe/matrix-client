import aiohttp


class Authentication:
    """Represents an authentication class for the bot."""

    def __init__(self, homeserver_url: str) -> None:
        self.homeserver_url = homeserver_url
        self.token: str | None = None

    async def password_auth(self, username: str, password: str) -> None:
        """Authenticate using a username and password."""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.homeserver_url}/_matrix/client/v3/login",
                json={
                    "type": "m.login.password",
                    "identifier": {"type": "m.id.user", "user": username},
                    "password": password,
                },
            ) as response:
                response_json = await response.json()
                self.token = response_json["access_token"]

    async def get_token(self) -> str:
        """Return the access token."""
        if self.token is None:
            raise ValueError("Token is not set.")
        return self.token
