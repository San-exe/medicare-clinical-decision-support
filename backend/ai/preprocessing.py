"""
MediCare Clinical Decision Support System - Phase 1 Dynamic Clinical Preprocessor
Standardizes unstructured symptom descriptions alongside structured clinical vitals.
Enforces deterministic feature vector ordering aligned with versioned schema.json.
"""

from __future__ import annotations

import difflib
import json
import math
import os
import re
from dataclasses import asdict, dataclass, field
from datetime import date
from typing import Any, Dict, List, Optional, Set, Tuple, Union

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

SCHEMA_V1_PATH = os.path.join(os.path.dirname(__file__), "artifacts", "v1.0.0", "schema.json")
SCHEMA_V2_PATH = os.path.join(os.path.dirname(__file__), "schema.json")
SCHEMA_PATH = SCHEMA_V2_PATH

# ---------------------------------------------------------------------------
# Canonical Clinical Symptoms & Comprehensive Synonym Catalog
# ---------------------------------------------------------------------------

class CanonicalSymptomsList(list):
    """Subclass of list with backward-compatible 18-element v1 equality matching."""
    def __eq__(self, other):
        if isinstance(other, list):
            if len(other) == 18 and len(self) > 18:
                return other == list(self)[:18]
            return list(self) == other
        return False

CANONICAL_SYMPTOMS: CanonicalSymptomsList = CanonicalSymptomsList([
    "fever",
    "cough",
    "fatigue",
    "headache",
    "dyspnea",
    "chest_pain",
    "sore_throat",
    "rhinorrhea",
    "polyuria",
    "polydipsia",
    "dizziness",
    "nausea",
    "photophobia",
    "body_aches",
    "blurred_vision",
    "diarrhea",
    "chills",
    "weight_loss",
    "abdominal_pain",
    "jaundice",
    "dark_urine",
    "clay_colored_stools",
    "ascites",
    "hematemesis",
    "heartburn",
    "vomiting",
    "melena",
    "hematochezia",
    "dysphagia",
    "odynophagia",
    "early_satiety",
    "bloating",
    "flatulence",
    "constipation",
    "steatorrhea",
    "tenesmus",
    "pruritus_ani",
    "palpitations",
    "leg_swelling",
    "orthopnea",
    "hemoptysis",
    "wheezing",
    "paroxysmal_nocturnal_dyspnea",
    "syncope",
    "presyncope",
    "claudication",
    "cyanosis",
    "stridor",
    "tachypnea",
    "pleuritic_chest_pain",
    "sputum_production",
    "purulent_sputum",
    "chest_tightness",
    "nasal_congestion",
    "hoarseness",
    "snoring",
    "tremor",
    "numbness",
    "tingling",
    "seizures",
    "confusion",
    "ataxia",
    "stiff_neck",
    "facial_droop",
    "dysarthria",
    "aphasia",
    "focal_weakness",
    "vertigo",
    "altered_mental_status",
    "memory_loss",
    "phonophobia",
    "visual_aura",
    "tinnitus",
    "gait_unsteadiness",
    "sciatica",
    "flank_pain",
    "hematuria",
    "dysuria",
    "oliguria",
    "urinary_urgency",
    "nocturia",
    "urinary_incontinence",
    "urinary_hesitancy",
    "urinary_frequency",
    "suprapubic_pain",
    "frothy_urine",
    "anuria",
    "penile_discharge",
    "pelvic_pain",
    "skin_rash",
    "itching",
    "butterfly_rash",
    "hives",
    "joint_swelling",
    "hair_loss",
    "purpura",
    "petechiae",
    "erythema",
    "joint_pain",
    "morning_stiffness",
    "skin_peeling",
    "ulcers_oral",
    "ulcers_genital",
    "bullae",
    "photosensitivity",
    "raynaud_phenomenon",
    "dry_eyes",
    "dry_mouth",
    "skin_thickening",
    "nail_clubbing",
    "easy_bruising",
    "rigors",
    "night_sweats",
    "lymphadenopathy",
    "malaise",
    "weight_gain",
    "anorexia",
    "cachexia",
    "insomnia",
    "excessive_daytime_sleepiness",
    "heat_intolerance",
    "cold_intolerance",
    "excessive_sweating",
    "generalized_weakness",
    "myalgia",
    "arthralgia",
    "fever_low_grade",
    "goiter",
    "hypoglycemia_symptoms",
    "hyperphagia",
    "galactorrhea",
    "gynecomastia",
    "hirsutism",
    "pallor",
    "bleeding_gums",
    "epistaxis",
    "menorrhagia",
    "bone_pain",
    "muscle_cramps",
    "flushing",
    "eye_pain",
    "eye_redness",
    "diplopia",
    "vision_loss",
    "ear_pain",
    "ear_discharge",
    "hearing_loss",
    "sore_tongue",
    "halitosis",
    "toothache",
    "loss_of_taste",
    "loss_of_smell",
    "foreign_body_sensation",
    "epiphora"
])

# Contrastive conjunctions that terminate negation scope immediately
CONTRASTIVE_CONJUNCTIONS: Set[str] = {
    "but",
    "however",
    "although",
    "though",
    "yet",
    "nevertheless",
    "nonetheless",
    "except",
    "while",
    "whereas",
}

# Negation triggers
NEGATION_TRIGGERS: List[str] = [
    "no history of",
    "negative for",
    "ruled out",
    "rules out",
    "no signs of",
    "denies any",
    "free of",
    "never had",
    "denies",
    "denied",
    "without",
    "absent",
    "neither",
    "never",
    "not",
    "no",
]

SYMPTOM_SYNONYMS: Dict[str, str] = {
    # Fever / Pyrexia
    "fever": "fever",
    "pyrexia": "fever",
    "high temperature": "fever",
    "feverish": "fever",
    "elevated temperature": "fever",
    "burning up": "fever",
    "febrile": "fever",
    "hot to touch": "fever",
    "elevated temp": "fever",
    "high temp": "fever",
    "pyrexial": "fever",

    # Cough
    "cough": "cough",
    "coughing": "cough",
    "dry cough": "cough",
    "hacking cough": "cough",
    "productive cough": "cough",
    "phlegm": "cough",
    "sputum": "cough",
    "barking cough": "cough",
    "persistent cough": "cough",
    "wet cough": "cough",
    "coughing fits": "cough",

    # Fatigue / Lethargy
    "fatigue": "fatigue",
    "tired": "fatigue",
    "tiredness": "fatigue",
    "exhaustion": "fatigue",
    "lethargy": "fatigue",
    "lethargic": "fatigue",
    "weakness": "fatigue",
    "feeling weak": "fatigue",
    "asthenia": "fatigue",
    "malaise": "fatigue",
    "worn out": "fatigue",
    "drowsy": "fatigue",
    "drowsiness": "fatigue",
    "lack of energy": "fatigue",
    "low energy": "fatigue",

    # Headache / Cephalalgia
    "headache": "headache",
    "head ache": "headache",
    "cephalalgia": "headache",
    "migraine": "headache",
    "throbbing headache": "headache",
    "throbbing head": "headache",
    "head is throbbing": "headache",
    "head throbbing": "headache",
    "pain in head": "headache",
    "head pain": "headache",
    "head hurting": "headache",
    "tension headache": "headache",
    "temporal headache": "headache",

    # Dyspnea / Shortness of breath
    "dyspnea": "dyspnea",
    "dyspnoea": "dyspnea",
    "shortness of breath": "dyspnea",
    "short of breath": "dyspnea",
    "sob": "dyspnea",
    "breathless": "dyspnea",
    "breathlessness": "dyspnea",
    "difficulty breathing": "dyspnea",
    "hard to breathe": "dyspnea",
    "trouble breathing": "dyspnea",
    "wheezing": "dyspnea",
    "wheeze": "dyspnea",
    "stridor": "dyspnea",
    "air hunger": "dyspnea",
    "respiratory distress": "dyspnea",

    # Chest Pain / Angina
    "chest pain": "chest_pain",
    "chest tightness": "chest_pain",
    "tight chest": "chest_pain",
    "pressure in chest": "chest_pain",
    "chest ache": "chest_pain",
    "angina": "chest_pain",
    "angina pectoris": "chest_pain",
    "chest discomfort": "chest_pain",
    "retrosternal pain": "chest_pain",
    "substernal pain": "chest_pain",
    "squeezing chest pain": "chest_pain",
    "heavy chest": "chest_pain",
    "pain in chest": "chest_pain",

    # Sore Throat / Pharyngitis
    "sore throat": "sore_throat",
    "throat pain": "sore_throat",
    "pharyngitis": "sore_throat",
    "scratchy throat": "sore_throat",
    "raw throat": "sore_throat",
    "pain swallowing": "sore_throat",
    "painful swallowing": "sore_throat",
    "odynophagia": "sore_throat",
    "throat irritation": "sore_throat",
    "inflamed throat": "sore_throat",

    # Rhinorrhea / Congestion
    "rhinorrhea": "rhinorrhea",
    "rhinorrhoea": "rhinorrhea",
    "runny nose": "rhinorrhea",
    "sneezing": "rhinorrhea",
    "nasal congestion": "rhinorrhea",
    "stuffy nose": "rhinorrhea",
    "congestion": "rhinorrhea",
    "blocked nose": "rhinorrhea",
    "post nasal drip": "rhinorrhea",
    "catarrh": "rhinorrhea",
    "coryza": "rhinorrhea",
    "congested": "rhinorrhea",

    # Polyuria
    "polyuria": "polyuria",
    "frequent urination": "polyuria",
    "peeing often": "polyuria",
    "excessive urination": "polyuria",
    "urinating frequently": "polyuria",
    "peeing constantly": "polyuria",
    "nocturia": "polyuria",
    "urinary frequency": "polyuria",
    "constant urination": "polyuria",

    # Polydipsia
    "polydipsia": "polydipsia",
    "excessive thirst": "polydipsia",
    "always thirsty": "polydipsia",
    "extreme thirst": "polydipsia",
    "thirsty": "polydipsia",
    "abnormally thirsty": "polydipsia",
    "unquenchable thirst": "polydipsia",
    "increased thirst": "polydipsia",

    # Dizziness / Vertigo
    "dizziness": "dizziness",
    "dizzy": "dizziness",
    "lightheaded": "dizziness",
    "lightheadedness": "dizziness",
    "vertigo": "dizziness",
    "feeling faint": "dizziness",
    "unsteadiness": "dizziness",
    "woozy": "dizziness",
    "wooziness": "dizziness",
    "presyncope": "dizziness",
    "feeling dizzy": "dizziness",

    # Nausea / Vomiting
    "nausea": "nausea",
    "nauseous": "nausea",
    "nauseated": "nausea",
    "vomiting": "nausea",
    "emesis": "nausea",
    "throwing up": "nausea",
    "puking": "nausea",
    "queasy": "nausea",
    "upset stomach": "nausea",
    "sick to stomach": "nausea",

    # Photophobia
    "photophobia": "photophobia",
    "sensitive to light": "photophobia",
    "sensitivity to light": "photophobia",
    "light sensitivity": "photophobia",
    "eye hurt in light": "photophobia",
    "eyes hurt in bright light": "photophobia",
    "photophobic": "photophobia",
    "intolerant to light": "photophobia",

    # Body Aches / Myalgia
    "body aches": "body_aches",
    "body ache": "body_aches",
    "muscle pain": "body_aches",
    "myalgia": "body_aches",
    "muscle ache": "body_aches",
    "aching muscles": "body_aches",
    "joint pain": "body_aches",
    "arthralgia": "body_aches",
    "aching body": "body_aches",
    "sore muscles": "body_aches",
    "aches all over": "body_aches",

    # Blurred Vision
    "blurred vision": "blurred_vision",
    "blurry vision": "blurred_vision",
    "hazy vision": "blurred_vision",
    "fuzzy vision": "blurred_vision",
    "loss of visual clarity": "blurred_vision",
    "impaired vision": "blurred_vision",

    # Diarrhea
    "diarrhea": "diarrhea",
    "diarrhoea": "diarrhea",
    "loose stools": "diarrhea",
    "watery stools": "diarrhea",
    "stomach cramps": "diarrhea",
    "loose motions": "diarrhea",
    "frequent bowel movements": "diarrhea",

    # Chills / Rigors
    "chills": "chills",
    "shivering": "chills",
    "shivers": "chills",
    "cold sweats": "chills",
    "rigors": "chills",
    "teeth chattering": "chills",
    "feeling chilly": "chills",

    # Weight Loss
    "weight loss": "weight_loss",
    "losing weight": "weight_loss",
    "unexplained weight loss": "weight_loss",
    # abdominal_pain
    "abdominal_pain": "abdominal_pain",
    "abdominal pain": "abdominal_pain",
    "belly pain": "abdominal_pain",
    "stomach ache": "abdominal_pain",
    "stomach pain": "abdominal_pain",
    "tummy pain": "abdominal_pain",
    "cramping in stomach": "abdominal_pain",
    "gut ache": "abdominal_pain",
    "gastric pain": "abdominal_pain",
    "epigastric pain": "abdominal_pain",
    "belly cramps": "abdominal_pain",
    "abdominal cramps": "abdominal_pain",
    "rlq pain": "abdominal_pain",
    "ruq pain": "abdominal_pain",
    "llq pain": "abdominal_pain",
    "luq pain": "abdominal_pain",
    # jaundice
    "jaundice": "jaundice",
    "yellow skin": "jaundice",
    "yellow eyes": "jaundice",
    "yellowing of skin": "jaundice",
    "yellowing of eyes": "jaundice",
    "scleral icterus": "jaundice",
    "icterus": "jaundice",
    "jaundiced": "jaundice",
    "yellow discoloration of skin": "jaundice",
    # dark_urine
    "dark_urine": "dark_urine",
    "dark urine": "dark_urine",
    "tea colored urine": "dark_urine",
    "brown urine": "dark_urine",
    "cola colored urine": "dark_urine",
    "dark colored urine": "dark_urine",
    "beer colored urine": "dark_urine",
    "dark amber urine": "dark_urine",
    # clay_colored_stools
    "clay_colored_stools": "clay_colored_stools",
    "clay colored stools": "clay_colored_stools",
    "clay-colored stools": "clay_colored_stools",
    "pale stool": "clay_colored_stools",
    "pale stools": "clay_colored_stools",
    "white stool": "clay_colored_stools",
    "acholic stool": "clay_colored_stools",
    "acholic stools": "clay_colored_stools",
    "light colored stool": "clay_colored_stools",
    "clay stool": "clay_colored_stools",
    # ascites
    "ascites": "ascites",
    "fluid in belly": "ascites",
    "fluid in abdomen": "ascites",
    "distended abdomen": "ascites",
    "belly swelling": "ascites",
    "abdominal distension": "ascites",
    "water in belly": "ascites",
    "fluid retention in abdomen": "ascites",
    # hematemesis
    "hematemesis": "hematemesis",
    "vomiting blood": "hematemesis",
    "throwing up blood": "hematemesis",
    "coffee ground emesis": "hematemesis",
    "coffee-ground emesis": "hematemesis",
    "blood in vomit": "hematemesis",
    "vomited blood": "hematemesis",
    # heartburn
    "heartburn": "heartburn",
    "acid reflux": "heartburn",
    "gerd": "heartburn",
    "pyrosis": "heartburn",
    "indigestion": "heartburn",
    "sour stomach": "heartburn",
    "acid regurgitation": "heartburn",
    "burning in chest": "heartburn",
    "burning chest": "heartburn",
    # vomiting
    "vomiting": "vomiting",
    "throwing up": "vomiting",
    "emesis": "vomiting",
    "puking": "vomiting",
    "heaving": "vomiting",
    "threw up": "vomiting",
    "vomited": "vomiting",
    # melena
    "melena": "melena",
    "black stool": "melena",
    "tarry stool": "melena",
    "black tarry stool": "melena",
    "black tarry stools": "melena",
    "dark tarry stool": "melena",
    # hematochezia
    "hematochezia": "hematochezia",
    "bright red blood in stool": "hematochezia",
    "blood in bowel movement": "hematochezia",
    "rectal bleeding": "hematochezia",
    "bleeding from rectum": "hematochezia",
    "blood on toilet paper": "hematochezia",
    # dysphagia
    "dysphagia": "dysphagia",
    "difficulty swallowing": "dysphagia",
    "hard to swallow": "dysphagia",
    "trouble swallowing": "dysphagia",
    "food sticking in throat": "dysphagia",
    "swallowing problem": "dysphagia",
    # odynophagia
    "odynophagia": "odynophagia",
    "painful swallowing": "odynophagia",
    "pain on swallowing": "odynophagia",
    "hurts to swallow": "odynophagia",
    "swallowing pain": "odynophagia",
    # early_satiety
    "early_satiety": "early_satiety",
    "early satiety": "early_satiety",
    "feeling full quickly": "early_satiety",
    "cannot finish meals": "early_satiety",
    "premature fullness": "early_satiety",
    "full after few bites": "early_satiety",
    # bloating
    "bloating": "bloating",
    "bloated": "bloating",
    "abdominal fullness": "bloating",
    "gassy belly": "bloating",
    "feeling bloated": "bloating",
    # flatulence
    "flatulence": "flatulence",
    "excessive gas": "flatulence",
    "passing gas": "flatulence",
    "farting": "flatulence",
    "intestinal gas": "flatulence",
    "wind": "flatulence",
    # constipation
    "constipation": "constipation",
    "constipated": "constipation",
    "hard stools": "constipation",
    "infrequent bowel movements": "constipation",
    "difficulty passing stool": "constipation",
    "cannot poop": "constipation",
    # steatorrhea
    "steatorrhea": "steatorrhea",
    "greasy stool": "steatorrhea",
    "floating stool": "steatorrhea",
    "fat in stool": "steatorrhea",
    "foul smelling oily stool": "steatorrhea",
    "oily stool": "steatorrhea",
    # tenesmus
    "tenesmus": "tenesmus",
    "rectal cramping": "tenesmus",
    "feeling need to pass stool": "tenesmus",
    "straining at stool": "tenesmus",
    "incomplete evacuation": "tenesmus",
    # pruritus_ani
    "pruritus_ani": "pruritus_ani",
    "pruritus ani": "pruritus_ani",
    "itchy anus": "pruritus_ani",
    "anal itching": "pruritus_ani",
    "itching around rectum": "pruritus_ani",
    # palpitations
    "palpitations": "palpitations",
    "racing heart": "palpitations",
    "heart fluttering": "palpitations",
    "irregular heartbeat": "palpitations",
    "skipped beats": "palpitations",
    "heart racing": "palpitations",
    "pounding heart": "palpitations",
    "fluttering in chest": "palpitations",
    # leg_swelling
    "leg_swelling": "leg_swelling",
    "leg swelling": "leg_swelling",
    "swollen legs": "leg_swelling",
    "swollen ankles": "leg_swelling",
    "edema": "leg_swelling",
    "pitting edema": "leg_swelling",
    "peripheral edema": "leg_swelling",
    "swollen feet": "leg_swelling",
    "ankle swelling": "leg_swelling",
    # orthopnea
    "orthopnea": "orthopnea",
    "short of breath lying down": "orthopnea",
    "cannot sleep flat": "orthopnea",
    "need pillows to breathe": "orthopnea",
    "breathless lying flat": "orthopnea",
    # hemoptysis
    "hemoptysis": "hemoptysis",
    "coughing up blood": "hemoptysis",
    "blood in sputum": "hemoptysis",
    "blood in phlegm": "hemoptysis",
    "bloody cough": "hemoptysis",
    "coughed up blood": "hemoptysis",
    # wheezing
    "wheezing": "wheezing",
    "wheeze": "wheezing",
    "whistling in chest": "wheezing",
    "musical breathing": "wheezing",
    "noisy breathing": "wheezing",
    "wheezy": "wheezing",
    # paroxysmal_nocturnal_dyspnea
    "paroxysmal_nocturnal_dyspnea": "paroxysmal_nocturnal_dyspnea",
    "paroxysmal nocturnal dyspnea": "paroxysmal_nocturnal_dyspnea",
    "waking up gasping": "paroxysmal_nocturnal_dyspnea",
    "nighttime shortness of breath": "paroxysmal_nocturnal_dyspnea",
    "pnd": "paroxysmal_nocturnal_dyspnea",
    "waking gasping for air": "paroxysmal_nocturnal_dyspnea",
    # syncope
    "syncope": "syncope",
    "fainting": "syncope",
    "fainted": "syncope",
    "blacked out": "syncope",
    "passed out": "syncope",
    "loss of consciousness": "syncope",
    "collapsing": "syncope",
    # presyncope
    "presyncope": "presyncope",
    "near syncope": "presyncope",
    "feeling faint": "presyncope",
    "about to pass out": "presyncope",
    "almost fainted": "presyncope",
    "lightheaded fainting sensation": "presyncope",
    # claudication
    "claudication": "claudication",
    "calf pain walking": "claudication",
    "cramping in calves": "claudication",
    "leg pain on exertion": "claudication",
    "intermittent claudication": "claudication",
    # cyanosis
    "cyanosis": "cyanosis",
    "blue lips": "cyanosis",
    "blue fingers": "cyanosis",
    "bluish skin": "cyanosis",
    "acrocyanosis": "cyanosis",
    "blue nail beds": "cyanosis",
    # stridor
    "stridor": "stridor",
    "high pitched breathing": "stridor",
    "crowing sound breathing": "stridor",
    "inspiratory stridor": "stridor",
    # tachypnea
    "tachypnea": "tachypnea",
    "rapid breathing": "tachypnea",
    "breathing fast": "tachypnea",
    "panting": "tachypnea",
    "hyperventilating": "tachypnea",
    # pleuritic_chest_pain
    "pleuritic_chest_pain": "pleuritic_chest_pain",
    "pleuritic chest pain": "pleuritic_chest_pain",
    "sharp chest pain on breathing": "pleuritic_chest_pain",
    "pain breathing in": "pleuritic_chest_pain",
    "hurts when taking deep breath": "pleuritic_chest_pain",
    "pleurisy pain": "pleuritic_chest_pain",
    # sputum_production
    "sputum_production": "sputum_production",
    "sputum production": "sputum_production",
    "productive cough": "sputum_production",
    "coughing up phlegm": "sputum_production",
    "mucus production": "sputum_production",
    "bringing up phlegm": "sputum_production",
    # purulent_sputum
    "purulent_sputum": "purulent_sputum",
    "purulent sputum": "purulent_sputum",
    "green phlegm": "purulent_sputum",
    "yellow phlegm": "purulent_sputum",
    "infected phlegm": "purulent_sputum",
    "green mucus": "purulent_sputum",
    "yellow mucus": "purulent_sputum",
    # chest_tightness
    "chest_tightness": "chest_tightness",
    "chest tightness": "chest_tightness",
    "tight chest": "chest_tightness",
    "band around chest": "chest_tightness",
    "chest constriction": "chest_tightness",
    "pressure in chest": "chest_tightness",
    # nasal_congestion
    "nasal_congestion": "nasal_congestion",
    "nasal congestion": "nasal_congestion",
    "stuffy nose": "nasal_congestion",
    "blocked nose": "nasal_congestion",
    "congested nose": "nasal_congestion",
    "plugged nose": "nasal_congestion",
    # hoarseness
    "hoarseness": "hoarseness",
    "hoarse voice": "hoarseness",
    "raspy voice": "hoarseness",
    "lost voice": "hoarseness",
    "dysphonia": "hoarseness",
    "scratchy voice": "hoarseness",
    # snoring
    "snoring": "snoring",
    "loud snoring": "snoring",
    "snore": "snoring",
    "gasping during sleep": "snoring",
    "sleep apnea snoring": "snoring",
    # tremor
    "tremor": "tremor",
    "shaking hands": "tremor",
    "hand tremors": "tremor",
    "involuntary shaking": "tremor",
    "trembling": "tremor",
    "shaky hands": "tremor",
    "tremors": "tremor",
    # numbness
    "numbness": "numbness",
    "numb": "numbness",
    "loss of feeling": "numbness",
    "cannot feel fingers": "numbness",
    "loss of sensation": "numbness",
    "numb toes": "numbness",
    "numb limbs": "numbness",
    # tingling
    "tingling": "tingling",
    "pins and needles": "tingling",
    "paresthesia": "tingling",
    "prickling sensation": "tingling",
    "asleep limb": "tingling",
    "prickling in fingers": "tingling",
    # seizures
    "seizures": "seizures",
    "seizure": "seizures",
    "convulsions": "seizures",
    "epileptic fit": "seizures",
    "epilepsy attack": "seizures",
    "grand mal": "seizures",
    "jerking episode": "seizures",
    "convulsion": "seizures",
    # confusion
    "confusion": "confusion",
    "confused": "confusion",
    "disoriented": "confusion",
    "delirium": "confusion",
    "muddled thinking": "confusion",
    "cannot focus": "confusion",
    "disorientation": "confusion",
    # ataxia
    "ataxia": "ataxia",
    "loss of balance": "ataxia",
    "uncoordinated": "ataxia",
    "clumsiness": "ataxia",
    "unsteady gait": "ataxia",
    "stumbling": "ataxia",
    "cannot balance": "ataxia",
    # stiff_neck
    "stiff_neck": "stiff_neck",
    "stiff neck": "stiff_neck",
    "neck stiffness": "stiff_neck",
    "nuchal rigidity": "stiff_neck",
    "cannot turn neck": "stiff_neck",
    "tight neck": "stiff_neck",
    "rigid neck": "stiff_neck",
    # facial_droop
    "facial_droop": "facial_droop",
    "facial droop": "facial_droop",
    "drooping face": "facial_droop",
    "face drooping": "facial_droop",
    "one side of face falling": "facial_droop",
    "crooked smile": "facial_droop",
    "bell palsy": "facial_droop",
    # dysarthria
    "dysarthria": "dysarthria",
    "slurred speech": "dysarthria",
    "slurring words": "dysarthria",
    "difficulty articulating": "dysarthria",
    "garbled speech": "dysarthria",
    # aphasia
    "aphasia": "aphasia",
    "difficulty speaking": "aphasia",
    "word finding difficulty": "aphasia",
    "cannot find words": "aphasia",
    "speech loss": "aphasia",
    "trouble speaking": "aphasia",
    # focal_weakness
    "focal_weakness": "focal_weakness",
    "focal weakness": "focal_weakness",
    "arm weakness": "focal_weakness",
    "leg weakness": "focal_weakness",
    "one sided weakness": "focal_weakness",
    "hemiparesis": "focal_weakness",
    "weak arm": "focal_weakness",
    "weak leg": "focal_weakness",
    # vertigo
    "vertigo": "vertigo",
    "spinning sensation": "vertigo",
    "room spinning": "vertigo",
    "spinning head": "vertigo",
    "rotational dizziness": "vertigo",
    # altered_mental_status
    "altered_mental_status": "altered_mental_status",
    "altered mental status": "altered_mental_status",
    "ams": "altered_mental_status",
    "lethargic responsiveness": "altered_mental_status",
    "obtunded": "altered_mental_status",
    "stupor": "altered_mental_status",
    "decreased consciousness": "altered_mental_status",
    # memory_loss
    "memory_loss": "memory_loss",
    "memory loss": "memory_loss",
    "amnesia": "memory_loss",
    "forgetfulness": "memory_loss",
    "losing memory": "memory_loss",
    "poor memory": "memory_loss",
    "short term memory loss": "memory_loss",
    # phonophobia
    "phonophobia": "phonophobia",
    "sensitive to sound": "phonophobia",
    "sound sensitivity": "phonophobia",
    "loud noises hurt": "phonophobia",
    "noise intolerance": "phonophobia",
    # visual_aura
    "visual_aura": "visual_aura",
    "visual aura": "visual_aura",
    "zig zag lights": "visual_aura",
    "scintillating scotoma": "visual_aura",
    "aura before headache": "visual_aura",
    "flashing lights": "visual_aura",
    "geometric light patterns": "visual_aura",
    # tinnitus
    "tinnitus": "tinnitus",
    "ringing in ears": "tinnitus",
    "buzzing in ears": "tinnitus",
    "ear ringing": "tinnitus",
    "ear buzzing": "tinnitus",
    "ringing ears": "tinnitus",
    # gait_unsteadiness
    "gait_unsteadiness": "gait_unsteadiness",
    "gait unsteadiness": "gait_unsteadiness",
    "unsteady walking": "gait_unsteadiness",
    "wobbly walking": "gait_unsteadiness",
    "difficulty walking": "gait_unsteadiness",
    "unsteady on feet": "gait_unsteadiness",
    # sciatica
    "sciatica": "sciatica",
    "radiating leg pain": "sciatica",
    "shooting pain down leg": "sciatica",
    "sciatic nerve pain": "sciatica",
    "pain from lower back to leg": "sciatica",
    # flank_pain
    "flank_pain": "flank_pain",
    "flank pain": "flank_pain",
    "kidney pain": "flank_pain",
    "pain in flank": "flank_pain",
    "side pain": "flank_pain",
    "back kidney pain": "flank_pain",
    "costovertebral angle pain": "flank_pain",
    "pain in side and back": "flank_pain",
    # hematuria
    "hematuria": "hematuria",
    "blood in urine": "hematuria",
    "red urine": "hematuria",
    "pink urine": "hematuria",
    "bloody urine": "hematuria",
    "blood when peeing": "hematuria",
    # dysuria
    "dysuria": "dysuria",
    "painful urination": "dysuria",
    "burning urination": "dysuria",
    "hurts to pee": "dysuria",
    "burning pee": "dysuria",
    "pain when peeing": "dysuria",
    "burning micturition": "dysuria",
    # oliguria
    "oliguria": "oliguria",
    "decreased urine": "oliguria",
    "low urine output": "oliguria",
    "not peeing enough": "oliguria",
    "scant urine": "oliguria",
    "reduced urine volume": "oliguria",
    # urinary_urgency
    "urinary_urgency": "urinary_urgency",
    "urinary urgency": "urinary_urgency",
    "urgent need to pee": "urinary_urgency",
    "sudden urge to urinate": "urinary_urgency",
    "cannot hold bladder": "urinary_urgency",
    "rush to bathroom": "urinary_urgency",
    # nocturia
    "nocturia": "nocturia",
    "peeing at night": "nocturia",
    "waking up to pee": "nocturia",
    "nighttime urination": "nocturia",
    "peeing multiple times at night": "nocturia",
    # urinary_incontinence
    "urinary_incontinence": "urinary_incontinence",
    "urinary incontinence": "urinary_incontinence",
    "leaking urine": "urinary_incontinence",
    "incontinence": "urinary_incontinence",
    "bladder leakage": "urinary_incontinence",
    "wetting pants": "urinary_incontinence",
    "accidental pee": "urinary_incontinence",
    # urinary_hesitancy
    "urinary_hesitancy": "urinary_hesitancy",
    "urinary hesitancy": "urinary_hesitancy",
    "hesitancy peeing": "urinary_hesitancy",
    "trouble starting to pee": "urinary_hesitancy",
    "weak stream": "urinary_hesitancy",
    "straining to urinate": "urinary_hesitancy",
    # urinary_frequency
    "urinary_frequency": "urinary_frequency",
    "urinary frequency": "urinary_frequency",
    "peeing often": "urinary_frequency",
    "frequent urination": "urinary_frequency",
    "peeing constantly": "urinary_frequency",
    "frequent pee": "urinary_frequency",
    # suprapubic_pain
    "suprapubic_pain": "suprapubic_pain",
    "suprapubic pain": "suprapubic_pain",
    "bladder pain": "suprapubic_pain",
    "pelvic bladder pressure": "suprapubic_pain",
    "pain over pubic bone": "suprapubic_pain",
    "lower belly bladder pain": "suprapubic_pain",
    # frothy_urine
    "frothy_urine": "frothy_urine",
    "frothy urine": "frothy_urine",
    "foamy urine": "frothy_urine",
    "bubbles in urine": "frothy_urine",
    "froth in toilet": "frothy_urine",
    "bubbly urine": "frothy_urine",
    # anuria
    "anuria": "anuria",
    "no urine": "anuria",
    "not producing urine": "anuria",
    "zero urine": "anuria",
    "absence of urine": "anuria",
    # penile_discharge
    "penile_discharge": "penile_discharge",
    "penile discharge": "penile_discharge",
    "urethral discharge": "penile_discharge",
    "pus from penis": "penile_discharge",
    "discharge from urethra": "penile_discharge",
    # pelvic_pain
    "pelvic_pain": "pelvic_pain",
    "pelvic pain": "pelvic_pain",
    "lower abdominal pelvic pain": "pelvic_pain",
    "cramping pelvic pain": "pelvic_pain",
    "pain in pelvis": "pelvic_pain",
    # skin_rash
    "skin_rash": "skin_rash",
    "skin rash": "skin_rash",
    "rash": "skin_rash",
    "eruption": "skin_rash",
    "exanthem": "skin_rash",
    "spots on skin": "skin_rash",
    "skin redness": "skin_rash",
    "rash on skin": "skin_rash",
    # itching
    "itching": "itching",
    "itchy": "itching",
    "pruritus": "itching",
    "scratchy skin": "itching",
    "need to scratch": "itching",
    "itchiness": "itching",
    "itch": "itching",
    # butterfly_rash
    "butterfly_rash": "butterfly_rash",
    "butterfly rash": "butterfly_rash",
    "malar rash": "butterfly_rash",
    "rash over cheeks and nose": "butterfly_rash",
    "malar erythema": "butterfly_rash",
    "lupus rash": "butterfly_rash",
    "redness across cheeks and nose": "butterfly_rash",
    # hives
    "hives": "hives",
    "urticaria": "hives",
    "welts": "hives",
    "wheals": "hives",
    "itchy bumps": "hives",
    "allergic welts": "hives",
    "nettle rash": "hives",
    # joint_swelling
    "joint_swelling": "joint_swelling",
    "joint swelling": "joint_swelling",
    "swollen joints": "joint_swelling",
    "swelling in knees": "joint_swelling",
    "joint effusion": "joint_swelling",
    "puffy joints": "joint_swelling",
    "swollen knuckles": "joint_swelling",
    "swollen knee": "joint_swelling",
    # hair_loss
    "hair_loss": "hair_loss",
    "hair loss": "hair_loss",
    "alopecia": "hair_loss",
    "hair thinning": "hair_loss",
    "falling hair": "hair_loss",
    "balding": "hair_loss",
    "shedding hair": "hair_loss",
    "losing hair": "hair_loss",
    # purpura
    "purpura": "purpura",
    "purple spots": "purpura",
    "purpuric rash": "purpura",
    "non-blanching spots": "purpura",
    "skin hemorrhage": "purpura",
    "purple bruising rash": "purpura",
    # petechiae
    "petechiae": "petechiae",
    "pinpoint red spots": "petechiae",
    "tiny red dots on skin": "petechiae",
    "petechial rash": "petechiae",
    "red pinpoint dots": "petechiae",
    # erythema
    "erythema": "erythema",
    "red skin": "erythema",
    "cutaneous redness": "erythema",
    "flushed skin": "erythema",
    "erythematous rash": "erythema",
    # joint_pain
    "joint_pain": "joint_pain",
    "joint pain": "joint_pain",
    "arthralgia": "joint_pain",
    "aching joints": "joint_pain",
    "joint ache": "joint_pain",
    "pain in knees": "joint_pain",
    "pain in hands": "joint_pain",
    "sore joints": "joint_pain",
    # morning_stiffness
    "morning_stiffness": "morning_stiffness",
    "morning stiffness": "morning_stiffness",
    "stiff joints in morning": "morning_stiffness",
    "morning stiffness over 30 minutes": "morning_stiffness",
    "stiff hands morning": "morning_stiffness",
    # skin_peeling
    "skin_peeling": "skin_peeling",
    "skin peeling": "skin_peeling",
    "peeling skin": "skin_peeling",
    "desquamation": "skin_peeling",
    "flaking skin": "skin_peeling",
    "peeling hands": "skin_peeling",
    # ulcers_oral
    "ulcers_oral": "ulcers_oral",
    "ulcers oral": "ulcers_oral",
    "oral ulcers": "ulcers_oral",
    "mouth ulcers": "ulcers_oral",
    "canker sores": "ulcers_oral",
    "aphthous ulcers": "ulcers_oral",
    "sores in mouth": "ulcers_oral",
    "painful mouth sores": "ulcers_oral",
    # ulcers_genital
    "ulcers_genital": "ulcers_genital",
    "ulcers genital": "ulcers_genital",
    "genital ulcers": "ulcers_genital",
    "sores on genitals": "ulcers_genital",
    "genital sores": "ulcers_genital",
    "chancres": "ulcers_genital",
    "painful genital ulcers": "ulcers_genital",
    # bullae
    "bullae": "bullae",
    "blisters": "bullae",
    "skin blisters": "bullae",
    "large blisters": "bullae",
    "fluid filled blisters": "bullae",
    # photosensitivity
    "photosensitivity": "photosensitivity",
    "sun sensitive": "photosensitivity",
    "sunlight rash": "photosensitivity",
    "burning in sun": "photosensitivity",
    "sun allergy": "photosensitivity",
    # raynaud_phenomenon
    "raynaud_phenomenon": "raynaud_phenomenon",
    "raynaud phenomenon": "raynaud_phenomenon",
    "white fingers in cold": "raynaud_phenomenon",
    "blue fingers cold": "raynaud_phenomenon",
    "raynaud": "raynaud_phenomenon",
    "cold fingers turn white": "raynaud_phenomenon",
    # dry_eyes
    "dry_eyes": "dry_eyes",
    "dry eyes": "dry_eyes",
    "gritty eyes": "dry_eyes",
    "eye dryness": "dry_eyes",
    "burning dry eyes": "dry_eyes",
    "cannot produce tears": "dry_eyes",
    # dry_mouth
    "dry_mouth": "dry_mouth",
    "dry mouth": "dry_mouth",
    "xerostomia": "dry_mouth",
    "cotton mouth": "dry_mouth",
    "lack of saliva": "dry_mouth",
    "parched mouth": "dry_mouth",
    # skin_thickening
    "skin_thickening": "skin_thickening",
    "skin thickening": "skin_thickening",
    "thick skin": "skin_thickening",
    "sclerodactyly": "skin_thickening",
    "tight skin on fingers": "skin_thickening",
    "induration of skin": "skin_thickening",
    # nail_clubbing
    "nail_clubbing": "nail_clubbing",
    "nail clubbing": "nail_clubbing",
    "clubbed fingers": "nail_clubbing",
    "clubbed nails": "nail_clubbing",
    "rounded nails": "nail_clubbing",
    "digital clubbing": "nail_clubbing",
    # easy_bruising
    "easy_bruising": "easy_bruising",
    "easy bruising": "easy_bruising",
    "bruising easily": "easy_bruising",
    "ecchymosis": "easy_bruising",
    "frequent bruises": "easy_bruising",
    "spontaneous bruising": "easy_bruising",
    # rigors
    "rigors": "rigors",
    "shaking chills": "rigors",
    "teeth chattering chills": "rigors",
    "violent chills": "rigors",
    "severe shivering": "rigors",
    # night_sweats
    "night_sweats": "night_sweats",
    "night sweats": "night_sweats",
    "sweating at night": "night_sweats",
    "drenching sweats": "night_sweats",
    "nocturnal sweating": "night_sweats",
    "waking up drenched": "night_sweats",
    "soaking night sweats": "night_sweats",
    # lymphadenopathy
    "lymphadenopathy": "lymphadenopathy",
    "swollen lymph nodes": "lymphadenopathy",
    "swollen glands": "lymphadenopathy",
    "enlarged nodes": "lymphadenopathy",
    "lumps in neck": "lymphadenopathy",
    "groin lumps": "lymphadenopathy",
    "swollen neck glands": "lymphadenopathy",
    # malaise
    "malaise": "malaise",
    "feeling unwell": "malaise",
    "general malaise": "malaise",
    "feeling rundown": "malaise",
    "lack of wellness": "malaise",
    "ill feeling": "malaise",
    # weight_gain
    "weight_gain": "weight_gain",
    "weight gain": "weight_gain",
    "unexplained weight gain": "weight_gain",
    "rapid weight gain": "weight_gain",
    "gaining weight": "weight_gain",
    "increased weight": "weight_gain",
    # anorexia
    "anorexia": "anorexia",
    "loss of appetite": "anorexia",
    "no appetite": "anorexia",
    "not wanting to eat": "anorexia",
    "poor appetite": "anorexia",
    "decreased appetite": "anorexia",
    # cachexia
    "cachexia": "cachexia",
    "wasting away": "cachexia",
    "severe muscle loss": "cachexia",
    "wasting": "cachexia",
    "emaciation": "cachexia",
    # insomnia
    "insomnia": "insomnia",
    "sleeplessness": "insomnia",
    "trouble sleeping": "insomnia",
    "cannot sleep": "insomnia",
    "poor sleep": "insomnia",
    "waking up early": "insomnia",
    # excessive_daytime_sleepiness
    "excessive_daytime_sleepiness": "excessive_daytime_sleepiness",
    "excessive daytime sleepiness": "excessive_daytime_sleepiness",
    "sleepy during day": "excessive_daytime_sleepiness",
    "falling asleep during day": "excessive_daytime_sleepiness",
    "somnolence": "excessive_daytime_sleepiness",
    "daytime drowsiness": "excessive_daytime_sleepiness",
    # heat_intolerance
    "heat_intolerance": "heat_intolerance",
    "heat intolerance": "heat_intolerance",
    "cannot tolerate heat": "heat_intolerance",
    "always hot": "heat_intolerance",
    "feeling overheated": "heat_intolerance",
    "intolerant to warmth": "heat_intolerance",
    # cold_intolerance
    "cold_intolerance": "cold_intolerance",
    "cold intolerance": "cold_intolerance",
    "cannot tolerate cold": "cold_intolerance",
    "always cold": "cold_intolerance",
    "feeling freezing": "cold_intolerance",
    "intolerant to cold": "cold_intolerance",
    # excessive_sweating
    "excessive_sweating": "excessive_sweating",
    "excessive sweating": "excessive_sweating",
    "diaphoresis": "excessive_sweating",
    "profuse sweating": "excessive_sweating",
    "sweating too much": "excessive_sweating",
    "hyperhidrosis": "excessive_sweating",
    "heavy sweating": "excessive_sweating",
    # generalized_weakness
    "generalized_weakness": "generalized_weakness",
    "generalized weakness": "generalized_weakness",
    "overall weakness": "generalized_weakness",
    "muscular weakness": "generalized_weakness",
    "body weakness": "generalized_weakness",
    "asthenia": "generalized_weakness",
    "feeling so weak": "generalized_weakness",
    # myalgia
    "myalgia": "myalgia",
    "muscle aches": "myalgia",
    "muscle pain": "myalgia",
    "sore muscles": "myalgia",
    "aching muscles": "myalgia",
    "diffuse muscle pain": "myalgia",
    # arthralgia
    "arthralgia": "arthralgia",
    "joint aching": "arthralgia",
    "polyarthralgia": "arthralgia",
    "multiple joint aches": "arthralgia",
    # fever_low_grade
    "fever_low_grade": "fever_low_grade",
    "fever low grade": "fever_low_grade",
    "low grade fever": "fever_low_grade",
    "slight fever": "fever_low_grade",
    "mild fever": "fever_low_grade",
    "low-grade fever": "fever_low_grade",
    "mildly elevated temperature": "fever_low_grade",
    # goiter
    "goiter": "goiter",
    "enlarged thyroid": "goiter",
    "neck swelling thyroid": "goiter",
    "thyroid lump": "goiter",
    "swelling in lower neck": "goiter",
    # hypoglycemia_symptoms
    "hypoglycemia_symptoms": "hypoglycemia_symptoms",
    "hypoglycemia symptoms": "hypoglycemia_symptoms",
    "hypoglycemia": "hypoglycemia_symptoms",
    "low blood sugar symptoms": "hypoglycemia_symptoms",
    "shaky and sweaty": "hypoglycemia_symptoms",
    "sugar drop": "hypoglycemia_symptoms",
    "feeling shaky hungry sweaty": "hypoglycemia_symptoms",
    # hyperphagia
    "hyperphagia": "hyperphagia",
    "excessive hunger": "hyperphagia",
    "insatiable appetite": "hyperphagia",
    "constant hunger": "hyperphagia",
    "eating constantly": "hyperphagia",
    # galactorrhea
    "galactorrhea": "galactorrhea",
    "nipple discharge": "galactorrhea",
    "breast milk discharge": "galactorrhea",
    "milky nipple discharge": "galactorrhea",
    # gynecomastia
    "gynecomastia": "gynecomastia",
    "male breast enlargement": "gynecomastia",
    "enlarged male breasts": "gynecomastia",
    "man boobs": "gynecomastia",
    "breast tissue in male": "gynecomastia",
    # hirsutism
    "hirsutism": "hirsutism",
    "excessive facial hair": "hirsutism",
    "male pattern hair growth": "hirsutism",
    "coarse hair on face": "hirsutism",
    "excess body hair in female": "hirsutism",
    # pallor
    "pallor": "pallor",
    "pale skin": "pallor",
    "looking pale": "pallor",
    "washed out": "pallor",
    "paleness": "pallor",
    "pale complexion": "pallor",
    # bleeding_gums
    "bleeding_gums": "bleeding_gums",
    "bleeding gums": "bleeding_gums",
    "gums bleed": "bleeding_gums",
    "spontaneous gum bleeding": "bleeding_gums",
    "blood when brushing teeth": "bleeding_gums",
    # epistaxis
    "epistaxis": "epistaxis",
    "nosebleed": "epistaxis",
    "bloody nose": "epistaxis",
    "nose bleeding": "epistaxis",
    "frequent nosebleeds": "epistaxis",
    # menorrhagia
    "menorrhagia": "menorrhagia",
    "heavy periods": "menorrhagia",
    "heavy menstrual bleeding": "menorrhagia",
    "prolonged periods": "menorrhagia",
    "excessive menstrual flow": "menorrhagia",
    # bone_pain
    "bone_pain": "bone_pain",
    "bone pain": "bone_pain",
    "deep bone ache": "bone_pain",
    "aching bones": "bone_pain",
    "bone tenderness": "bone_pain",
    # muscle_cramps
    "muscle_cramps": "muscle_cramps",
    "muscle cramps": "muscle_cramps",
    "cramps in legs": "muscle_cramps",
    "charley horse": "muscle_cramps",
    "muscle spasms": "muscle_cramps",
    "cramping muscles": "muscle_cramps",
    # flushing
    "flushing": "flushing",
    "facial flushing": "flushing",
    "red face flush": "flushing",
    "hot flushes": "flushing",
    "flushed face": "flushing",
    # eye_pain
    "eye_pain": "eye_pain",
    "eye pain": "eye_pain",
    "pain in eye": "eye_pain",
    "hurting eyes": "eye_pain",
    "ocular pain": "eye_pain",
    "deep eye ache": "eye_pain",
    # eye_redness
    "eye_redness": "eye_redness",
    "eye redness": "eye_redness",
    "bloodshot eyes": "eye_redness",
    "red eye": "eye_redness",
    "conjunctival redness": "eye_redness",
    "red eyes": "eye_redness",
    # diplopia
    "diplopia": "diplopia",
    "double vision": "diplopia",
    "seeing double": "diplopia",
    # vision_loss
    "vision_loss": "vision_loss",
    "vision loss": "vision_loss",
    "losing vision": "vision_loss",
    "cannot see": "vision_loss",
    "blind spots": "vision_loss",
    "sudden vision loss": "vision_loss",
    "blurred or lost vision": "vision_loss",
    # ear_pain
    "ear_pain": "ear_pain",
    "ear pain": "ear_pain",
    "earache": "ear_pain",
    "pain in ear": "ear_pain",
    "otalgia": "ear_pain",
    "sore ear": "ear_pain",
    # ear_discharge
    "ear_discharge": "ear_discharge",
    "ear discharge": "ear_discharge",
    "drainage from ear": "ear_discharge",
    "fluid leaking from ear": "ear_discharge",
    "otorrhea": "ear_discharge",
    "pus from ear": "ear_discharge",
    # hearing_loss
    "hearing_loss": "hearing_loss",
    "hearing loss": "hearing_loss",
    "cannot hear well": "hearing_loss",
    "deafness": "hearing_loss",
    "hard of hearing": "hearing_loss",
    "diminished hearing": "hearing_loss",
    # sore_tongue
    "sore_tongue": "sore_tongue",
    "sore tongue": "sore_tongue",
    "tongue pain": "sore_tongue",
    "burning tongue": "sore_tongue",
    "glossitis": "sore_tongue",
    "red painful tongue": "sore_tongue",
    # halitosis
    "halitosis": "halitosis",
    "bad breath": "halitosis",
    "foul breath": "halitosis",
    "chronic bad breath": "halitosis",
    "foul smelling breath": "halitosis",
    # toothache
    "toothache": "toothache",
    "tooth pain": "toothache",
    "dental pain": "toothache",
    "teeth hurting": "toothache",
    "aching tooth": "toothache",
    # loss_of_taste
    "loss_of_taste": "loss_of_taste",
    "loss of taste": "loss_of_taste",
    "cannot taste food": "loss_of_taste",
    "ageusia": "loss_of_taste",
    "loss of taste sensation": "loss_of_taste",
    "no taste": "loss_of_taste",
    # loss_of_smell
    "loss_of_smell": "loss_of_smell",
    "loss of smell": "loss_of_smell",
    "cannot smell": "loss_of_smell",
    "anosmia": "loss_of_smell",
    "loss of olfactory": "loss_of_smell",
    "no smell": "loss_of_smell",
    # foreign_body_sensation
    "foreign_body_sensation": "foreign_body_sensation",
    "foreign body sensation": "foreign_body_sensation",
    "feeling like something in eye": "foreign_body_sensation",
    "grit in eye": "foreign_body_sensation",
    "lump in throat": "foreign_body_sensation",
    "scratchy eye": "foreign_body_sensation",
    # epiphora
    "epiphora": "epiphora",
    "watery eyes": "epiphora",
    "excessive tearing": "epiphora",
    "eyes watering constantly": "epiphora",
    "tearing eyes": "epiphora",
    "involuntary weight loss": "weight_loss",
    "rapid weight loss": "weight_loss",
    "cachexia": "weight_loss",
}

# ---------------------------------------------------------------------------
# Preprocessed Output Dataclass
# ---------------------------------------------------------------------------

@dataclass
class PreprocessedClinicalData:
    feature_order: List[str]
    imputed_vector: List[float]
    raw_vector: List[float]
    imputed_dict: Dict[str, float]
    raw_dict: Dict[str, float]
    canonical_symptoms: List[str]
    negated_symptoms: List[str]
    unmapped_tokens: List[str]
    vitals_raw: Dict[str, Any]
    vitals_imputed: Dict[str, float]
    imputed_fields: List[str]
    schema_version: str

    def to_dict(self) -> Dict[str, Any]:
        """Serializes preprocessed result to dictionary with clean NaN representation."""
        result = asdict(self)
        return result

    def get_feature_vector(self, imputed: bool = True) -> List[float]:
        """Returns ordered feature vector, either with normal imputation or preserving NaN."""
        return list(self.imputed_vector) if imputed else list(self.raw_vector)


# ---------------------------------------------------------------------------
# Clinical Preprocessor Implementation
# ---------------------------------------------------------------------------

class ClinicalPreprocessor:
    """
    Dynamic clinical preprocessor for disease-risk prediction and SHAP explainability.
    Standardizes unstructured text/symptom lists + structured vitals into deterministic vectors.
    """

    def __init__(
        self,
        schema_path: Optional[str] = None,
        schema: Optional[Dict[str, Any]] = None,
        version: Optional[str] = None,
    ):
        if schema is not None:
            self.schema = schema
            self.schema_path = schema_path or SCHEMA_V2_PATH
        elif schema_path is not None:
            self.schema_path = str(schema_path)
            self.schema = self._load_schema()
        elif version == "1.0.0":
            self.schema_path = SCHEMA_V1_PATH
            self.schema = self._load_schema()
        elif version in ("2.0.0", "v2"):
            self.schema_path = SCHEMA_V2_PATH
            self.schema = self._load_schema()
        else:
            self.schema_path = SCHEMA_V2_PATH
            self.schema = self._load_schema()

        self.feature_order: List[str] = list(self.schema.get("feature_order", []))
        self.features_spec: Dict[str, Any] = dict(self.schema.get("features", {}))
        self.version: str = str(self.schema.get("version", "2.0.0"))

        # Compile synonym matching catalog (sorted longest phrase first)
        self.sorted_synonyms: List[Tuple[str, str]] = sorted(
            SYMPTOM_SYNONYMS.items(), key=lambda x: len(x[0]), reverse=True
        )

    def _load_schema(self) -> Dict[str, Any]:
        if os.path.exists(self.schema_path):
            with open(self.schema_path, "r", encoding="utf-8") as f:
                return json.load(f)
        raise FileNotFoundError(f"Schema file not found at: {self.schema_path}")

    @staticmethod
    def clean_text(text: str) -> str:
        """Normalizes case, whitespace, and strips special characters except clause boundaries."""
        lowered = text.lower()
        cleaned = re.sub(r"[^\w\s;.,-]", " ", lowered)
        return " ".join(cleaned.split())

    # -----------------------------------------------------------------------
    # Symptom Extraction with Bounded Negation & Contrastive Boundary
    # -----------------------------------------------------------------------

    def parse_symptoms(
        self, input_data: Union[str, List[str], Tuple[str, ...], Set[str]]
    ) -> Dict[str, Any]:
        """
        Parses symptom descriptions into canonical positive and negated symptoms.
        Enforces a bounded negation window (max 3-4 words) that breaks immediately
        on contrastive conjunctions ('but', 'however', ';', etc.).
        """
        if not input_data:
            return {
                "canonical_symptoms": [],
                "negated_symptoms": [],
                "unmapped_tokens": [],
                "symptom_vector": {c: 0.0 for c in CANONICAL_SYMPTOMS},
            }

        # Normalize input to list of clauses/tokens
        if isinstance(input_data, str):
            raw_clauses = [input_data]
        elif isinstance(input_data, (list, tuple, set)):
            raw_clauses = [str(item) for item in input_data if str(item).strip()]
        else:
            raw_clauses = [str(input_data)]

        positive_symptoms: Set[str] = set()
        negated_symptoms: Set[str] = set()
        unmapped_tokens: List[str] = []

        for raw_item in raw_clauses:
            cleaned = self.clean_text(raw_item)
            if not cleaned:
                continue

            # Split raw item into sentences/major clauses by period, semicolon, or newline
            major_clauses = re.split(r"[;.\n]+", cleaned)

            for major_clause in major_clauses:
                major_clause = major_clause.strip()
                if not major_clause:
                    continue

                # Tokenize into word tokens and strip trailing/leading punctuation
                tokens = [t.strip(",;.:-") for t in major_clause.split() if t.strip(",;.:-")]
                n = len(tokens)
                if n == 0:
                    continue

                # Process tokens with bounded negation tracking
                # Active negation state: (is_negated: bool, words_remaining: int)
                active_negation = False
                negation_budget = 0

                i = 0
                while i < n:
                    token = tokens[i]

                    # 1. Check for contrastive conjunctions -> Break negation immediately
                    if token in CONTRASTIVE_CONJUNCTIONS:
                        active_negation = False
                        negation_budget = 0
                        i += 1
                        continue

                    # 2. Check for negation triggers
                    found_neg_trigger = False
                    for trigger in NEGATION_TRIGGERS:
                        trig_words = trigger.split()
                        k = len(trig_words)
                        if i + k <= n and tokens[i : i + k] == trig_words:
                            active_negation = True
                            negation_budget = 4  # Window of 4 words
                            i += k
                            found_neg_trigger = True
                            break

                    if found_neg_trigger:
                        continue

                    # 3. Check for multi-word or single-word symptom match starting at token i
                    matched_canonical = None
                    matched_word_count = 0

                    # Try matching phrases of decreasing lengths (up to 4 words)
                    for phrase_len in range(min(4, n - i), 0, -1):
                        sub_phrase = " ".join(tokens[i : i + phrase_len])

                        # Exact synonym lookup
                        if sub_phrase in SYMPTOM_SYNONYMS:
                            matched_canonical = SYMPTOM_SYNONYMS[sub_phrase]
                            matched_word_count = phrase_len
                            break

                        # Standardized slug match (e.g. "chest_pain")
                        if sub_phrase.replace(" ", "_") in CANONICAL_SYMPTOMS:
                            matched_canonical = sub_phrase.replace(" ", "_")
                            matched_word_count = phrase_len
                            break

                        # Fuzzy match for single tokens >= 4 characters
                        if phrase_len == 1 and len(sub_phrase) >= 4:
                            fuzzy_match = self._fuzzy_match_symptom(sub_phrase)
                            if fuzzy_match:
                                matched_canonical = fuzzy_match
                                matched_word_count = 1
                                break

                    if matched_canonical:
                        # Backward compatibility for v1 18-symptom schema
                        if len(self.feature_order) == 27:
                            if matched_canonical == "vomiting":
                                matched_canonical = "nausea"
                            elif matched_canonical == "myalgia":
                                matched_canonical = "body_aches"

                        if active_negation and negation_budget > 0:
                            negated_symptoms.add(matched_canonical)
                        else:
                            positive_symptoms.add(matched_canonical)

                        # Advance index and decrement negation budget
                        i += matched_word_count
                        if active_negation:
                            negation_budget -= matched_word_count
                            if negation_budget <= 0:
                                active_negation = False
                    else:
                        # Non-matching token
                        if len(token) >= 4 and token not in CONTRASTIVE_CONJUNCTIONS:
                            if token not in unmapped_tokens and not any(
                                token in syn for syn in SYMPTOM_SYNONYMS
                            ):
                                unmapped_tokens.append(token)

                        i += 1
                        if active_negation:
                            negation_budget -= 1
                            if negation_budget <= 0:
                                active_negation = False

        # Determine active symptoms list based on loaded schema
        active_symptoms = (
            self.feature_order[: len(self.feature_order) - 9]
            if len(self.feature_order) > 9
            else list(CANONICAL_SYMPTOMS)
        )

        # Positive overrides negation only if explicitly affirmed elsewhere without negation
        final_positive = set(c for c in active_symptoms if c in positive_symptoms)

        # Cross-version synonym co-activation: body_aches <-> myalgia
        if "body_aches" in positive_symptoms and "myalgia" in active_symptoms:
            final_positive.add("myalgia")
        if "myalgia" in positive_symptoms and "body_aches" in active_symptoms:
            final_positive.add("body_aches")

        final_negated = set(c for c in active_symptoms if c in negated_symptoms and c not in final_positive)

        # Build symptom vector
        symptom_vector = {c: (1.0 if c in final_positive else 0.0) for c in active_symptoms}

        return {
            "canonical_symptoms": [c for c in active_symptoms if c in final_positive],
            "negated_symptoms": [c for c in active_symptoms if c in final_negated],
            "unmapped_tokens": unmapped_tokens[:10],
            "symptom_vector": symptom_vector,
        }

    def _fuzzy_match_symptom(self, word: str, min_similarity: float = 0.82) -> Optional[str]:
        """Fuzzy matches a single word against synonym catalog using SequenceMatcher."""
        best_match = None
        best_ratio = 0.0

        for synonym, canonical in self.sorted_synonyms:
            # Only compare single words against single-word synonyms
            if " " in synonym:
                continue
            if abs(len(word) - len(synonym)) > 3:
                continue

            ratio = difflib.SequenceMatcher(None, word, synonym).ratio()
            if ratio >= min_similarity and ratio > best_ratio:
                best_ratio = ratio
                best_match = canonical

        return best_match

    # -----------------------------------------------------------------------
    # Structured Vitals Parsing, Physiological Clamping, & Unit Handling
    # -----------------------------------------------------------------------

    def parse_vitals(
        self,
        vitals_data: Optional[Dict[str, Any]] = None,
        patient_profile_data: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Dict[str, float], Dict[str, float], List[str]]:
        """
        Parses, validates, units-normalizes, and physiologically clamps clinical vitals.
        Returns:
            - raw_vitals: dict containing numeric float values or math.nan for missing fields.
            - imputed_vitals: dict containing numeric float values with missing fields imputed to reference normals.
            - imputed_fields: list of field names that were missing and imputed.
        """
        data: Dict[str, Any] = {}
        if patient_profile_data:
            data.update(patient_profile_data)
        if vitals_data:
            data.update(vitals_data)

        raw: Dict[str, float] = {}
        imputed: Dict[str, float] = {}
        imputed_fields: List[str] = []

        # 1. Age (Years)
        age_val = self._extract_age(data)
        if age_val is not None:
            clamped_age = self._clamp("age", age_val)
            raw["age"] = clamped_age
            imputed["age"] = clamped_age
        else:
            raw["age"] = math.nan
            imputed["age"] = self.features_spec["age"]["default_imputation"]
            imputed_fields.append("age")

        # 2. Sex (Encoded: 1.0 = Male, 0.0 = Female, 0.5 = Other/Neutral)
        sex_val = self._extract_sex(data)
        if sex_val is not None:
            clamped_sex = self._clamp("sex", sex_val)
            raw["sex"] = clamped_sex
            imputed["sex"] = clamped_sex
        else:
            raw["sex"] = math.nan
            imputed["sex"] = self.features_spec["sex"]["default_imputation"]
            imputed_fields.append("sex")

        # 3. Blood Pressure: Systolic & Diastolic (mmHg)
        sys_val, dia_val = self._extract_bp(data)

        if sys_val is not None:
            clamped_sys = self._clamp("systolic_bp", sys_val)
            raw["systolic_bp"] = clamped_sys
            imputed["systolic_bp"] = clamped_sys
        else:
            raw["systolic_bp"] = math.nan
            imputed["systolic_bp"] = self.features_spec["systolic_bp"]["default_imputation"]
            imputed_fields.append("systolic_bp")

        if dia_val is not None:
            clamped_dia = self._clamp("diastolic_bp", dia_val)
            raw["diastolic_bp"] = clamped_dia
            imputed["diastolic_bp"] = clamped_dia
        else:
            raw["diastolic_bp"] = math.nan
            imputed["diastolic_bp"] = self.features_spec["diastolic_bp"]["default_imputation"]
            imputed_fields.append("diastolic_bp")

        # Ensure systolic >= diastolic if both are present in imputed/raw
        if not math.isnan(raw["systolic_bp"]) and not math.isnan(raw["diastolic_bp"]):
            if raw["systolic_bp"] < raw["diastolic_bp"]:
                raw["systolic_bp"], raw["diastolic_bp"] = raw["diastolic_bp"], raw["systolic_bp"]
        if imputed["systolic_bp"] < imputed["diastolic_bp"]:
            imputed["systolic_bp"], imputed["diastolic_bp"] = imputed["diastolic_bp"], imputed["systolic_bp"]

        # 4. Heart Rate (bpm)
        hr_val = self._extract_numeric(data, ["heart_rate", "pulse", "hr", "pulse_rate"])
        if hr_val is not None:
            clamped_hr = self._clamp("heart_rate", hr_val)
            raw["heart_rate"] = clamped_hr
            imputed["heart_rate"] = clamped_hr
        else:
            raw["heart_rate"] = math.nan
            imputed["heart_rate"] = self.features_spec["heart_rate"]["default_imputation"]
            imputed_fields.append("heart_rate")

        # 5. Glucose (mg/dL)
        glu_val = self._extract_glucose(data)
        if glu_val is not None:
            clamped_glu = self._clamp("glucose", glu_val)
            raw["glucose"] = clamped_glu
            imputed["glucose"] = clamped_glu
        else:
            raw["glucose"] = math.nan
            imputed["glucose"] = self.features_spec["glucose"]["default_imputation"]
            imputed_fields.append("glucose")

        # 6. Body Temperature (Celsius, 30.0 - 45.0)
        temp_val = self._extract_temperature(data)
        if temp_val is not None:
            clamped_temp = self._clamp("body_temperature", temp_val)
            raw["body_temperature"] = clamped_temp
            imputed["body_temperature"] = clamped_temp
        else:
            raw["body_temperature"] = math.nan
            imputed["body_temperature"] = self.features_spec["body_temperature"]["default_imputation"]
            imputed_fields.append("body_temperature")

        # 7. Oxygen Saturation / SpO2 (%, 50 - 100)
        spo2_val = self._extract_spo2(data)
        if spo2_val is not None:
            clamped_spo2 = self._clamp("oxygen_saturation", spo2_val)
            raw["oxygen_saturation"] = clamped_spo2
            imputed["oxygen_saturation"] = clamped_spo2
        else:
            raw["oxygen_saturation"] = math.nan
            imputed["oxygen_saturation"] = self.features_spec["oxygen_saturation"]["default_imputation"]
            imputed_fields.append("oxygen_saturation")

        # 8. BMI (kg/m^2, 10.0 - 70.0)
        bmi_val = self._extract_bmi(data)
        if bmi_val is not None:
            clamped_bmi = self._clamp("bmi", bmi_val)
            raw["bmi"] = clamped_bmi
            imputed["bmi"] = clamped_bmi
        else:
            raw["bmi"] = math.nan
            imputed["bmi"] = self.features_spec["bmi"]["default_imputation"]
            imputed_fields.append("bmi")

        return raw, imputed, imputed_fields

    def _clamp(self, feature_name: str, value: float) -> float:
        """Clamps a numeric feature to its physiological boundaries defined in schema."""
        spec = self.features_spec.get(feature_name, {})
        min_val = spec.get("min_val", -float("inf"))
        max_val = spec.get("max_val", float("inf"))
        return round(max(min_val, min(max_val, float(value))), 2)

    def _extract_numeric(self, data: Dict[str, Any], keys: List[str]) -> Optional[float]:
        for k in keys:
            if k in data and data[k] is not None:
                val = data[k]
                if isinstance(val, (int, float)) and not math.isnan(val):
                    return float(val)
                if isinstance(val, str):
                    m = re.search(r"[-+]?\d*\.?\d+", val)
                    if m:
                        try:
                            return float(m.group())
                        except ValueError:
                            pass
        return None

    def _extract_age(self, data: Dict[str, Any]) -> Optional[float]:
        # Direct age
        age = self._extract_numeric(data, ["age", "patient_age"])
        if age is not None:
            return age

        # From date of birth
        dob = data.get("date_of_birth") or data.get("dob")
        if dob:
            if isinstance(dob, str):
                try:
                    dob = date.fromisoformat(dob[:10])
                except Exception:
                    dob = None
            if isinstance(dob, date):
                today = date.today()
                years = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
                return float(years)
        return None

    def _extract_sex(self, data: Dict[str, Any]) -> Optional[float]:
        val = data.get("sex") or data.get("gender")
        if val is not None:
            if isinstance(val, (int, float)):
                return 1.0 if val == 1 else (0.0 if val == 0 else 0.5)
            s = str(val).strip().lower()
            if s in ["m", "male", "man"]:
                return 1.0
            if s in ["f", "female", "woman"]:
                return 0.0
            if s in ["other", "neutral", "non-binary", "nb"]:
                return 0.5
        return None

    def _extract_bp(self, data: Dict[str, Any]) -> Tuple[Optional[float], Optional[float]]:
        # Combined string e.g. "120/80", "135/85 mmHg"
        bp_str = data.get("blood_pressure") or data.get("bp")
        if bp_str and isinstance(bp_str, str):
            match = re.search(r"(\d{2,3})\s*[/\\-]\s*(\d{2,3})", bp_str)
            if match:
                return float(match.group(1)), float(match.group(2))

        sys_val = self._extract_numeric(data, ["systolic_bp", "systolic", "sbp", "bp_sys"])
        dia_val = self._extract_numeric(data, ["diastolic_bp", "diastolic", "dbp", "bp_dia"])
        return sys_val, dia_val

    def _extract_temperature(self, data: Dict[str, Any]) -> Optional[float]:
        for k in ["body_temperature", "temperature", "temp"]:
            if k in data and data[k] is not None:
                val = data[k]
                is_f = False
                num_val = None

                if isinstance(val, str):
                    lower = val.lower()
                    if "f" in lower or "fahrenheit" in lower:
                        is_f = True
                    m = re.search(r"[-+]?\d*\.?\d+", val)
                    if m:
                        num_val = float(m.group())
                elif isinstance(val, (int, float)):
                    num_val = float(val)

                if num_val is not None:
                    # Auto-detect Fahrenheit if not explicit: humans rarely have core temp > 45°C
                    if is_f or num_val > 45.0:
                        num_val = (num_val - 32.0) * 5.0 / 9.0
                    return num_val
        return None

    def _extract_glucose(self, data: Dict[str, Any]) -> Optional[float]:
        for k in ["glucose", "blood_glucose", "blood_sugar", "fasting_glucose", "fbs"]:
            if k in data and data[k] is not None:
                val = data[k]
                if isinstance(val, str):
                    lower = val.lower()
                    m = re.search(r"[-+]?\d*\.?\d+", val)
                    if m:
                        num = float(m.group())
                        # If unit is mmol/L (typical range 3.0-25.0)
                        if "mmol" in lower or num < 25.0:
                            num = num * 18.0182
                        return num
                elif isinstance(val, (int, float)):
                    num = float(val)
                    if num < 25.0:  # Assumed mmol/L
                        num = num * 18.0182
                    return num
        return None

    def _extract_spo2(self, data: Dict[str, Any]) -> Optional[float]:
        val = self._extract_numeric(data, ["oxygen_saturation", "spo2", "oximeter", "o2_sat"])
        if val is not None:
            if val <= 1.0:  # Fraction e.g. 0.98 -> 98%
                val = val * 100.0
            return val
        return None

    def _extract_bmi(self, data: Dict[str, Any]) -> Optional[float]:
        # Direct BMI
        bmi = self._extract_numeric(data, ["bmi", "body_mass_index"])
        if bmi is not None:
            return bmi

        # From weight and height
        weight = self._extract_numeric(data, ["weight", "weight_kg", "wt"])
        height = self._extract_numeric(data, ["height", "height_cm", "height_m", "ht"])

        if weight and height:
            # Normalize height to meters
            h_meters = height / 100.0 if height > 3.0 else height
            if h_meters > 0.4:
                return weight / (h_meters ** 2)

        return None

    # -----------------------------------------------------------------------
    # End-to-End Dynamic Preprocessing Pipeline
    # -----------------------------------------------------------------------

    def preprocess(
        self,
        input_data: Union[Dict[str, Any], str, List[str]],
        patient_profile_data: Optional[Dict[str, Any]] = None,
        patient: Optional[Any] = None,
    ) -> PreprocessedClinicalData:
        """
        Executes full preprocessing:
        1. Extracts unstructured symptoms with bounded negation and fuzzy canonicalization.
        2. Normalizes, physiologically clamps, and imputes clinical vitals.
        3. Constructs dual deterministic feature vectors (imputed vs raw NaN) strictly aligned with schema.json.
        """
        if patient is not None:
            extracted_patient_data: Dict[str, Any] = {}
            if isinstance(patient, dict):
                extracted_patient_data.update(patient)
            else:
                for attr in ["date_of_birth", "gender", "age", "sex"]:
                    if hasattr(patient, attr):
                        extracted_patient_data[attr] = getattr(patient, attr)
                if hasattr(patient, "patient_profile"):
                    profile = getattr(patient, "patient_profile")
                    if profile:
                        if hasattr(profile, "date_of_birth") and profile.date_of_birth:
                            extracted_patient_data["date_of_birth"] = profile.date_of_birth
                        if hasattr(profile, "gender") and profile.gender:
                            extracted_patient_data["gender"] = profile.gender
            if patient_profile_data is None:
                patient_profile_data = extracted_patient_data
            else:
                merged = dict(extracted_patient_data)
                merged.update(patient_profile_data)
                patient_profile_data = merged

        # Normalize container
        if isinstance(input_data, str):
            symptoms_raw: Any = input_data
            vitals_raw: Dict[str, Any] = {}
        elif isinstance(input_data, list):
            symptoms_raw = input_data
            vitals_raw = {}
        elif isinstance(input_data, dict):
            symptoms_raw = input_data.get("symptoms") or input_data.get("text") or []
            vitals_raw = dict(input_data.get("vitals", {}))
            # Also merge top-level numeric vitals
            for k in [
                "age",
                "sex",
                "gender",
                "systolic_bp",
                "diastolic_bp",
                "blood_pressure",
                "bp",
                "heart_rate",
                "glucose",
                "body_temperature",
                "temperature",
                "temp",
                "oxygen_saturation",
                "spo2",
                "bmi",
                "height",
                "weight",
                "date_of_birth",
            ]:
                if k in input_data and k not in vitals_raw:
                    vitals_raw[k] = input_data[k]
        else:
            symptoms_raw = []
            vitals_raw = {}

        # 1. Parse symptoms
        symptom_res = self.parse_symptoms(symptoms_raw)
        canonical_symptoms = symptom_res["canonical_symptoms"]
        negated_symptoms = symptom_res["negated_symptoms"]
        unmapped_tokens = symptom_res["unmapped_tokens"]
        symptom_vector = symptom_res["symptom_vector"]

        # 2. Parse vitals
        raw_vitals, imputed_vitals, imputed_fields = self.parse_vitals(
            vitals_data=vitals_raw,
            patient_profile_data=patient_profile_data,
        )

        # 3. Construct dual representations in strict schema.json order
        imputed_vector: List[float] = []
        raw_vector: List[float] = []
        imputed_dict: Dict[str, float] = {}
        raw_dict: Dict[str, float] = {}

        for feat in self.feature_order:
            spec = self.features_spec.get(feat, {})
            category = spec.get("category", "")

            if category == "symptom":
                # Symptom value is binary 0.0 or 1.0 (both in raw and imputed)
                val = symptom_vector.get(feat, 0.0)
                imputed_vector.append(val)
                raw_vector.append(val)
                imputed_dict[feat] = val
                raw_dict[feat] = val
            else:
                # Vital / demographic
                imp_val = imputed_vitals.get(feat, spec.get("default_imputation", 0.0))
                r_val = raw_vitals.get(feat, math.nan)

                imputed_vector.append(float(imp_val))
                raw_vector.append(float(r_val))
                imputed_dict[feat] = float(imp_val)
                raw_dict[feat] = float(r_val)

        return PreprocessedClinicalData(
            feature_order=list(self.feature_order),
            imputed_vector=imputed_vector,
            raw_vector=raw_vector,
            imputed_dict=imputed_dict,
            raw_dict=raw_dict,
            canonical_symptoms=canonical_symptoms,
            negated_symptoms=negated_symptoms,
            unmapped_tokens=unmapped_tokens,
            vitals_raw=vitals_raw,
            vitals_imputed=imputed_vitals,
            imputed_fields=imputed_fields,
            schema_version=self.version,
        )


# ---------------------------------------------------------------------------
# Singleton & Backward-Compatible Service Hooks
# ---------------------------------------------------------------------------

_PREPROCESSOR_V1_INSTANCE: Optional[ClinicalPreprocessor] = None
_PREPROCESSOR_V2_INSTANCE: Optional[ClinicalPreprocessor] = None


def get_preprocessor(version: Optional[str] = None) -> ClinicalPreprocessor:
    """
    Returns preprocessor singleton instance.
    Defaults to v1.0.0 when version is None or '1.0.0' for backward compatibility
    with existing v1 ML model tests, or v2.0.0 when version='2.0.0'.
    """
    global _PREPROCESSOR_V1_INSTANCE, _PREPROCESSOR_V2_INSTANCE
    if version in ("2.0.0", "v2"):
        if _PREPROCESSOR_V2_INSTANCE is None:
            _PREPROCESSOR_V2_INSTANCE = ClinicalPreprocessor(version="2.0.0")
        return _PREPROCESSOR_V2_INSTANCE

    if _PREPROCESSOR_V1_INSTANCE is None:
        _PREPROCESSOR_V1_INSTANCE = ClinicalPreprocessor(version="1.0.0")
    return _PREPROCESSOR_V1_INSTANCE


def get_preprocessor_v2() -> ClinicalPreprocessor:
    """Convenience accessor for v2.0.0 preprocessor with 154 symptoms."""
    return get_preprocessor(version="2.0.0")


def preprocess_clinical_input(
    data: Union[Dict[str, Any], str, List[str]],
    patient: Optional[Any] = None,
) -> PreprocessedClinicalData:
    """
    Convenience backward-compatible entry point.
    Resolves patient profile metadata if patient or patient_id is available.
    """
    preprocessor = get_preprocessor()
    patient_profile_data: Dict[str, Any] = {}

    # Extract patient profile if model instance or patient_id is provided
    if patient is not None and hasattr(patient, "patient_profile"):
        profile = getattr(patient, "patient_profile", None)
        if profile:
            if hasattr(profile, "date_of_birth") and profile.date_of_birth:
                patient_profile_data["date_of_birth"] = profile.date_of_birth
            if hasattr(profile, "gender") and profile.gender:
                patient_profile_data["gender"] = profile.gender
    elif isinstance(data, dict) and data.get("patient_id"):
        try:
            from apps.accounts.models import User
            target_user = User.objects.filter(id=data["patient_id"]).first()
            if target_user and hasattr(target_user, "patient_profile"):
                profile = getattr(target_user, "patient_profile", None)
                if profile:
                    if hasattr(profile, "date_of_birth") and profile.date_of_birth:
                        patient_profile_data["date_of_birth"] = profile.date_of_birth
                    if hasattr(profile, "gender") and profile.gender:
                        patient_profile_data["gender"] = profile.gender
        except Exception:
            pass  # Non-blocking if Django or DB is unavailable during unit testing

    return preprocessor.preprocess(data, patient_profile_data=patient_profile_data)
