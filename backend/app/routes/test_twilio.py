account_sid = "AC6e105a79612959f9d2cfb7b2d3534984".strip()
auth_token = "5f944bf943704e6801a3358f4dfb4d7b".strip()

from twilio.rest import Client
client = Client(account_sid, auth_token)

# Test authentication
account = client.api.accounts(account_sid).fetch()
print("Authenticated account SID:", account.sid)
