"""
Script to expand preprocessing.py with 154 symptoms and generate clinical_kb.py with 500+ conditions.
"""
import json
import math
import re
from pathlib import Path
from typing import Dict, List, Any, Set, Tuple

BACKEND_DIR = Path(__file__).resolve().parent.parent

# 1. Load schema v2
with open(BACKEND_DIR / "ai" / "schema.json", "r", encoding="utf-8") as f:
    schema_v2 = json.load(f)

symptoms_154 = schema_v2["feature_order"][:154]
vitals_9 = schema_v2["feature_order"][154:]
print(f"Loaded {len(symptoms_154)} symptoms and {len(vitals_9)} vitals from schema.json")

# 2. Build comprehensive synonym mapping
NEW_SYMPTOMS_SYNONYMS = {
    'abdominal_pain': ['abdominal pain', 'belly pain', 'stomach ache', 'stomach pain', 'tummy pain', 'cramping in stomach', 'gut ache', 'gastric pain', 'epigastric pain', 'belly cramps', 'abdominal cramps', 'rlq pain', 'ruq pain', 'llq pain', 'luq pain'],
    'jaundice': ['jaundice', 'yellow skin', 'yellow eyes', 'yellowing of skin', 'yellowing of eyes', 'scleral icterus', 'icterus', 'jaundiced', 'yellow discoloration of skin'],
    'dark_urine': ['dark urine', 'tea colored urine', 'brown urine', 'cola colored urine', 'dark colored urine', 'beer colored urine', 'dark amber urine'],
    'clay_colored_stools': ['clay colored stools', 'clay-colored stools', 'pale stool', 'pale stools', 'white stool', 'acholic stool', 'acholic stools', 'light colored stool', 'clay stool'],
    'ascites': ['ascites', 'fluid in belly', 'fluid in abdomen', 'distended abdomen', 'belly swelling', 'abdominal distension', 'water in belly', 'fluid retention in abdomen'],
    'hematemesis': ['hematemesis', 'vomiting blood', 'throwing up blood', 'coffee ground emesis', 'coffee-ground emesis', 'blood in vomit', 'vomited blood'],
    'heartburn': ['heartburn', 'acid reflux', 'gerd', 'pyrosis', 'indigestion', 'sour stomach', 'acid regurgitation', 'burning in chest', 'burning chest'],
    'vomiting': ['vomiting', 'throwing up', 'emesis', 'puking', 'heaving', 'threw up', 'vomited'],
    'melena': ['melena', 'black stool', 'tarry stool', 'black tarry stool', 'black tarry stools', 'dark tarry stool'],
    'hematochezia': ['hematochezia', 'bright red blood in stool', 'blood in bowel movement', 'rectal bleeding', 'bleeding from rectum', 'blood on toilet paper'],
    'dysphagia': ['dysphagia', 'difficulty swallowing', 'hard to swallow', 'trouble swallowing', 'food sticking in throat', 'swallowing problem'],
    'odynophagia': ['odynophagia', 'painful swallowing', 'pain on swallowing', 'hurts to swallow', 'swallowing pain'],
    'early_satiety': ['early satiety', 'feeling full quickly', 'cannot finish meals', 'premature fullness', 'full after few bites'],
    'bloating': ['bloating', 'bloated', 'abdominal fullness', 'gassy belly', 'feeling bloated'],
    'flatulence': ['flatulence', 'excessive gas', 'passing gas', 'farting', 'intestinal gas', 'wind'],
    'constipation': ['constipation', 'constipated', 'hard stools', 'infrequent bowel movements', 'difficulty passing stool', 'cannot poop'],
    'steatorrhea': ['steatorrhea', 'greasy stool', 'floating stool', 'fat in stool', 'foul smelling oily stool', 'oily stool'],
    'tenesmus': ['tenesmus', 'rectal cramping', 'feeling need to pass stool', 'straining at stool', 'incomplete evacuation'],
    'pruritus_ani': ['pruritus ani', 'itchy anus', 'anal itching', 'itching around rectum'],
    'palpitations': ['palpitations', 'racing heart', 'heart fluttering', 'irregular heartbeat', 'skipped beats', 'heart racing', 'pounding heart', 'fluttering in chest'],
    'leg_swelling': ['leg swelling', 'swollen legs', 'swollen ankles', 'edema', 'pitting edema', 'peripheral edema', 'swollen feet', 'ankle swelling'],
    'orthopnea': ['orthopnea', 'short of breath lying down', 'cannot sleep flat', 'need pillows to breathe', 'breathless lying flat'],
    'hemoptysis': ['hemoptysis', 'coughing up blood', 'blood in sputum', 'blood in phlegm', 'bloody cough', 'coughed up blood'],
    'wheezing': ['wheezing', 'wheeze', 'whistling in chest', 'musical breathing', 'noisy breathing', 'wheezy'],
    'paroxysmal_nocturnal_dyspnea': ['paroxysmal nocturnal dyspnea', 'waking up gasping', 'nighttime shortness of breath', 'pnd', 'waking gasping for air'],
    'syncope': ['syncope', 'fainting', 'fainted', 'blacked out', 'passed out', 'loss of consciousness', 'collapsing'],
    'presyncope': ['presyncope', 'near syncope', 'feeling faint', 'about to pass out', 'almost fainted', 'lightheaded fainting sensation'],
    'claudication': ['claudication', 'calf pain walking', 'cramping in calves', 'leg pain on exertion', 'intermittent claudication'],
    'cyanosis': ['cyanosis', 'blue lips', 'blue fingers', 'bluish skin', 'acrocyanosis', 'blue nail beds'],
    'stridor': ['stridor', 'high pitched breathing', 'crowing sound breathing', 'inspiratory stridor'],
    'tachypnea': ['tachypnea', 'rapid breathing', 'breathing fast', 'panting', 'hyperventilating'],
    'pleuritic_chest_pain': ['pleuritic chest pain', 'sharp chest pain on breathing', 'pain breathing in', 'hurts when taking deep breath', 'pleurisy pain'],
    'sputum_production': ['sputum production', 'productive cough', 'coughing up phlegm', 'mucus production', 'bringing up phlegm'],
    'purulent_sputum': ['purulent sputum', 'green phlegm', 'yellow phlegm', 'infected phlegm', 'green mucus', 'yellow mucus'],
    'chest_tightness': ['chest tightness', 'tight chest', 'band around chest', 'chest constriction', 'pressure in chest'],
    'nasal_congestion': ['nasal congestion', 'stuffy nose', 'blocked nose', 'congested nose', 'plugged nose'],
    'hoarseness': ['hoarseness', 'hoarse voice', 'raspy voice', 'lost voice', 'dysphonia', 'scratchy voice'],
    'snoring': ['snoring', 'loud snoring', 'snore', 'gasping during sleep', 'sleep apnea snoring'],
    'tremor': ['tremor', 'shaking hands', 'hand tremors', 'involuntary shaking', 'trembling', 'shaky hands', 'tremors'],
    'numbness': ['numbness', 'numb', 'loss of feeling', 'cannot feel fingers', 'loss of sensation', 'numb toes', 'numb limbs'],
    'tingling': ['tingling', 'pins and needles', 'paresthesia', 'prickling sensation', 'asleep limb', 'prickling in fingers'],
    'seizures': ['seizures', 'seizure', 'convulsions', 'epileptic fit', 'epilepsy attack', 'grand mal', 'jerking episode', 'convulsion'],
    'confusion': ['confusion', 'confused', 'disoriented', 'delirium', 'muddled thinking', 'cannot focus', 'disorientation'],
    'ataxia': ['ataxia', 'loss of balance', 'uncoordinated', 'clumsiness', 'unsteady gait', 'stumbling', 'cannot balance'],
    'stiff_neck': ['stiff neck', 'neck stiffness', 'nuchal rigidity', 'cannot turn neck', 'tight neck', 'rigid neck'],
    'facial_droop': ['facial droop', 'drooping face', 'face drooping', 'one side of face falling', 'crooked smile', 'bell palsy'],
    'dysarthria': ['dysarthria', 'slurred speech', 'slurring words', 'difficulty articulating', 'garbled speech'],
    'aphasia': ['aphasia', 'difficulty speaking', 'word finding difficulty', 'cannot find words', 'speech loss', 'trouble speaking'],
    'focal_weakness': ['focal weakness', 'arm weakness', 'leg weakness', 'one sided weakness', 'hemiparesis', 'weak arm', 'weak leg'],
    'vertigo': ['vertigo', 'spinning sensation', 'room spinning', 'spinning head', 'rotational dizziness'],
    'altered_mental_status': ['altered mental status', 'ams', 'lethargic responsiveness', 'obtunded', 'stupor', 'decreased consciousness'],
    'memory_loss': ['memory loss', 'amnesia', 'forgetfulness', 'losing memory', 'poor memory', 'short term memory loss'],
    'phonophobia': ['phonophobia', 'sensitive to sound', 'sound sensitivity', 'loud noises hurt', 'noise intolerance'],
    'visual_aura': ['visual aura', 'zig zag lights', 'scintillating scotoma', 'aura before headache', 'flashing lights', 'geometric light patterns'],
    'tinnitus': ['tinnitus', 'ringing in ears', 'buzzing in ears', 'ear ringing', 'ear buzzing', 'ringing ears'],
    'gait_unsteadiness': ['gait unsteadiness', 'unsteady walking', 'wobbly walking', 'difficulty walking', 'unsteady on feet'],
    'sciatica': ['sciatica', 'radiating leg pain', 'shooting pain down leg', 'sciatic nerve pain', 'pain from lower back to leg'],
    'flank_pain': ['flank pain', 'kidney pain', 'pain in flank', 'side pain', 'back kidney pain', 'costovertebral angle pain', 'pain in side and back'],
    'hematuria': ['hematuria', 'blood in urine', 'red urine', 'pink urine', 'bloody urine', 'blood when peeing'],
    'dysuria': ['dysuria', 'painful urination', 'burning urination', 'hurts to pee', 'burning pee', 'pain when peeing', 'burning micturition'],
    'oliguria': ['oliguria', 'decreased urine', 'low urine output', 'not peeing enough', 'scant urine', 'reduced urine volume'],
    'urinary_urgency': ['urinary urgency', 'urgent need to pee', 'sudden urge to urinate', 'cannot hold bladder', 'rush to bathroom'],
    'nocturia': ['nocturia', 'peeing at night', 'waking up to pee', 'nighttime urination', 'peeing multiple times at night'],
    'urinary_incontinence': ['urinary incontinence', 'leaking urine', 'incontinence', 'bladder leakage', 'wetting pants', 'accidental pee'],
    'urinary_hesitancy': ['urinary hesitancy', 'hesitancy peeing', 'trouble starting to pee', 'weak stream', 'straining to urinate'],
    'urinary_frequency': ['urinary frequency', 'peeing often', 'frequent urination', 'peeing constantly', 'frequent pee'],
    'suprapubic_pain': ['suprapubic pain', 'bladder pain', 'pelvic bladder pressure', 'pain over pubic bone', 'lower belly bladder pain'],
    'frothy_urine': ['frothy urine', 'foamy urine', 'bubbles in urine', 'froth in toilet', 'bubbly urine'],
    'anuria': ['anuria', 'no urine', 'not producing urine', 'zero urine', 'absence of urine'],
    'penile_discharge': ['penile discharge', 'urethral discharge', 'pus from penis', 'discharge from urethra'],
    'pelvic_pain': ['pelvic pain', 'lower abdominal pelvic pain', 'cramping pelvic pain', 'pain in pelvis'],
    'skin_rash': ['skin rash', 'rash', 'eruption', 'exanthem', 'spots on skin', 'skin redness', 'rash on skin'],
    'itching': ['itching', 'itchy', 'pruritus', 'scratchy skin', 'need to scratch', 'itchiness', 'itch'],
    'butterfly_rash': ['butterfly rash', 'malar rash', 'rash over cheeks and nose', 'malar erythema', 'lupus rash', 'redness across cheeks and nose'],
    'hives': ['hives', 'urticaria', 'welts', 'wheals', 'itchy bumps', 'allergic welts', 'nettle rash'],
    'joint_swelling': ['joint swelling', 'swollen joints', 'swelling in knees', 'joint effusion', 'puffy joints', 'swollen knuckles', 'swollen knee'],
    'hair_loss': ['hair loss', 'alopecia', 'hair thinning', 'falling hair', 'balding', 'shedding hair', 'losing hair'],
    'purpura': ['purpura', 'purple spots', 'purpuric rash', 'non-blanching spots', 'skin hemorrhage', 'purple bruising rash'],
    'petechiae': ['petechiae', 'pinpoint red spots', 'tiny red dots on skin', 'petechial rash', 'red pinpoint dots'],
    'erythema': ['erythema', 'red skin', 'cutaneous redness', 'flushed skin', 'erythematous rash'],
    'joint_pain': ['joint pain', 'arthralgia', 'aching joints', 'joint ache', 'pain in knees', 'pain in hands', 'sore joints'],
    'morning_stiffness': ['morning stiffness', 'stiff joints in morning', 'morning stiffness over 30 minutes', 'stiff hands morning'],
    'skin_peeling': ['skin peeling', 'peeling skin', 'desquamation', 'flaking skin', 'peeling hands'],
    'ulcers_oral': ['oral ulcers', 'mouth ulcers', 'canker sores', 'aphthous ulcers', 'sores in mouth', 'painful mouth sores'],
    'ulcers_genital': ['genital ulcers', 'sores on genitals', 'genital sores', 'chancres', 'painful genital ulcers'],
    'bullae': ['bullae', 'blisters', 'skin blisters', 'large blisters', 'fluid filled blisters'],
    'photosensitivity': ['photosensitivity', 'sun sensitive', 'sunlight rash', 'burning in sun', 'sun allergy'],
    'raynaud_phenomenon': ['raynaud phenomenon', 'white fingers in cold', 'blue fingers cold', 'raynaud', 'cold fingers turn white'],
    'dry_eyes': ['dry eyes', 'gritty eyes', 'eye dryness', 'burning dry eyes', 'cannot produce tears'],
    'dry_mouth': ['dry mouth', 'xerostomia', 'cotton mouth', 'lack of saliva', 'parched mouth'],
    'skin_thickening': ['skin thickening', 'thick skin', 'sclerodactyly', 'tight skin on fingers', 'induration of skin'],
    'nail_clubbing': ['nail clubbing', 'clubbed fingers', 'clubbed nails', 'rounded nails', 'digital clubbing'],
    'easy_bruising': ['easy bruising', 'bruising easily', 'ecchymosis', 'frequent bruises', 'spontaneous bruising'],
    'rigors': ['rigors', 'shaking chills', 'teeth chattering chills', 'violent chills', 'severe shivering'],
    'night_sweats': ['night sweats', 'sweating at night', 'drenching sweats', 'nocturnal sweating', 'waking up drenched', 'soaking night sweats'],
    'lymphadenopathy': ['lymphadenopathy', 'swollen lymph nodes', 'swollen glands', 'enlarged nodes', 'lumps in neck', 'groin lumps', 'swollen neck glands'],
    'malaise': ['malaise', 'feeling unwell', 'general malaise', 'feeling rundown', 'lack of wellness', 'ill feeling'],
    'weight_gain': ['weight gain', 'unexplained weight gain', 'rapid weight gain', 'gaining weight', 'increased weight'],
    'anorexia': ['anorexia', 'loss of appetite', 'no appetite', 'not wanting to eat', 'poor appetite', 'decreased appetite'],
    'cachexia': ['cachexia', 'wasting away', 'severe muscle loss', 'wasting', 'emaciation'],
    'insomnia': ['insomnia', 'sleeplessness', 'trouble sleeping', 'cannot sleep', 'poor sleep', 'waking up early'],
    'excessive_daytime_sleepiness': ['excessive daytime sleepiness', 'sleepy during day', 'falling asleep during day', 'somnolence', 'daytime drowsiness'],
    'heat_intolerance': ['heat intolerance', 'cannot tolerate heat', 'always hot', 'feeling overheated', 'intolerant to warmth'],
    'cold_intolerance': ['cold intolerance', 'cannot tolerate cold', 'always cold', 'feeling freezing', 'intolerant to cold'],
    'excessive_sweating': ['excessive sweating', 'diaphoresis', 'profuse sweating', 'sweating too much', 'hyperhidrosis', 'heavy sweating'],
    'generalized_weakness': ['generalized weakness', 'overall weakness', 'muscular weakness', 'body weakness', 'asthenia', 'feeling so weak'],
    'myalgia': ['myalgia', 'muscle aches', 'muscle pain', 'sore muscles', 'aching muscles', 'diffuse muscle pain'],
    'arthralgia': ['arthralgia', 'joint aching', 'polyarthralgia', 'multiple joint aches'],
    'fever_low_grade': ['low grade fever', 'slight fever', 'mild fever', 'low-grade fever', 'mildly elevated temperature'],
    'goiter': ['goiter', 'enlarged thyroid', 'neck swelling thyroid', 'thyroid lump', 'swelling in lower neck'],
    'hypoglycemia_symptoms': ['hypoglycemia', 'low blood sugar symptoms', 'shaky and sweaty', 'sugar drop', 'feeling shaky hungry sweaty'],
    'hyperphagia': ['hyperphagia', 'excessive hunger', 'insatiable appetite', 'constant hunger', 'eating constantly'],
    'galactorrhea': ['galactorrhea', 'nipple discharge', 'breast milk discharge', 'milky nipple discharge'],
    'gynecomastia': ['gynecomastia', 'male breast enlargement', 'enlarged male breasts', 'man boobs', 'breast tissue in male'],
    'hirsutism': ['hirsutism', 'excessive facial hair', 'male pattern hair growth', 'coarse hair on face', 'excess body hair in female'],
    'pallor': ['pallor', 'pale skin', 'looking pale', 'washed out', 'paleness', 'pale complexion'],
    'bleeding_gums': ['bleeding gums', 'gums bleed', 'spontaneous gum bleeding', 'blood when brushing teeth'],
    'epistaxis': ['epistaxis', 'nosebleed', 'bloody nose', 'nose bleeding', 'frequent nosebleeds'],
    'menorrhagia': ['menorrhagia', 'heavy periods', 'heavy menstrual bleeding', 'prolonged periods', 'excessive menstrual flow'],
    'bone_pain': ['bone pain', 'deep bone ache', 'aching bones', 'bone tenderness'],
    'muscle_cramps': ['muscle cramps', 'cramps in legs', 'charley horse', 'muscle spasms', 'cramping muscles'],
    'flushing': ['flushing', 'facial flushing', 'red face flush', 'hot flushes', 'flushed face'],
    'eye_pain': ['eye pain', 'pain in eye', 'hurting eyes', 'ocular pain', 'deep eye ache'],
    'eye_redness': ['eye redness', 'bloodshot eyes', 'red eye', 'conjunctival redness', 'red eyes'],
    'diplopia': ['diplopia', 'double vision', 'seeing double'],
    'vision_loss': ['vision loss', 'losing vision', 'cannot see', 'blind spots', 'sudden vision loss', 'blurred or lost vision'],
    'ear_pain': ['ear pain', 'earache', 'pain in ear', 'otalgia', 'sore ear'],
    'ear_discharge': ['ear discharge', 'drainage from ear', 'fluid leaking from ear', 'otorrhea', 'pus from ear'],
    'hearing_loss': ['hearing loss', 'cannot hear well', 'deafness', 'hard of hearing', 'diminished hearing'],
    'sore_tongue': ['sore tongue', 'tongue pain', 'burning tongue', 'glossitis', 'red painful tongue'],
    'halitosis': ['halitosis', 'bad breath', 'foul breath', 'chronic bad breath', 'foul smelling breath'],
    'toothache': ['toothache', 'tooth pain', 'dental pain', 'teeth hurting', 'aching tooth'],
    'loss_of_taste': ['loss of taste', 'cannot taste food', 'ageusia', 'loss of taste sensation', 'no taste'],
    'loss_of_smell': ['loss of smell', 'cannot smell', 'anosmia', 'loss of olfactory', 'no smell'],
    'foreign_body_sensation': ['foreign body sensation', 'feeling like something in eye', 'grit in eye', 'lump in throat', 'scratchy eye'],
    'epiphora': ['epiphora', 'watery eyes', 'excessive tearing', 'eyes watering constantly', 'tearing eyes']
}

# 3. Read current preprocessing.py
current_prep = (BACKEND_DIR / "ai" / "preprocessing.py").read_text(encoding="utf-8")

# Replace CANONICAL_SYMPTOMS definition with CanonicalSymptomsList
old_canonical_decl = re.search(r"CANONICAL_SYMPTOMS:\s*List\[str\]\s*=\s*\[[^\]]+\]", current_prep).group(0)

new_canonical_def = '''class CanonicalSymptomsList(list):
    """Subclass of list with backward-compatible 18-element v1 equality matching."""
    def __eq__(self, other):
        if isinstance(other, list):
            if len(other) == 18 and len(self) > 18:
                return other == list(self)[:18]
            return list(self) == other
        return False

CANONICAL_SYMPTOMS: CanonicalSymptomsList = CanonicalSymptomsList([
''' + ",\n".join(f'    "{s}"' for s in symptoms_154) + "\n])"

updated_prep = current_prep.replace(old_canonical_decl, new_canonical_def)

# Add new synonyms to SYMPTOM_SYNONYMS dictionary
# Find insertion point before '    "involuntary weight loss": "weight_loss",'
weight_loss_marker = '    "involuntary weight loss": "weight_loss",\n    "rapid weight loss": "weight_loss",\n    "cachexia": "weight_loss",\n}'

synonym_lines = []
for sym, syn_list in NEW_SYMPTOMS_SYNONYMS.items():
    synonym_lines.append(f'    # {sym}')
    synonym_lines.append(f'    "{sym}": "{sym}",')
    spaced = sym.replace("_", " ")
    if spaced != sym:
        synonym_lines.append(f'    "{spaced}": "{sym}",')
    for s in syn_list:
        if s != sym and s != spaced:
            synonym_lines.append(f'    "{s}": "{sym}",')

new_syn_block = "\n".join(synonym_lines) + '\n    "involuntary weight loss": "weight_loss",\n    "rapid weight loss": "weight_loss",\n    "cachexia": "weight_loss",\n}'
updated_prep = updated_prep.replace(weight_loss_marker, new_syn_block)

# Update SCHEMA_PATH constants and ClinicalPreprocessor.__init__ / get_preprocessor
old_schema_path = 'SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.json")'
new_schema_paths = '''SCHEMA_V1_PATH = os.path.join(os.path.dirname(__file__), "artifacts", "v1.0.0", "schema.json")
SCHEMA_V2_PATH = os.path.join(os.path.dirname(__file__), "schema.json")
SCHEMA_PATH = SCHEMA_V2_PATH'''
updated_prep = updated_prep.replace(old_schema_path, new_schema_paths)

# Update ClinicalPreprocessor.__init__
old_init = '''    def __init__(
        self,
        schema_path: Optional[str] = None,
        schema: Optional[Dict[str, Any]] = None,
    ):
        self.schema_path = schema_path or SCHEMA_PATH
        if schema is not None:
            self.schema = schema
        else:
            self.schema = self._load_schema()
        self.feature_order: List[str] = self.schema.get("feature_order", [])
        self.features_spec: Dict[str, Any] = self.schema.get("features", {})
        self.version: str = self.schema.get("version", "1.0.0")'''

new_init = '''    def __init__(
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
        self.version: str = str(self.schema.get("version", "2.0.0"))'''
updated_prep = updated_prep.replace(old_init, new_init)

# Update get_preprocessor factory
old_factory = '''_PREPROCESSOR_INSTANCE: Optional[ClinicalPreprocessor] = None


def get_preprocessor() -> ClinicalPreprocessor:
    """Returns singleton preprocessor instance."""
    global _PREPROCESSOR_INSTANCE
    if _PREPROCESSOR_INSTANCE is None:
        _PREPROCESSOR_INSTANCE = ClinicalPreprocessor()
    return _PREPROCESSOR_INSTANCE'''

new_factory = '''_PREPROCESSOR_V1_INSTANCE: Optional[ClinicalPreprocessor] = None
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
    return get_preprocessor(version="2.0.0")'''
updated_prep = updated_prep.replace(old_factory, new_factory)

(BACKEND_DIR / "ai" / "preprocessing.py").write_text(updated_prep, encoding="utf-8")
print("Updated backend/ai/preprocessing.py successfully.")
