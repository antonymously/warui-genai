'''
Functions to interact with Renshuu API.
Estimate proficiency of user.
Select terms to use in conversation.
'''
import os
import json
from dotenv import load_dotenv
import requests

load_dotenv()

RENSHUU_API_KEY = os.getenv('RENSHUU_API_KEY')

LEVELS = ["n5", "n4", "n3", "n2", "n1"]

HEADERS = {
    'Authorization': f'Bearer {RENSHUU_API_KEY}',
    'Content-Type': 'application/json'
}

def estimate_proficiency_from_profile(threshold = 0.5):
    '''
    Estimate the users proficiency based on his profile level progress
    Will get the highest level with atleast <threshold> progress
    '''
    profile = requests.get(
        "https://api.renshuu.org/v1/profile", 
        headers=HEADERS
    ).json()

    level_proficiencies = {}
    for level in LEVELS:
        # assume equal importance of sentence, grammar, kanji and vocab
        level_proficiencies[level] = (\
            profile["level_progress_percs"]["vocab"][level]\
            + profile["level_progress_percs"]["kanji"][level]\
            + profile["level_progress_percs"]["grammar"][level]\
            + profile["level_progress_percs"]["sent"][level]\
        )/400

    estimated_level = "n5"
    for level in LEVELS[1:]:
        if level_proficiencies[level] >= threshold:
            estimated_level = level

    return {
        "level_proficiencies": level_proficiencies,
        "estimated_level": estimated_level,
    }

def get_focus_terms():
    '''
    Get terms for the Interlocuter and Critic to focus on.
    Prioritize:
        -In current level
        -Low to Mid mastery
    Sometimes add random terms for review
    '''
    pass