import json

from ai_client import analyze_message

scam = ("Dear customer, your SBI account will be blocked today. Update KYC now: "
        "http://bit.ly/sbi-kyc-update . Call 9876543210")
legit = "Hi, your Swiggy order #4521 is out for delivery and will arrive in 10 minutes."

for msg in (scam, legit):
    print(json.dumps(analyze_message(msg), indent=2))
    print("-" * 40)