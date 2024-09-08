'''
Functions to interact with Renshuu API.
Estimate proficiency of user.
Select terms to use in conversation.
'''
import os
import json
from copy import copy
from dotenv import load_dotenv
import requests
from typing import Optional
import numpy as np

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

def get_schedule_terms(schedule_id: str):
    # NOTE: deal with paged results

    url = "https://api.renshuu.org/v1/schedule/{}/list".format(schedule_id)

    contents = requests.get(
        url, 
        headers=HEADERS,
    ).json()["contents"]

    n_pages = contents["total_pg"]
    terms = copy(contents["terms"])

    if n_pages <= 1:
        return terms

    for page_num in range(2, n_pages + 1):
        contents = requests.get(
            url, 
            headers=HEADERS,
            params = {
                "pg": page_num
            }
        ).json()["contents"]
        terms += copy(contents["terms"])
    return terms

def term_is_studied(term):
    # NOTE: sometimes they don't have "user_data"
        # but sometimes they have "user_data", but 0 "correct_count" and "missed_count"
    if "user_data" not in term:
        return False

    if term["user_data"]["correct_count"] + term["user_data"]["missed_count"] <= 0:
        return False

    return True

def get_term_type(term):
    # figure out the type of the term based on structure
    # sadly, it is not indicated
    if "onyomi" in term:
        return "kanji"
    elif "typeofspeech" in term:
        return "vocab"
    elif "title_japanese" in term:
        return "grammar"
    else:
        return None

def get_terms_from_schedules(
    levels: Optional[list] = ["n5"],
    types: Optional[list] = ["vocab", "kanji", "grammar"],
    include_unstudied_terms: Optional[bool] = False,
):
    '''
    Get terms for the Interlocuter and Critic to focus on.
    Gets from the user's schedules.
    Does not get from other sources such as lists.
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
    for schedule in target_schedules:

        # need to deal with paged results here
        terms = get_schedule_terms(schedule["id"])

        term_types = [get_term_type(t) for t in terms]

        for i, term_type in enumerate(term_types):
            terms[i]["type"] = term_type

        sched_terms += copy(terms)

    # keep only terms of indicated types
    sched_terms = [t for t in sched_terms if t["type"] in types] 
    # keep only studied terms if indicated
        # use function term_is_studied above
    if not include_unstudied_terms:
        sched_terms = [t for t in sched_terms if term_is_studied(t)]

    return sched_terms

def get_mastery(term):
    mastery_str = term.get("user_data", {}).get("mastery_avg_perc", 0)

    if mastery_str == '':
        return 0
    else:
        return int(mastery_str)

def get_inverse_mastery_weights(
    terms, 
    normalize: Optional[bool] = True,
    min_raw_weight: Optional[int] = 30,
):
    weights = [max(100 - get_mastery(t), 0) + min_raw_weight for t in terms]
    
    # adjust so that each type has equal sum of weights
    term_types = [t["type"] for t in terms]
    unique_types = set(term_types)
    type_sum_weights = {}
    for term_type in term_types:
        type_sum_weights[term_type] = sum([w for i, w in enumerate(weights) if term_types[i] == term_type])
    
    weights = [w/type_sum_weights[term_types[i]] for i, w in enumerate(weights)]

    if normalize:
        sum_weights = sum(weights)
        weights = [w/sum_weights for w in weights]

    return weights

def get_focus_terms(
    terms: list,
    n_terms: Optional[int] = 5,
    seed: Optional[int] = None,
):
    '''
    Prioritize:
        -In current level
        -Low to Mid mastery

    Sometimes add random terms for review?
    '''
    weights = get_inverse_mastery_weights(terms)

    if seed is not None:
        np.random.seed(seed)

    focus_terms = np.random.choice(
        terms,
        size = n_terms,
        replace = False,
        p = weights,
    )

    return list(focus_terms)

