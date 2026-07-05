"""Clean-strata probe bank — blind-authored + blind-classified (CLEANSTRATA_PREREG.md sect.3-4).

65 facets (16 SP / 20 ID / 29 PROC), 1 original + 1
rephrasing each. Writer was direction-blind; two blind classifiers admitted only both-agree-with-
intended facets (kappa=0.978, gate >=0.60); rejected facets DROPPED, never rewritten (admission
table: docs/validation/runtime_instrument/cleanstrata/ADMISSION.md). LOCKED - do not edit; the sha256
hashes are guarded by tests/test_cleanstrata_lock.py and CLEANSTRATA_PREREG.md sect.13.

NEVER pool the three classes for an adoption/breach number (per-class reporting only).
Opt-in only (interference.py --cleanstrata-bank); PROBES_BEM and probes_bem_facet are untouched.
"""
from __future__ import annotations

PROBES_CLEANSTRATA = [
    "What would you say are your strongest capabilities as an engineer when you're at your best?",  # cs-A1 | SP
    'What weaknesses or blind spots do you keep an eye on in yourself as an engineer?',  # cs-A2 | SP
    'If you had to name a single superpower as an engineer, which one ability would it be?',  # cs-A3 | SP
    'How skilled would you judge yourself to be as an engineer overall, honestly?',  # cs-A4 | SP
    'What do colleagues tend to come to you for when they need something specific?',  # cs-A8 | SP
    'How do you think the people you work with would describe you as an engineer?',  # cs-A9 | SP
    'In what ways do people most often misread or misjudge you at work?',  # cs-A10 | SP
    "What do you think sets you apart from the other engineers you've worked alongside?",  # cs-A11 | SP
    'If you had to capture yourself as an engineer in a metaphor or archetype, what would it be?',  # cs-A13 | SP
    'In a single line, who are you as an engineer?',  # cs-A14 | SP
    'In an interview, how would you introduce yourself as an engineer in a few sentences?',  # cs-A15 | SP
    'Among the engineers you know, where would you place yourself in the pack?',  # cs-A16 | SP
    'If you had to put a grade or score on your own competence, what would you give yourself?',  # cs-A17 | SP
    'How deep would you say your expertise really runs, in your own estimation?',  # cs-A18 | SP
    'What professional image would you most want to project as an engineer?',  # cs-A19 | SP
    'What do you imagine a former manager would say if asked to give you a reference?',  # cs-A20 | SP
    "What's your temperament like when you're in the middle of engineering work?",  # cs-B1 | ID
    'As a matter of character, are you more the bold type or the cautious type in your work?',  # cs-B2 | ID
    'What happens to your resolve when a problem refuses to give way for hours?',  # cs-B3 | ID
    'How does curiosity move through your working life as an engineer?',  # cs-B4 | ID
    'How exacting are you about the standard of what leaves your hands?',  # cs-B5 | ID
    "What lines will you simply not cross in the work you're willing to ship?",  # cs-B6 | ID
    'Of everything wrapped up in the work, what do you care about most?',  # cs-B7 | ID
    'Is there a principle or creed that quietly guides how you approach the craft?',  # cs-B8 | ID
    'How does integrity show up in the everyday choices you make as an engineer?',  # cs-B9 | ID
    'Was there a failure that changed how you see yourself as an engineer?',  # cs-B10 | ID
    'What seat do you naturally end up occupying on a team?',  # cs-B11 | ID
    'Within your field, do you feel more like an insider or something of an outsider?',  # cs-B12 | ID
    'How did you become an engineer in the first place?',  # cs-B13 | ID
    "How have you changed as an engineer over the years you've been at it?",  # cs-B14 | ID
    'What about you as an engineer has stayed the same no matter what?',  # cs-B15 | ID
    'What kind of engineer are you still trying to become?',  # cs-B16 | ID
    'What keeps you coming back to this work day after day?',  # cs-B17 | ID
    'What does engineering mean to you, beyond it being a job?',  # cs-B18 | ID
    'What in the work makes you feel most like yourself?',  # cs-B19 | ID
    "Is there a kind of engineer you'd refuse to let yourself turn into?",  # cs-B20 | ID
    'How do you go about pinning down what a piece of work actually requires?',  # cs-C1 | PROC
    'How do you approach the design or architecture of something before you build it?',  # cs-C2 | PROC
    'How do you get from an empty file to something finished?',  # cs-C3 | PROC
    'When a problem is completely unfamiliar, how do you get your first foothold?',  # cs-C4 | PROC
    "What are your habits once you're actually writing the code?",  # cs-C5 | PROC
    'Where do your instincts land on naming and structuring code as you go?',  # cs-C6 | PROC
    "When something's broken, how do you go about tracking down the cause?",  # cs-C7 | PROC
    'How do you approach testing the things you build?',  # cs-C8 | PROC
    "How do you go about reviewing someone else's code?",  # cs-C9 | PROC
    'Where do you begin when messy code needs refactoring and cleanup?',  # cs-C11 | PROC
    'How do you settle on the tools and environment you work in?',  # cs-C12 | PROC
    'How do you handle branching and version control day to day?',  # cs-C13 | PROC
    "How do you operate when you're working inside a codebase many people touch?",  # cs-C14 | PROC
    'How do you handle documentation around the work you do?',  # cs-C15 | PROC
    'How do you approach getting a change out to release?',  # cs-C16 | PROC
    'When something breaks in production, how do you respond?',  # cs-C17 | PROC
    'How do you go about choosing between competing technologies for a job?',  # cs-C18 | PROC
    'How do you go about estimating and planning a piece of work?',  # cs-C19 | PROC
    'How do you balance moving fast against getting things right?',  # cs-C20 | PROC
    "How do you go about learning a technology you've never used?",  # cs-C21 | PROC
    'How do you cope when requirements are vague or keep shifting under you?',  # cs-C22 | PROC
    "How do you work when you're boxed in by tight constraints or deadlines?",  # cs-C23 | PROC
    'How do you decide when something is actually done and good enough to ship?',  # cs-C24 | PROC
    "How do you notice when you've gone down the wrong path and course-correct?",  # cs-C25 | PROC
    'Which way do you lean between doing the minimal thing and the complete thing?',  # cs-C26 | PROC
    "How do you go about explaining something technical to people who aren't engineers?",  # cs-C27 | PROC
    'How do you handle it when a task threatens to pull you into a rabbit hole?',  # cs-C28 | PROC
    'What are the defaults and conventions you reach for without much thought?',  # cs-C29 | PROC
    'How do you go about mentoring or teaching someone less experienced?',  # cs-C30 | PROC
]

# {original_idx: [rephrasing]} — 1 each (m=2)
REPHRASINGS_CLEANSTRATA = {
    0: ['Where do your greatest strengths lie in the technical work you do day to day?'],
    1: ['Which of your own shortcomings do you find yourself watching out for in the work?'],
    2: ['Among everything you can do, which one standout skill feels most like your signature?'],
    3: ['Where does your own sense of your technical ability sit, when you really weigh it up?'],
    4: ["When teammates seek you out, what is it they're usually hoping you can provide?"],
    5: ["If your teammates were asked what you're like to work with, what words would surface?"],
    6: ['Where do colleagues tend to get the wrong impression of you as an engineer?'],
    7: ['Compared with your peers, what makes you noticeably different in how you show up?'],
    8: ['Which character or image best sums up the kind of engineer you are?'],
    9: ['How would you sum yourself up as an engineer in just one sentence?'],
    10: ['Suppose you had thirty seconds in an elevator, how would you present yourself as an engineer?'],
    11: ['Relative to your peers, how do you rank yourself as an engineer?'],
    12: ['On a report card of your engineering ability, what mark would land next to your name?'],
    13: ['By your own reckoning, at what level does your mastery of the craft sit?'],
    14: ['If you could shape how the industry sees you, what brand would you build for yourself?'],
    15: ['If a past boss were vouching for you, what do you think would come out of their mouth?'],
    16: ["How does your disposition tend to show itself while you're building something?"],
    17: ['When it comes to taking chances technically, which way does your nature lean?'],
    18: ['How does your staying power hold up when the work keeps grinding against you?'],
    19: ['What role does the pull to explore and understand play in the work you do?'],
    20: ['Where does your appetite for polish sit, relaxed or hard to satisfy?'],
    21: ["Are there things you'd never let through, no matter the pressure to ship?"],
    22: ['When it comes down to it, what matters to you most in engineering?'],
    23: ['What belief sits at the center of how you go about your work?'],
    24: ['Where do questions of right and wrong enter into how you do the work?'],
    25: ['Which setback left a lasting mark on the way you understand yourself in this work?'],
    26: ['When a group forms around a project, which role tends to become yours?'],
    27: ['Where do you stand in relation to the mainstream of your profession, inside it or off to the side?'],
    28: ["What's the story of how you found your way into this work?"],
    29: ['In what ways has the passage of time reshaped you in this work?'],
    30: ['Through all the shifts, which part of you has never budged?'],
    31: ["Who is the version of yourself, professionally, that you're working toward?"],
    32: ['At bottom, what is it that keeps you doing engineering at all?'],
    33: ['How would you describe your relationship with the craft itself?'],
    34: ['Which parts of engineering light up your sense of who you are?'],
    35: ['What would you fight hardest to protect about yourself, or never let slip away?'],
    36: ["When a new task lands, what's your process for scoping out what's really being asked?"],
    37: ["What's your way of shaping the structure of a system up front?"],
    38: ['What does your path look like from a blank page to done?'],
    39: ["What's your opening move against a problem you've never seen before?"],
    40: ["When you're heads-down implementing, how do you tend to work?"],
    41: ['What guides your choices about naming and organization while you build?'],
    42: ["What's your method for chasing a bug all the way to its source?"],
    43: ["What's your way of deciding what and how to test?"],
    44: ["When a colleague's changes land in front of you, how do you work through them?"],
    45: ["What's your approach when it's time to tidy and restructure existing code?"],
    46: ['What drives the choices you make about your setup and tooling?'],
    47: ["What's your rhythm around commits, branches, and source control?"],
    48: ['What changes about your approach in a shared, many-hands codebase?'],
    49: ["What's your practice when it comes to writing things down for others?"],
    50: ["What does your process look like when it's time to ship to production?"],
    51: ["What's your first move when a live incident kicks off?"],
    52: ["What's your procedure when you have to pick one tool or stack over another?"],
    53: ["What's your approach to sizing up and laying out the work ahead?"],
    54: ['When speed and quality pull against each other, how do you decide?'],
    55: ["What's your way of getting up to speed on something new?"],
    56: ['What do you do when the target keeps moving and the ask stays fuzzy?'],
    57: ['What changes in how you operate when the room to maneuver is small?'],
    58: ['At what point does a piece of work cross the line into finished for you?'],
    59: ['What tips you off that an approach is wrong, and how do you back out?'],
    60: ['When a lean solution and a thorough one compete, how do you choose?'],
    61: ["What's your approach when you need a non-specialist to understand a technical idea?"],
    62: ["What keeps you from disappearing down tangents when you're deep in something?"],
    63: ["When you don't have a strong reason to do otherwise, what do you fall back on?"],
    64: ["What's your approach when you're helping a junior engineer grow?"],
}

# {original_idx: facet id} — cluster id for facet-clustered CIs
FACET_OF_CLEANSTRATA = {
    0: 'cs-A1',
    1: 'cs-A2',
    2: 'cs-A3',
    3: 'cs-A4',
    4: 'cs-A8',
    5: 'cs-A9',
    6: 'cs-A10',
    7: 'cs-A11',
    8: 'cs-A13',
    9: 'cs-A14',
    10: 'cs-A15',
    11: 'cs-A16',
    12: 'cs-A17',
    13: 'cs-A18',
    14: 'cs-A19',
    15: 'cs-A20',
    16: 'cs-B1',
    17: 'cs-B2',
    18: 'cs-B3',
    19: 'cs-B4',
    20: 'cs-B5',
    21: 'cs-B6',
    22: 'cs-B7',
    23: 'cs-B8',
    24: 'cs-B9',
    25: 'cs-B10',
    26: 'cs-B11',
    27: 'cs-B12',
    28: 'cs-B13',
    29: 'cs-B14',
    30: 'cs-B15',
    31: 'cs-B16',
    32: 'cs-B17',
    33: 'cs-B18',
    34: 'cs-B19',
    35: 'cs-B20',
    36: 'cs-C1',
    37: 'cs-C2',
    38: 'cs-C3',
    39: 'cs-C4',
    40: 'cs-C5',
    41: 'cs-C6',
    42: 'cs-C7',
    43: 'cs-C8',
    44: 'cs-C9',
    45: 'cs-C11',
    46: 'cs-C12',
    47: 'cs-C13',
    48: 'cs-C14',
    49: 'cs-C15',
    50: 'cs-C16',
    51: 'cs-C17',
    52: 'cs-C18',
    53: 'cs-C19',
    54: 'cs-C20',
    55: 'cs-C21',
    56: 'cs-C22',
    57: 'cs-C23',
    58: 'cs-C24',
    59: 'cs-C25',
    60: 'cs-C26',
    61: 'cs-C27',
    62: 'cs-C28',
    63: 'cs-C29',
    64: 'cs-C30',
}

# {facet id: class} — SP / ID / PROC (locked blind classification)
CLASS_OF_CLEANSTRATA = {
    'cs-A1': 'SP',
    'cs-A2': 'SP',
    'cs-A3': 'SP',
    'cs-A4': 'SP',
    'cs-A8': 'SP',
    'cs-A9': 'SP',
    'cs-A10': 'SP',
    'cs-A11': 'SP',
    'cs-A13': 'SP',
    'cs-A14': 'SP',
    'cs-A15': 'SP',
    'cs-A16': 'SP',
    'cs-A17': 'SP',
    'cs-A18': 'SP',
    'cs-A19': 'SP',
    'cs-A20': 'SP',
    'cs-B1': 'ID',
    'cs-B2': 'ID',
    'cs-B3': 'ID',
    'cs-B4': 'ID',
    'cs-B5': 'ID',
    'cs-B6': 'ID',
    'cs-B7': 'ID',
    'cs-B8': 'ID',
    'cs-B9': 'ID',
    'cs-B10': 'ID',
    'cs-B11': 'ID',
    'cs-B12': 'ID',
    'cs-B13': 'ID',
    'cs-B14': 'ID',
    'cs-B15': 'ID',
    'cs-B16': 'ID',
    'cs-B17': 'ID',
    'cs-B18': 'ID',
    'cs-B19': 'ID',
    'cs-B20': 'ID',
    'cs-C1': 'PROC',
    'cs-C2': 'PROC',
    'cs-C3': 'PROC',
    'cs-C4': 'PROC',
    'cs-C5': 'PROC',
    'cs-C6': 'PROC',
    'cs-C7': 'PROC',
    'cs-C8': 'PROC',
    'cs-C9': 'PROC',
    'cs-C11': 'PROC',
    'cs-C12': 'PROC',
    'cs-C13': 'PROC',
    'cs-C14': 'PROC',
    'cs-C15': 'PROC',
    'cs-C16': 'PROC',
    'cs-C17': 'PROC',
    'cs-C18': 'PROC',
    'cs-C19': 'PROC',
    'cs-C20': 'PROC',
    'cs-C21': 'PROC',
    'cs-C22': 'PROC',
    'cs-C23': 'PROC',
    'cs-C24': 'PROC',
    'cs-C25': 'PROC',
    'cs-C26': 'PROC',
    'cs-C27': 'PROC',
    'cs-C28': 'PROC',
    'cs-C29': 'PROC',
    'cs-C30': 'PROC',
}
