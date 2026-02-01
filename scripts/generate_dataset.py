#!/usr/bin/env python
"""
Dataset Generation Script for ScamShield AI.

Generates training dataset for scam detection with:
- 1000+ total samples
- 60% scam, 40% legitimate
- 50% English, 40% Hindi, 10% Hinglish

Output: data/scam_detection_train.jsonl

See DATA_SPEC.md for schema details.
"""

import json
import os
import random
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Ensure we can import from app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Target distribution
TOTAL_SAMPLES = 1100  # Generate extra to ensure 1000+ after any filtering
SCAM_RATIO = 0.60  # 60% scam
LEGIT_RATIO = 0.40  # 40% legitimate

# Language distribution
EN_RATIO = 0.50  # 50% English
HI_RATIO = 0.40  # 40% Hindi
HINGLISH_RATIO = 0.10  # 10% Hinglish

# Scam type distribution (within scam samples)
SCAM_TYPES = {
    "lottery": 0.25,
    "bank_fraud": 0.25,
    "police_threat": 0.20,
    "phishing": 0.15,
    "courier_fraud": 0.10,
    "government_impersonation": 0.05,
}

# Base date for annotations
BASE_DATE = datetime(2026, 1, 28, 10, 0, 0)


# =============================================================================
# SCAM MESSAGE TEMPLATES
# =============================================================================

SCAM_TEMPLATES_EN = {
    "lottery": [
        "Congratulations! You have won ₹{amount} lakh in our lucky draw! Share your OTP to claim immediately.",
        "You are the lucky winner of ₹{amount} crore rupees! Send your bank details to claim the prize.",
        "WINNER! You have been selected for a cash prize of ₹{amount} lakh. Call now to receive payment.",
        "Dear customer, you won lottery prize worth ₹{amount} lakh. Send OTP to verify and claim.",
        "Congratulations! Your mobile number won ₹{amount} crore in our mega draw. Act now!",
        "You won iPhone 15 Pro Max! Click link to claim your prize: http://fake-prize.com",
        "Lucky winner! You've won ₹{amount} lakh cash prize. Share bank account to receive.",
        "Dear user, your number selected for ₹{amount} lakh lottery. Send documents immediately.",
        "JACKPOT! You won ₹{amount} crore. Call this number to claim: 9876543210",
        "Winner announcement! You are selected for cash reward of ₹{amount} lakh.",
    ],
    "bank_fraud": [
        "Your bank account will be blocked in 24 hours. Verify by sending ₹{amount} to our UPI.",
        "ALERT: Suspicious activity detected on your account. Share OTP to secure it.",
        "Dear customer, your KYC is incomplete. Update now to avoid account suspension.",
        "Your debit card is suspended. Call {phone} immediately to reactivate.",
        "URGENT: Your account has been compromised. Send OTP to verify identity.",
        "Your {bank} account needs immediate verification. Click: http://fake-bank.com",
        "Security alert! Unknown login attempt. Confirm by sharing your OTP.",
        "Your credit card has been blocked due to suspicious activity. Call now.",
        "Dear customer, your PAN is linked to multiple accounts. Update immediately.",
        "Account blocked! Send ₹{amount} processing fee to unblock: scammer@paytm",
    ],
    "police_threat": [
        "This is police department. You are under investigation. Pay ₹{amount} fine immediately.",
        "CYBER CRIME ALERT: Your Aadhaar linked to illegal activity. Pay penalty now.",
        "Your name appeared in money laundering case. Transfer ₹{amount} to avoid arrest.",
        "CBI notice: You are involved in crime. Pay ₹{amount} or face arrest today.",
        "Police warning: Warrant issued against you. Clear penalty of ₹{amount} now.",
        "ED investigation: Your bank accounts frozen. Pay ₹{amount} to release.",
        "Court order: Appear immediately or pay fine of ₹{amount} to avoid arrest.",
        "Cyber cell: Your mobile used for fraud. Pay ₹{amount} penalty immediately.",
        "This is Income Tax department. Pay pending tax of ₹{amount} to avoid prosecution.",
        "Legal notice: Case filed against you. Settle for ₹{amount} to close case.",
    ],
    "phishing": [
        "Click here to verify your account: http://fake-verify-{bank}.com",
        "Your password expires today. Update now: http://fake-security.com",
        "Confirm your identity by clicking: http://scam-{bank}-verify.com",
        "Action required: Verify account at http://fake-{bank}-login.com",
        "Your session expired. Login again: http://phishing-bank.com/login",
        "Update KYC by clicking this link: http://fake-kyc-update.com",
        "Claim your refund at: http://fake-refund-{bank}.com",
        "Your reward is waiting! Click: http://fake-prize-claim.com",
        "Verify your mobile at: http://fake-mobile-verify.com",
        "Complete registration: http://fake-registration-{bank}.com",
    ],
    "courier_fraud": [
        "Your parcel is stuck at customs. Pay ₹{amount} clearance fee to release.",
        "Delivery failed! Pay ₹{amount} to reschedule: scammer@paytm",
        "Your package contains prohibited items. Pay ₹{amount} fine or face arrest.",
        "Customs hold: International parcel needs ₹{amount} duty payment.",
        "Your courier requires address verification fee of ₹{amount}.",
        "Package seized by customs. Pay ₹{amount} to fraud@ybl to release.",
        "Delivery partner unable to deliver. Pay ₹{amount} redelivery charges.",
        "Your parcel flagged for inspection. Clear ₹{amount} fee immediately.",
        "Import duty pending: Pay ₹{amount} to receive your parcel.",
        "Courier returned! Pay ₹{amount} return handling fee.",
    ],
    "government_impersonation": [
        "Government is offering COVID relief ₹{amount}. Register with Aadhaar and OTP.",
        "PM Kisan Yojana: Claim ₹{amount} benefit. Send bank details now.",
        "Gas subsidy of ₹{amount} credited. Share OTP to receive in account.",
        "PMAY housing subsidy: Get ₹{amount}. Apply with Aadhaar: http://fake-gov.com",
        "Free ration scheme: Register at http://fake-ration.com for benefits.",
        "Ayushman Bharat: Claim ₹{amount} health benefit. Share documents.",
        "LPG refund of ₹{amount} pending. Send OTP to receive.",
        "Government job vacancy! Pay ₹{amount} registration fee.",
        "MNREGA payment of ₹{amount} pending. Verify bank account.",
        "Pension scheme: Get ₹{amount}/month. Register now with fee.",
    ],
}

SCAM_TEMPLATES_HI = {
    "lottery": [
        "बधाई हो! आपने ₹{amount} लाख जीते हैं! OTP शेयर करें और इनाम पाएं।",
        "आप लॉटरी के विजेता हैं! ₹{amount} करोड़ जीतने के लिए बैंक डिटेल्स भेजें।",
        "विजेता! आपको ₹{amount} लाख का नकद पुरस्कार मिला है। तुरंत कॉल करें।",
        "प्रिय ग्राहक, आपने ₹{amount} लाख की लॉटरी जीती है। OTP से वेरिफाई करें।",
        "मुबारक हो! आपका नंबर ₹{amount} करोड़ के मेगा ड्रा में चुना गया।",
        "आपने iPhone 15 जीता! इनाम लेने के लिए लिंक पर क्लिक करें।",
        "विजेता! आपको ₹{amount} लाख मिले हैं। बैंक खाता भेजें।",
        "आपका नंबर ₹{amount} लाख लॉटरी में चुना गया। दस्तावेज़ भेजें।",
        "जैकपॉट! आपने ₹{amount} करोड़ जीते। इस नंबर पर कॉल करें।",
        "विजेता घोषणा! आपको ₹{amount} लाख का इनाम मिला है।",
    ],
    "bank_fraud": [
        "आपका बैंक खाता 24 घंटे में ब्लॉक हो जाएगा। वेरिफाई करने के लिए ₹{amount} भेजें।",
        "अलर्ट: आपके खाते पर संदिग्ध गतिविधि। OTP शेयर करके सुरक्षित करें।",
        "प्रिय ग्राहक, आपका KYC अधूरा है। खाता बंद होने से पहले अपडेट करें।",
        "आपका डेबिट कार्ड सस्पेंड है। तुरंत {phone} पर कॉल करें।",
        "जरूरी: आपका खाता हैक हुआ है। पहचान वेरिफाई करने के लिए OTP भेजें।",
        "आपके {bank} खाते को तुरंत वेरिफिकेशन चाहिए। क्लिक करें।",
        "सुरक्षा अलर्ट! अज्ञात लॉगिन। OTP से कंफर्म करें।",
        "संदिग्ध गतिविधि के कारण क्रेडिट कार्ड ब्लॉक। तुरंत कॉल करें।",
        "आपका PAN कई खातों से जुड़ा है। तुरंत अपडेट करें।",
        "खाता ब्लॉक! अनब्लॉक करने के लिए ₹{amount} भेजें: scammer@paytm",
    ],
    "police_threat": [
        "यह पुलिस है। आप जांच में हैं। ₹{amount} जुर्माना तुरंत भरें।",
        "साइबर क्राइम अलर्ट: आपका आधार अवैध गतिविधि से जुड़ा है। पेनाल्टी भरें।",
        "मनी लॉन्ड्रिंग केस में आपका नाम। गिरफ्तारी से बचने के लिए ₹{amount} भेजें।",
        "CBI नोटिस: आप अपराध में शामिल। ₹{amount} भरें या आज गिरफ्तार।",
        "पुलिस चेतावनी: वारंट जारी। ₹{amount} पेनाल्टी तुरंत क्लियर करें।",
        "ED जांच: बैंक खाते फ्रीज। ₹{amount} भरकर रिलीज करवाएं।",
        "कोर्ट आदेश: तुरंत हाज़िर हों या ₹{amount} जुर्माना भरें।",
        "साइबर सेल: आपका मोबाइल फ्रॉड में इस्तेमाल। ₹{amount} पेनाल्टी भरें।",
        "यह आयकर विभाग है। ₹{amount} टैक्स बकाया भरें।",
        "कानूनी नोटिस: केस दर्ज। ₹{amount} में सेटलमेंट करें।",
    ],
    "phishing": [
        "खाता वेरिफाई करने के लिए क्लिक करें: http://fake-verify.com",
        "आपका पासवर्ड आज एक्सपायर हो रहा है। अभी अपडेट करें।",
        "पहचान कंफर्म करने के लिए क्लिक करें: http://fake-bank.com",
        "एक्शन जरूरी: खाता वेरिफाई करें।",
        "सेशन एक्सपायर। फिर से लॉगिन करें।",
        "KYC अपडेट करने के लिए लिंक पर क्लिक करें।",
        "रिफंड क्लेम करने के लिए क्लिक करें।",
        "इनाम इंतज़ार कर रहा है! क्लिक करें।",
        "मोबाइल वेरिफाई करें।",
        "रजिस्ट्रेशन पूरा करें।",
    ],
    "courier_fraud": [
        "आपका पार्सल कस्टम्स में फंसा है। ₹{amount} क्लियरेंस फीस भरें।",
        "डिलीवरी फेल! ₹{amount} भरकर रीशेड्यूल करें।",
        "पैकेज में प्रतिबंधित सामान। ₹{amount} जुर्माना भरें।",
        "कस्टम्स होल्ड: इंटरनेशनल पार्सल पर ₹{amount} ड्यूटी बाकी।",
        "कूरियर को एड्रेस वेरिफिकेशन फीस ₹{amount} चाहिए।",
        "पैकेज सीज़। ₹{amount} भरकर छुड़वाएं।",
        "डिलीवरी पार्टनर डिलीवर नहीं कर पाया। ₹{amount} चार्ज भरें।",
        "पार्सल इंस्पेक्शन के लिए फ्लैग। ₹{amount} फीस भरें।",
        "इम्पोर्ट ड्यूटी बाकी: ₹{amount} भरें।",
        "कूरियर वापस! ₹{amount} हैंडलिंग फीस भरें।",
    ],
    "government_impersonation": [
        "सरकार कोविड राहत ₹{amount} दे रही है। आधार और OTP से रजिस्टर करें।",
        "पीएम किसान योजना: ₹{amount} लाभ क्लेम करें। बैंक डिटेल्स भेजें।",
        "गैस सब्सिडी ₹{amount} क्रेडिट। OTP शेयर करके प्राप्त करें।",
        "PMAY हाउसिंग सब्सिडी: ₹{amount} पाएं। आधार से अप्लाई करें।",
        "मुफ्त राशन योजना: लाभ के लिए रजिस्टर करें।",
        "आयुष्मान भारत: ₹{amount} हेल्थ बेनिफिट क्लेम करें।",
        "LPG रिफंड ₹{amount} पेंडिंग। OTP भेजें।",
        "सरकारी नौकरी! ₹{amount} रजिस्ट्रेशन फीस भरें।",
        "मनरेगा पेमेंट ₹{amount} पेंडिंग। बैंक वेरिफाई करें।",
        "पेंशन योजना: ₹{amount}/माह पाएं। अभी रजिस्टर करें।",
    ],
}

SCAM_TEMPLATES_HINGLISH = {
    "lottery": [
        "Congratulations! Aapne ₹{amount} lakh jeete hain! OTP share karo claim karne ke liye.",
        "Aap lucky winner ho ₹{amount} crore ke! Bank details bhejo prize lene ke liye.",
        "Winner! Aapko ₹{amount} lakh cash prize mila hai. Abhi call karo.",
        "Dear customer, aapne ₹{amount} lakh lottery jeeti hai. OTP se verify karo.",
        "Badhai ho! Aapka number ₹{amount} crore mega draw mein select hua.",
        "Aapne iPhone 15 jeeta! Claim karne ke liye link pe click karo.",
        "Winner! Aapko ₹{amount} lakh mile hain. Bank account bhejo.",
        "Aapka number ₹{amount} lakh lottery mein chuna gaya. Documents bhejo.",
        "Jackpot! Aapne ₹{amount} crore jeete. Is number pe call karo.",
        "Winner announcement! Aapko ₹{amount} lakh ka prize mila hai.",
    ],
    "bank_fraud": [
        "Aapka bank account 24 hours mein block ho jayega. Verify karne ke liye ₹{amount} bhejo.",
        "Alert: Account pe suspicious activity. OTP share karke secure karo.",
        "Dear customer, aapka KYC incomplete hai. Account suspend hone se pehle update karo.",
        "Aapka debit card suspend hai. Turant {phone} pe call karo.",
        "Urgent: Aapka account hack hua hai. Identity verify karne ke liye OTP bhejo.",
        "Aapke {bank} account ko immediate verification chahiye.",
        "Security alert! Unknown login attempt. OTP se confirm karo.",
        "Suspicious activity ke kaaran credit card block. Abhi call karo.",
        "Aapka PAN multiple accounts se linked hai. Turant update karo.",
        "Account blocked! Unblock karne ke liye ₹{amount} bhejo: scammer@paytm",
    ],
    "police_threat": [
        "Yeh police hai. Aap investigation mein ho. ₹{amount} fine turant bharo.",
        "Cyber crime alert: Aapka Aadhaar illegal activity se linked hai. Penalty bharo.",
        "Money laundering case mein aapka naam. Arrest se bachne ke liye ₹{amount} bhejo.",
        "CBI notice: Aap crime mein involved. ₹{amount} bharo ya aaj arrest.",
        "Police warning: Warrant issued. ₹{amount} penalty turant clear karo.",
        "ED investigation: Bank accounts freeze. ₹{amount} bhar ke release karao.",
        "Court order: Turant hazir ho ya ₹{amount} fine bharo.",
        "Cyber cell: Aapka mobile fraud mein use. ₹{amount} penalty bharo.",
        "Yeh Income Tax department hai. ₹{amount} pending tax bharo.",
        "Legal notice: Case filed. ₹{amount} mein settlement karo.",
    ],
    "phishing": [
        "Account verify karne ke liye click karo: http://fake-verify.com",
        "Aapka password aaj expire ho raha hai. Abhi update karo.",
        "Identity confirm karne ke liye click karo.",
        "Action required: Account verify karo.",
        "Session expire. Phir se login karo.",
        "KYC update karne ke liye link pe click karo.",
        "Refund claim karne ke liye click karo.",
        "Prize wait kar raha hai! Click karo.",
        "Mobile verify karo.",
        "Registration complete karo.",
    ],
    "courier_fraud": [
        "Aapka parcel customs mein stuck hai. ₹{amount} clearance fee bharo.",
        "Delivery fail! ₹{amount} bhar ke reschedule karo.",
        "Package mein prohibited items. ₹{amount} fine bharo.",
        "Customs hold: International parcel pe ₹{amount} duty pending.",
        "Courier ko address verification fee ₹{amount} chahiye.",
        "Package seize. ₹{amount} bhar ke release karao.",
        "Delivery partner deliver nahi kar paya. ₹{amount} charges bharo.",
        "Parcel inspection ke liye flag. ₹{amount} fee bharo.",
        "Import duty pending: ₹{amount} bharo.",
        "Courier wapas! ₹{amount} handling fee bharo.",
    ],
    "government_impersonation": [
        "Government COVID relief ₹{amount} de rahi hai. Aadhaar aur OTP se register karo.",
        "PM Kisan Yojana: ₹{amount} benefit claim karo. Bank details bhejo.",
        "Gas subsidy ₹{amount} credit. OTP share karke receive karo.",
        "PMAY housing subsidy: ₹{amount} pao. Aadhaar se apply karo.",
        "Free ration scheme: Benefits ke liye register karo.",
        "Ayushman Bharat: ₹{amount} health benefit claim karo.",
        "LPG refund ₹{amount} pending. OTP bhejo.",
        "Government job vacancy! ₹{amount} registration fee bharo.",
        "MNREGA payment ₹{amount} pending. Bank verify karo.",
        "Pension scheme: ₹{amount}/month pao. Abhi register karo.",
    ],
}


# =============================================================================
# LEGITIMATE MESSAGE TEMPLATES
# =============================================================================

LEGIT_TEMPLATES_EN = [
    "Hi! How are you doing? Let's meet for coffee this weekend if you're free.",
    "Your order #{order_id} has been shipped and will arrive by tomorrow.",
    "Reminder: Your dentist appointment is scheduled for tomorrow at {time}.",
    "Thanks for your payment. Receipt has been sent to your email.",
    "Happy birthday! Wishing you a wonderful day and year ahead.",
    "Meeting rescheduled to Monday at {time}. Please confirm your availability.",
    "The weather is lovely today. Let's go for a walk in the evening.",
    "Can you please send me the document we discussed yesterday?",
    "Thank you for your feedback. We appreciate your valuable input.",
    "See you at the party tonight! Don't forget to bring snacks.",
    "Your booking for {destination} is confirmed. Ticket attached.",
    "Please find the invoice attached for your reference.",
    "Happy to help with any questions you might have.",
    "The project deadline has been extended to next Friday.",
    "Great job on the presentation today! Very impressive work.",
    "Don't forget: Team lunch at {time} today in the cafeteria.",
    "Your subscription has been renewed successfully.",
    "Congratulations on your promotion! Well deserved.",
    "Can we schedule a call for tomorrow at {time}?",
    "The meeting notes have been shared with all participants.",
    "Your feedback survey has been submitted. Thank you!",
    "Looking forward to seeing you at the conference.",
    "The report is ready for your review. Please check.",
    "Your refund of ₹{amount} has been processed successfully.",
    "Reminder: Pay electricity bill before due date.",
    "Your OTP for {bank} is 123456. Valid for 5 minutes.",
    "Thank you for shopping with us. Order confirmed.",
    "Your train ticket PNR: {order_id} is confirmed.",
    "Flight booking confirmed for {destination}. Check-in opens soon.",
    "Your Swiggy order is out for delivery. Arriving in 30 mins.",
    "Amazon delivery: Package arriving today between {time}-{time2}.",
    "Your Flipkart order has been delivered. Rate your experience.",
    "Uber ride completed. Total fare: ₹{amount}. Rate your driver.",
    "Your Ola cab is arriving in 5 minutes. Car number: DL1234.",
    "Zomato order placed successfully. Estimated time: 40 mins.",
    "Your Paytm recharge of ₹{amount} was successful.",
    "PhonePe: ₹{amount} sent to {name} successfully.",
    "Google Pay: Received ₹{amount} from {name}.",
    "Your Netflix subscription is active. Enjoy streaming!",
    "Spotify Premium renewed. Continue enjoying ad-free music.",
]

LEGIT_TEMPLATES_HI = [
    "नमस्ते! कैसे हो? इस वीकेंड कॉफी के लिए मिलते हैं अगर फ्री हो।",
    "आपका ऑर्डर #{order_id} शिप हो गया है और कल तक पहुंच जाएगा।",
    "याद दिलाना: कल आपकी डेंटिस्ट अपॉइंटमेंट है {time} बजे।",
    "भुगतान के लिए धन्यवाद। रसीद ईमेल पर भेज दी गई है।",
    "जन्मदिन की शुभकामनाएं! आपका दिन और साल शानदार हो।",
    "मीटिंग सोमवार {time} बजे रीशेड्यूल हुई। कन्फर्म करें।",
    "आज मौसम बहुत अच्छा है। शाम को वॉक पर चलें।",
    "कल की चर्चा वाला डॉक्यूमेंट भेज सकते हो?",
    "फीडबैक के लिए धन्यवाद। आपकी राय हमारे लिए महत्वपूर्ण है।",
    "आज रात पार्टी में मिलते हैं! स्नैक्स लाना मत भूलना।",
    "{destination} की बुकिंग कन्फर्म। टिकट अटैच है।",
    "रेफरेंस के लिए इनवॉइस अटैच है।",
    "किसी भी सवाल में मदद करने को तैयार हूं।",
    "प्रोजेक्ट डेडलाइन अगले शुक्रवार तक बढ़ाई गई।",
    "आज की प्रेजेंटेशन बहुत अच्छी थी! बढ़िया काम।",
    "याद रखो: टीम लंच आज {time} बजे कैफेटेरिया में।",
    "आपकी सब्सक्रिप्शन सफलतापूर्वक रिन्यू हो गई।",
    "प्रमोशन की बधाई! पूरी तरह से लायक।",
    "कल {time} बजे कॉल शेड्यूल कर सकते हैं?",
    "मीटिंग नोट्स सभी को शेयर कर दिए गए।",
    "फीडबैक सर्वे सबमिट हो गया। धन्यवाद!",
    "कॉन्फ्रेंस में मिलने का इंतज़ार है।",
    "रिपोर्ट रिव्यू के लिए तैयार है। चेक करें।",
    "₹{amount} का रिफंड सफलतापूर्वक प्रोसेस हुआ।",
    "याद दिलाना: बिजली बिल ड्यू डेट से पहले भरें।",
    "{bank} के लिए OTP 123456 है। 5 मिनट के लिए वैलिड।",
    "खरीदारी के लिए धन्यवाद। ऑर्डर कन्फर्म।",
    "ट्रेन टिकट PNR: {order_id} कन्फर्म है।",
    "फ्लाइट बुकिंग कन्फर्म। जल्द ही चेक-इन शुरू होगा।",
    "Swiggy ऑर्डर डिलीवरी के लिए निकला। 30 मिनट में आ रहा।",
    "Amazon डिलीवरी: पैकेज आज {time}-{time2} बीच आएगा।",
    "Flipkart ऑर्डर डिलीवर हो गया। अनुभव रेट करें।",
    "Uber राइड पूरी। कुल किराया: ₹{amount}। ड्राइवर रेट करें।",
    "Ola कैब 5 मिनट में आ रही। कार नंबर: DL1234।",
    "Zomato ऑर्डर सफलतापूर्वक प्लेस। अनुमानित समय: 40 मिनट।",
    "Paytm रिचार्ज ₹{amount} सफल।",
    "PhonePe: ₹{amount} सफलतापूर्वक {name} को भेजे।",
    "Google Pay: {name} से ₹{amount} मिले।",
    "Netflix सब्सक्रिप्शन एक्टिव। स्ट्रीमिंग का आनंद लें!",
    "Spotify Premium रिन्यू। एड-फ्री म्यूज़िक का मज़ा लें।",
]

LEGIT_TEMPLATES_HINGLISH = [
    "Hi! Kaise ho? Weekend pe coffee ke liye milte hain agar free ho.",
    "Aapka order #{order_id} ship ho gaya hai. Kal tak aa jayega.",
    "Reminder: Kal dentist appointment hai {time} baje.",
    "Payment ke liye thanks. Receipt email pe bhej di.",
    "Happy birthday! Bahut bahut badhai.",
    "Meeting Monday {time} baje reschedule hui. Please confirm karo.",
    "Aaj weather bahut accha hai. Evening mein walk pe chalein?",
    "Kal wala document bhej sakte ho?",
    "Feedback ke liye thanks. Appreciate karte hain.",
    "Aaj party mein milte hain! Snacks lana mat bhoolna.",
    "{destination} ki booking confirm. Ticket attach hai.",
    "Invoice attach hai reference ke liye.",
    "Koi bhi question ho, help karne ko ready hoon.",
    "Project deadline next Friday tak extend hui.",
    "Aaj ki presentation bahut achi thi! Great job.",
    "Yaad rakhna: Team lunch {time} baje cafeteria mein.",
    "Subscription successfully renew ho gayi.",
    "Promotion ki badhai! Well deserved.",
    "Kal {time} baje call schedule kar sakte hain?",
    "Meeting notes sabko share kar diye.",
    "Feedback survey submit ho gaya. Thanks!",
    "Conference mein milne ka wait kar raha hoon.",
    "Report review ke liye ready hai. Check karo.",
    "₹{amount} refund successfully process hua.",
    "Reminder: Electricity bill due date se pehle bharo.",
    "{bank} ka OTP 123456 hai. 5 minutes ke liye valid.",
    "Shopping ke liye thanks. Order confirmed.",
    "Train ticket PNR: {order_id} confirmed hai.",
    "Flight booking confirm. Check-in jaldi shuru hoga.",
    "Swiggy order delivery ke liye nikla. 30 mins mein aa raha.",
    "Amazon delivery: Package aaj {time}-{time2} beech aayega.",
    "Flipkart order deliver ho gaya. Experience rate karo.",
    "Uber ride complete. Total fare: ₹{amount}. Driver rate karo.",
    "Ola cab 5 minutes mein aa rahi. Car number: DL1234.",
    "Zomato order successfully placed. Estimated time: 40 mins.",
    "Paytm recharge ₹{amount} successful.",
    "PhonePe: ₹{amount} successfully {name} ko sent.",
    "Google Pay: {name} se ₹{amount} receive kiye.",
    "Netflix subscription active. Streaming enjoy karo!",
    "Spotify Premium renewed. Ad-free music ka mazaa lo.",
]


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_random_amount() -> int:
    """Generate random money amount."""
    return random.choice([5, 10, 15, 20, 25, 50, 100, 500, 1000, 5000, 10000])


def get_random_phone() -> str:
    """Generate random phone number."""
    return f"98765432{random.randint(10, 99)}"


def get_random_bank() -> str:
    """Generate random bank name."""
    return random.choice(["SBI", "HDFC", "ICICI", "Axis", "Kotak", "PNB", "BOB"])


def get_random_order_id() -> str:
    """Generate random order ID."""
    return f"{random.randint(100000000, 999999999)}"


def get_random_time() -> str:
    """Generate random time."""
    hour = random.randint(8, 20)
    return f"{hour}:{'00' if random.random() > 0.5 else '30'}"


def get_random_destination() -> str:
    """Generate random destination."""
    return random.choice(["Delhi", "Mumbai", "Bangalore", "Chennai", "Kolkata", "Hyderabad", "Pune", "Jaipur"])


def get_random_name() -> str:
    """Generate random name."""
    return random.choice(["Rahul", "Priya", "Amit", "Neha", "Vijay", "Anjali", "Raj", "Pooja"])


def fill_template(template: str) -> str:
    """Fill template with random values."""
    return template.format(
        amount=get_random_amount(),
        phone=get_random_phone(),
        bank=get_random_bank(),
        order_id=get_random_order_id(),
        time=get_random_time(),
        time2=get_random_time(),
        destination=get_random_destination(),
        name=get_random_name(),
    )


def get_indicators(message: str, language: str) -> List[str]:
    """Extract scam indicators from message."""
    indicators = []
    
    # English indicators (expanded list covering all scam types)
    en_keywords = [
        # Lottery/Prize
        "won", "winner", "prize", "lottery", "jackpot", "congratulations", "lucky", "draw",
        "claim", "reward", "selected", "cash", "crore", "lakh",
        # Bank fraud
        "otp", "bank", "blocked", "suspended", "kyc", "verify", "account", "card",
        "credit", "debit", "compromised", "security", "alert", "pan", "aadhaar",
        # Urgency
        "urgent", "immediately", "turant", "now", "today", "expire", "hours",
        # Threats
        "police", "arrest", "fine", "penalty", "investigation", "court", "warrant",
        "cbi", "cyber", "crime", "legal", "prosecution", "frozen", "ed",
        # Phishing
        "click", "link", "http", "login", "password", "update", "confirm",
        # Courier
        "customs", "parcel", "package", "delivery", "stuck", "clearance", "duty",
        "courier", "seized", "inspection",
        # Government
        "government", "subsidy", "relief", "scheme", "benefit", "pmay", "yojana",
        "registration", "pension", "ration",
        # Action words
        "send", "share", "transfer", "pay", "call", "contact", "@paytm", "@ybl",
        "@phonepe", "upi",
    ]
    
    # Hindi indicators (expanded list)
    hi_keywords = [
        # Lottery/Prize
        "जीत", "विजेता", "इनाम", "लॉटरी", "बधाई", "लाख", "करोड़", "पुरस्कार",
        # Bank fraud
        "ब्लॉक", "सस्पेंड", "खाता", "बैंक", "कार्ड",
        # Urgency
        "तुरंत", "अभी", "फौरन",
        # Threats
        "पुलिस", "गिरफ्तार", "जुर्माना", "जांच", "वारंट", "कोर्ट", "कानूनी",
        # Phishing
        "क्लिक", "लिंक", "वेरिफाई", "अपडेट",
        # Courier
        "कस्टम्स", "पार्सल", "डिलीवरी", "फंसा",
        # Government
        "सरकार", "सब्सिडी", "योजना", "राहत", "लाभ", "पेंशन", "राशन",
        # Action words
        "भेजें", "शेयर", "भरें", "कॉल",
    ]
    
    # Hinglish romanized indicators
    hinglish_keywords = [
        "jeeta", "jeete", "inaam", "jaldi", "turant", "bhejo", "bharo",
        "block", "suspend", "claim", "prize", "lakh", "crore",
    ]
    
    message_lower = message.lower()
    
    for kw in en_keywords:
        if kw in message_lower:
            indicators.append(kw)
    
    for kw in hi_keywords:
        if kw in message:
            indicators.append(kw)
    
    for kw in hinglish_keywords:
        if kw in message_lower:
            indicators.append(kw)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_indicators = []
    for ind in indicators:
        if ind.lower() not in seen:
            seen.add(ind.lower())
            unique_indicators.append(ind)
    
    return unique_indicators[:5]  # Limit to 5 indicators


def generate_sample(
    sample_id: str,
    message: str,
    language: str,
    label: str,
    scam_type: Optional[str],
    difficulty: str,
    timestamp: datetime,
) -> Dict:
    """Generate a single dataset sample."""
    indicators = get_indicators(message, language) if label == "scam" else []
    
    return {
        "id": sample_id,
        "message": message,
        "language": language,
        "label": label,
        "confidence": 1.0 if difficulty == "easy" else (0.9 if difficulty == "medium" else 0.7),
        "scam_type": scam_type,
        "indicators": indicators,
        "metadata": {
            "source": "synthetic",
            "annotator": "ai",
            "annotation_date": timestamp.isoformat() + "Z",
            "difficulty": difficulty,
        }
    }


def generate_scam_samples(count: int, language: str) -> List[Dict]:
    """Generate scam samples for a specific language."""
    samples = []
    
    # Select templates based on language
    if language == "en":
        templates = SCAM_TEMPLATES_EN
    elif language == "hi":
        templates = SCAM_TEMPLATES_HI
    else:
        templates = SCAM_TEMPLATES_HINGLISH
    
    # Calculate per-type counts
    type_counts = {t: int(count * r) for t, r in SCAM_TYPES.items()}
    remaining = count - sum(type_counts.values())
    if remaining > 0:
        type_counts["lottery"] += remaining
    
    sample_idx = 0
    for scam_type, type_count in type_counts.items():
        type_templates = templates.get(scam_type, [])
        if not type_templates:
            continue
        
        for i in range(type_count):
            template = random.choice(type_templates)
            message = fill_template(template)
            
            difficulty = random.choices(
                ["easy", "medium", "hard"],
                weights=[0.5, 0.35, 0.15],
                k=1
            )[0]
            
            sample_id = f"scam_{language}_{sample_idx:04d}"
            timestamp = BASE_DATE + timedelta(seconds=sample_idx * 30)
            
            sample = generate_sample(
                sample_id=sample_id,
                message=message,
                language=language,
                label="scam",
                scam_type=scam_type,
                difficulty=difficulty,
                timestamp=timestamp,
            )
            samples.append(sample)
            sample_idx += 1
    
    return samples


def generate_legit_samples(count: int, language: str) -> List[Dict]:
    """Generate legitimate samples for a specific language."""
    samples = []
    
    # Select templates based on language
    if language == "en":
        templates = LEGIT_TEMPLATES_EN
    elif language == "hi":
        templates = LEGIT_TEMPLATES_HI
    else:
        templates = LEGIT_TEMPLATES_HINGLISH
    
    for i in range(count):
        template = random.choice(templates)
        message = fill_template(template)
        
        difficulty = random.choices(
            ["easy", "medium", "hard"],
            weights=[0.6, 0.3, 0.1],
            k=1
        )[0]
        
        sample_id = f"legit_{language}_{i:04d}"
        timestamp = BASE_DATE + timedelta(hours=1, seconds=i * 30)
        
        sample = generate_sample(
            sample_id=sample_id,
            message=message,
            language=language,
            label="legitimate",
            scam_type=None,
            difficulty=difficulty,
            timestamp=timestamp,
        )
        samples.append(sample)
    
    return samples


def generate_dataset() -> List[Dict]:
    """Generate complete dataset."""
    all_samples = []
    
    # Calculate counts
    scam_count = int(TOTAL_SAMPLES * SCAM_RATIO)
    legit_count = TOTAL_SAMPLES - scam_count
    
    # Scam samples by language
    scam_en = int(scam_count * EN_RATIO)
    scam_hi = int(scam_count * HI_RATIO)
    scam_hinglish = scam_count - scam_en - scam_hi
    
    # Legitimate samples by language
    legit_en = int(legit_count * EN_RATIO)
    legit_hi = int(legit_count * HI_RATIO)
    legit_hinglish = legit_count - legit_en - legit_hi
    
    print(f"Generating dataset with {TOTAL_SAMPLES} samples...")
    print(f"  Scam: {scam_count} ({scam_en} EN, {scam_hi} HI, {scam_hinglish} Hinglish)")
    print(f"  Legit: {legit_count} ({legit_en} EN, {legit_hi} HI, {legit_hinglish} Hinglish)")
    
    # Generate scam samples
    all_samples.extend(generate_scam_samples(scam_en, "en"))
    all_samples.extend(generate_scam_samples(scam_hi, "hi"))
    all_samples.extend(generate_scam_samples(scam_hinglish, "hinglish"))
    
    # Generate legitimate samples
    all_samples.extend(generate_legit_samples(legit_en, "en"))
    all_samples.extend(generate_legit_samples(legit_hi, "hi"))
    all_samples.extend(generate_legit_samples(legit_hinglish, "hinglish"))
    
    # Shuffle
    random.shuffle(all_samples)
    
    return all_samples


def validate_dataset(samples: List[Dict]) -> Dict:
    """Validate dataset against acceptance criteria."""
    stats = {
        "total": len(samples),
        "scam": sum(1 for s in samples if s["label"] == "scam"),
        "legitimate": sum(1 for s in samples if s["label"] == "legitimate"),
        "en": sum(1 for s in samples if s["language"] == "en"),
        "hi": sum(1 for s in samples if s["language"] == "hi"),
        "hinglish": sum(1 for s in samples if s["language"] == "hinglish"),
    }
    
    stats["scam_ratio"] = stats["scam"] / stats["total"]
    stats["en_ratio"] = stats["en"] / stats["total"]
    stats["hi_ratio"] = stats["hi"] / stats["total"]
    stats["hinglish_ratio"] = stats["hinglish"] / stats["total"]
    
    # Check acceptance criteria
    stats["passes_total"] = stats["total"] >= 1000
    stats["passes_scam_ratio"] = 0.55 <= stats["scam_ratio"] <= 0.65
    stats["passes_en_ratio"] = 0.45 <= stats["en_ratio"] <= 0.55
    stats["passes_hi_ratio"] = 0.35 <= stats["hi_ratio"] <= 0.45
    stats["passes_hinglish_ratio"] = 0.05 <= stats["hinglish_ratio"] <= 0.15
    
    stats["all_pass"] = all([
        stats["passes_total"],
        stats["passes_scam_ratio"],
        stats["passes_en_ratio"],
        stats["passes_hi_ratio"],
        stats["passes_hinglish_ratio"],
    ])
    
    return stats


def save_dataset(samples: List[Dict], filepath: str) -> None:
    """Save dataset to JSONL file."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    with open(filepath, "w", encoding="utf-8") as f:
        for sample in samples:
            f.write(json.dumps(sample, ensure_ascii=False) + "\n")


def main():
    """Main entry point."""
    print("=" * 60)
    print("ScamShield AI - Dataset Generation")
    print("=" * 60)
    print()
    
    # Set seed for reproducibility
    random.seed(42)
    
    # Generate dataset
    samples = generate_dataset()
    
    # Validate
    print("\nValidating dataset...")
    stats = validate_dataset(samples)
    
    print(f"\n--- Dataset Statistics ---")
    print(f"Total samples: {stats['total']}")
    print(f"Scam: {stats['scam']} ({stats['scam_ratio']:.1%})")
    print(f"Legitimate: {stats['legitimate']} ({1-stats['scam_ratio']:.1%})")
    print(f"English: {stats['en']} ({stats['en_ratio']:.1%})")
    print(f"Hindi: {stats['hi']} ({stats['hi_ratio']:.1%})")
    print(f"Hinglish: {stats['hinglish']} ({stats['hinglish_ratio']:.1%})")
    
    print(f"\n--- Acceptance Criteria ---")
    print(f"1000+ samples: {'PASS' if stats['passes_total'] else 'FAIL'}")
    print(f"60% scam (55-65%): {'PASS' if stats['passes_scam_ratio'] else 'FAIL'}")
    print(f"50% English (45-55%): {'PASS' if stats['passes_en_ratio'] else 'FAIL'}")
    print(f"40% Hindi (35-45%): {'PASS' if stats['passes_hi_ratio'] else 'FAIL'}")
    print(f"10% Hinglish (5-15%): {'PASS' if stats['passes_hinglish_ratio'] else 'FAIL'}")
    
    # Save
    output_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data",
        "scam_detection_train.jsonl"
    )
    
    save_dataset(samples, output_path)
    print(f"\nDataset saved to: {output_path}")
    
    if stats["all_pass"]:
        print("\n[SUCCESS] All acceptance criteria passed!")
        return 0
    else:
        print("\n[WARNING] Some acceptance criteria not met.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
