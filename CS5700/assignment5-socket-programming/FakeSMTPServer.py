import asyncore
import smtpd

class CustomSMTPServer(smtpd.SMTPServer):
    def process_message(self, peer, mailfrom, rcpttos, data, **kwargs):
        print('--------------------------------------------------')
        print(f'Receiving message from: {peer}')
        print(f'Message content:\n{data.decode()}')
        print('--------------------------------------------------')

# Start server on port 1025
server = CustomSMTPServer(('127.0.0.1', 1025), None)
print("Fake SMTP Server is running on port 1025...")
asyncore.loop()