'''
Functions to interact with Renshuu API.
Estimate proficiency of user.
Select terms to use in conversation.
'''
import os
import json
from dotenv import load_dotenv
import requests
from typing import Optional

load_dotenv()

RENSHUU_API_KEY = os.getenv('RENSHUU_API_KEY')

LEVELS = ["n5", "n4", "n3", "n2", "n1"]

HEADERS = {
    'Authorization': f'Bearer {RENSHUU_API_KEY}',
    'Content-Type': 'application/json'
}

TYPE_KEYWORDS = [
    (
        "grammar",
        ["grammar"]
    ),
    (
        "vocab",
        ["vocabulary", "vocab", "words"]
    ),
    (
        "kanji",
        ["kanji", "characters"]
    ),
]

SCHEDULE_KEYWORDS = [
    (
        "n5",
        ["n5", "beginner"]
    ),
    (
        "n4",
        ["n4", "pre-intermediate", "preintermediate"]
    ),
    (
        "n3",
        ["n3", "intermediate"]
    ),
    (
        "n2",
        ["n2", "pre-advanced", "preadvanced"]
    ),
    (
        "n1",
        ["n1", "advanced"]
    ),
]

def estimate_level_by_keywords(schedule_name):
    '''
    Estimate level by keywords
    TODO: next time, maybe do this by LLM
    '''
    estimated_level = "n5"
    sched_name_lower = schedule_name.strip().lower()

    for level, keywords in SCHEDULE_KEYWORDS[1:]:
        for keyword in keywords:
            if keyword in sched_name_lower:
                estimated_level = level
                break
        if estimated_level != "n5":
            break

    return estimated_level

def estimate_type_by_keywords(schedule_name):
    estimated_type = None
    sched_name_lower = schedule_name.strip().lower()

    for type_, keywords in TYPE_KEYWORDS:
        for keyword in keywords:
            if keyword in sched_name_lower:
                estimated_type = type_
                break
        if estimated_type is not None:
            break

    return estimated_type

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

def get_schedule_terms(url):
    # TODO
    # NOTE: deal with paged results

    pass

def term_is_studied(term):
    # NOTE: sometimes they don't have "user_data"
        # but sometimes they have "user_data", but 0 "correct_count" and "missed_count"
    pass

def get_focus_terms_from_schedules(
    levels: Optional[list] = ["n5"],
    n_terms: Optional[int] = 5,
    types: Optional[list] = ["vocab", "kanji", "grammar"],
    include_unstudied_terms: Optional[bool] = False,
):
    '''
    Get terms for the Interlocuter and Critic to focus on.
    Gets from the user's schedules.
    Does not get from other sources such as lists.

    Prioritize:
        -In current level
        -Low to Mid mastery
    Sometimes add random terms for review
    '''

    # get schedules
    schedules = requests.get(
        "https://api.renshuu.org/v1/schedule", 
        headers=HEADERS
    ).json()["schedules"]

    # estimate schedule levels from names
    for i, schedule in enumerate(schedules):
        schedules[i]["estimated_level"] = estimate_level_by_keywords(
            schedule["name"]
        )

    # keep only schedules in listed levels
    target_schedules = [s for s in schedules if s["estimated_level"] in levels]

    # get terms in target_schedules
    sched_terms = []
    for schedule in schedules:
        terms_url = "https://api.renshuu.org/v1/schedule/{}/list".format(schedule["id"])


        # TODO: need to deal with paged results here
        terms = get_schedule_terms(terms_url)

        # figure out the type of the terms
        for i, term in enumerate(terms):
            if "onyomi" in term.keys():
                terms["i"]["type"] = "kanji"
                continue
            elif "typeofspeech" in term.keys():
                terms["i"]["type"] = "vocab"
                continue
            elif "title_japanese" in term.keys():
                terms["i"]["type"] = "grammar"
                continue
            else:
                terms["i"]["type"] = None

        sched_terms += terms

    # keep only terms of indicated types
    sched_terms = [t for t in sched_terms if t["type"] in types] 

    # TODO: keep only studied terms if indicated
        # use function term_is_studied above

    # TODO: apply weights based on mastery_perc
        # NOTE: apply separately to each type, to balance for quantity

    # TODO:  weighted random selection 
 
    pass