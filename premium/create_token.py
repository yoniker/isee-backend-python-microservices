from cryptography.fernet import Fernet
key = Fernet.generate_key()
# with open('iSee_symmetric_key.key','wb') as f:
#     f.write(key)
