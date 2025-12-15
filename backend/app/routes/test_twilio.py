from twilio.rest import Client

account_sid = "AC6e105a79612959f9d2cfb7b2d3534984"
auth_token = "5f944bf943704e6801a3358f4dfb4d7b"
twilio_number = "+13048026706"

client = Client(account_sid, auth_token)
message = client.messages.create(
    body="Smart RC Book test SMS!",
    from_=twilio_number,
    to="+917666279385"   # Use your verified number with no spaces
)
print("Sent, SID:", message.sid)