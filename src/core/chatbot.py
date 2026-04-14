class Chatbot:
    def __init__(self, name="Mon Bot"):
        self.name = name
    
    def repondre(self, message):
        return f"Vous avez dit : {message}"
