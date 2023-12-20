from primitives import *
from manager import *
import random

from typing import Callable



CHANCE_CARDS: set[str] = {
    "newborn",
    "earthquake",
    "tax-heaven",
    "disease",
    "emergency-aid",
    "drug",
    "nursing", 
    "quirk-of-fate",
    "inherit-get",
    "inherit-donate",
    "maintenance",
    "healthy",
    "cyber-security-threat",
    "Typhoon",
    "pandemic",
    "fake-news",
    "green-new-deal",
    "voice-phishing",
    "scholarship",
    "catastrophe",
    "fee-exemption",
    "bonus",
    "doubleLotto",
    "insider-trading",
    "traffic-jam",
    "quick-move",
    "traffic-accident",
    "tax-exemption",
    "too-much-electrivity",
    "lawyers-help",
    "soaring-stock-price",
    "plunge-in-stock-price",
    "studying-hard",
    "extinction",
    "trade",
}


TYPHOON_TARGETS = [
    2,4,8,17,26,30,43,48,49,51
]