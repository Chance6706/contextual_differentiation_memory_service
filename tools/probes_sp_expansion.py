"""SP-open EXPANSION bank (FILLER_PREREG powered re-run) — blind-authored + blind-classified.

25 FORMAT-OPEN self-presentation facets (7 reused clean-strata + 18 new, kappa=0.932) + 6 PROC controls. Powers the length-matched
filler control (and the multifact availability question) past the 7-open-facet ceiling. REPRO_FACETS
= the reused 7 (G2 anchor to multifact open-SP T1=0.182). LOCKED — guarded by tests/test_filler.py.
"""
from __future__ import annotations

PROBES_SP_EXP = [
    "What would you say are your strongest capabilities as an engineer when you're at your best?",  # cs-A1 | SP
    'What weaknesses or blind spots do you keep an eye on in yourself as an engineer?',  # cs-A2 | SP
    'What do colleagues tend to come to you for when they need something specific?',  # cs-A8 | SP
    'How do you think the people you work with would describe you as an engineer?',  # cs-A9 | SP
    'In what ways do people most often misread or misjudge you at work?',  # cs-A10 | SP
    "What do you think sets you apart from the other engineers you've worked alongside?",  # cs-A11 | SP
    'What do you imagine a former manager would say if asked to give you a reference?',  # cs-A20 | SP
    "What would you say are your signature strengths as an engineer - the handful of things you're genuinely strongest at?",  # sp-N1 | SP
    'Across your team, what different kinds of tasks do colleagues tend to seek you out for?',  # sp-N2 | SP
    "Looking back at the feedback you've gotten over the years, what themes keep recurring?",  # sp-N3 | SP
    'If you were assembling a professional portfolio, which highlights of your work would you feature?',  # sp-N4 | SP
    "On the teams you've been part of, which distinct roles or hats do you tend to wear?",  # sp-N5 | SP
    "Which areas of engineering would you say you've developed genuinely deep technical expertise in?",  # sp-N6 | SP
    'Over your career so far, which standout contributions would you point to as most significant?',  # sp-N7 | SP
    'Heading into a self-review, what would you most want to emphasize about yourself?',  # sp-N9 | SP
    'What kinds of problems have you become the go-to person for around the office?',  # sp-N10 | SP
    "What do you bring to a team that others around you typically don't?",  # sp-N11 | SP
    'Which wins or accomplishments have you become known for among the people you work with?',  # sp-N12 | SP
    "What are the different facets of the reputation you've built as an engineer?",  # sp-N13 | SP
    "Which skills would you claim with real confidence if someone asked what you're good at?",  # sp-N14 | SP
    'When you join a new team, which strengths do you tend to lead with?',  # sp-N16 | SP
    'What compliments about your work do you find yourself hearing again and again?',  # sp-N17 | SP
    'Which capabilities would you most want featured on your professional profile for others to see?',  # sp-N18 | SP
    'What are the things the people around you most rely on you for?',  # sp-N19 | SP
    'What would you name as the defining professional accomplishments of your engineering career?',  # sp-N20 | SP
    'How do you go about pinning down what a piece of work actually requires?',  # cs-C1 | PROC
    'How do you get from an empty file to something finished?',  # cs-C3 | PROC
    "When something's broken, how do you go about tracking down the cause?",  # cs-C7 | PROC
    'How do you approach testing the things you build?',  # cs-C8 | PROC
    'How do you handle documentation around the work you do?',  # cs-C15 | PROC
    'How do you balance moving fast against getting things right?',  # cs-C20 | PROC
]

REPHRASINGS_SP_EXP = {
    0: ['Where do your greatest strengths lie in the technical work you do day to day?'],
    1: ['Which of your own shortcomings do you find yourself watching out for in the work?'],
    2: ["When teammates seek you out, what is it they're usually hoping you can provide?"],
    3: ["If your teammates were asked what you're like to work with, what words would surface?"],
    4: ['Where do colleagues tend to get the wrong impression of you as an engineer?'],
    5: ['Compared with your peers, what makes you noticeably different in how you show up?'],
    6: ['If a past boss were vouching for you, what do you think would come out of their mouth?'],
    7: ['When you think about where you consistently excel in your work, which core strengths come to mind?'],
    8: ['Which sorts of work do people around you come knocking about when they need a hand?'],
    9: ['Which patterns show up again and again in how managers and peers assess your work?'],
    10: ['What accomplishments would earn a place in a showcase of your best engineering work?'],
    11: ['What different parts do you naturally fall into when a group is getting work done?'],
    12: ['Where does your technical knowledge run deepest - what subjects can you go far into?'],
    13: ["What are the marks you feel you've left across the roles you've held?"],
    14: ['If you were writing up your own performance, which strengths would you choose to spotlight?'],
    15: ['Which types of challenges land on your desk because others trust you to crack them?'],
    16: ['Which distinctive contributions set you apart from the rest of the engineers you work alongside?'],
    17: ['When your reputation precedes you, what successes are usually attached to your name?'],
    18: ['In how many ways are you known professionally - which sides of your reputation stand out?'],
    19: ['Where do you feel fully assured of your abilities - what can you vouch for outright?'],
    20: ['Stepping into an unfamiliar group, what capabilities do you put forward first about yourself?'],
    21: ['Which kind words keep coming back your way when people talk about what you deliver?'],
    22: ['If a public profile summed you up, what abilities would you insist it highlight?'],
    23: ["Which responsibilities do colleagues consistently place in your hands, confident you'll come through?"],
    24: ['Which achievements, more than any others, have come to define you as an engineer?'],
    25: ["When a new task lands, what's your process for scoping out what's really being asked?"],
    26: ['What does your path look like from a blank page to done?'],
    27: ["What's your method for chasing a bug all the way to its source?"],
    28: ["What's your way of deciding what and how to test?"],
    29: ["What's your practice when it comes to writing things down for others?"],
    30: ['When speed and quality pull against each other, how do you decide?'],
}

FACET_OF_SP_EXP = {
    0: 'cs-A1',
    1: 'cs-A2',
    2: 'cs-A8',
    3: 'cs-A9',
    4: 'cs-A10',
    5: 'cs-A11',
    6: 'cs-A20',
    7: 'sp-N1',
    8: 'sp-N2',
    9: 'sp-N3',
    10: 'sp-N4',
    11: 'sp-N5',
    12: 'sp-N6',
    13: 'sp-N7',
    14: 'sp-N9',
    15: 'sp-N10',
    16: 'sp-N11',
    17: 'sp-N12',
    18: 'sp-N13',
    19: 'sp-N14',
    20: 'sp-N16',
    21: 'sp-N17',
    22: 'sp-N18',
    23: 'sp-N19',
    24: 'sp-N20',
    25: 'cs-C1',
    26: 'cs-C3',
    27: 'cs-C7',
    28: 'cs-C8',
    29: 'cs-C15',
    30: 'cs-C20',
}

CLASS_OF_SP_EXP = {
    'cs-A1': 'SP',
    'cs-A2': 'SP',
    'cs-A8': 'SP',
    'cs-A9': 'SP',
    'cs-A10': 'SP',
    'cs-A11': 'SP',
    'cs-A20': 'SP',
    'sp-N1': 'SP',
    'sp-N2': 'SP',
    'sp-N3': 'SP',
    'sp-N4': 'SP',
    'sp-N5': 'SP',
    'sp-N6': 'SP',
    'sp-N7': 'SP',
    'sp-N9': 'SP',
    'sp-N10': 'SP',
    'sp-N11': 'SP',
    'sp-N12': 'SP',
    'sp-N13': 'SP',
    'sp-N14': 'SP',
    'sp-N16': 'SP',
    'sp-N17': 'SP',
    'sp-N18': 'SP',
    'sp-N19': 'SP',
    'sp-N20': 'SP',
    'cs-C1': 'PROC',
    'cs-C3': 'PROC',
    'cs-C7': 'PROC',
    'cs-C8': 'PROC',
    'cs-C15': 'PROC',
    'cs-C20': 'PROC',
}

FORMAT_OPEN = frozenset(["cs-A1", "cs-A10", "cs-A11", "cs-A2", "cs-A20", "cs-A8", "cs-A9", "sp-N1", "sp-N10", "sp-N11", "sp-N12", "sp-N13", "sp-N14", "sp-N16", "sp-N17", "sp-N18", "sp-N19", "sp-N2", "sp-N20", "sp-N3", "sp-N4", "sp-N5", "sp-N6", "sp-N7", "sp-N9"])
REPRO_FACETS = frozenset(["cs-A1", "cs-A10", "cs-A11", "cs-A2", "cs-A20", "cs-A8", "cs-A9"])

# bank-object interface for multifact_analyze.collect(bank=...)
PROBES = PROBES_SP_EXP
REPHRASINGS = REPHRASINGS_SP_EXP
FACET_OF = FACET_OF_SP_EXP
CLASS_OF = CLASS_OF_SP_EXP
EXPECT_BEM = 62
