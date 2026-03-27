class Agent:
    def __init__(self, name: str, role: str, system_prompt: str = ""):
        self.name = name
        self.role = role
        self.system_prompt = system_prompt

    def respond(self, prompt: str) -> str:
        return f"[{self.name}/{self.role}] {prompt[:180]} -> analiz/taslak cevap"
