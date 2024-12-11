class Message:
    def __init__(self, sender: str, content: str) -> None:
        self.sender = sender
        self.content = content

    def to_openapi(self) -> dict[str, str]:
        return {
            "role": (self.sender if self.sender in ["user", "system"] else "user"),
            "content": self.content,
        }

    def to_localapi(self) -> dict[str, str]:
        return {"role": self.sender, "content": self.content}

    def to_text(self) -> str:
        return f"{self.sender}: {self.content}"
