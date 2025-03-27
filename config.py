import os

class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN", "7656369802:AAGdlo88cewouuiviq-eHoRHdxj_Ktji3To")
    API_ID = int(os.getenv("API_ID", "28795512"))
    API_HASH = os.getenv("API_HASH", "c17e4eb6d994c9892b8a8b6bfea4042a")
    MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://Radheee:sanatani@cluster0.sgop4.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")

config = Config()
