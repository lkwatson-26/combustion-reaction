from drafter import *
from dataclasses import dataclass

# Constants (allowed): molar masses in g/mol
MOLAR_MASS = {"C": 12.011, "H": 1.008, "O": 15.999}
M_O2 = 2 * MOLAR_MASS["O"]
M_CO2 = MOLAR_MASS["C"] + 2 * MOLAR_MASS["O"]
M_H2O = 2 * MOLAR_MASS["H"] + MOLAR_MASS["O"]

# Positions in the coefficient list returned by get_coefficients
FUEL = 0
OXYGEN = 1
CARBON_DIOXIDE = 2
WATER = 3

# Style constants (allowed): one accent color plus light backgrounds
ACCENT_COLOR = "#2e7d32"
RESULT_BACKGROUND = "#eef7ee"
ERROR_COLOR = "#b71c1c"
ERROR_BACKGROUND = "#fdecea"
INFO_BACKGROUND = "#f4f6f8"


@dataclass
class Element:
    name: str
    quantity: int
    molar_mass: float


@dataclass
class Compound:
    name: str
    amount: int
    molar_mass: float
    weight: float
    elements: list[Element]


@dataclass
class State:
    hydrocarbon: Compound       # current compound (set in set_hydrocarbon)
    history: list[Compound]     # every compound entered (appended to)
    oxygen_mode: str            # "excess" or "limited"
    limiting_reactant: str      # result of the last calculation


# ----------------------------------------------------------- style helpers

def page_title(text: str) -> Header:
    """Return a large green page title."""
    return Header(change_color(text, ACCENT_COLOR), 1)


def info_card(*lines: str) -> Div:
    """Return a light gray box that groups instructional text."""
    return Div(*lines,
               style_background_color=INFO_BACKGROUND,
               style_padding="12px",
               style_border="1px solid #cfd8dc")


def result_card(*lines: str) -> Div:
    """Return a green box that makes results stand out."""
    return Div(*lines,
               style_background_color=RESULT_BACKGROUND,
               style_padding="12px",
               style_border="2px solid " + ACCENT_COLOR)


def error_card(message: str) -> Div:
    """Return a red box that shows an error message."""
    return Div(change_color(message, ERROR_COLOR),
               style_background_color=ERROR_BACKGROUND,
               style_padding="12px",
               style_border="2px solid " + ERROR_COLOR)


# ---------------------------------------------------------------- helpers

def total_mass(elements: list[Element]) -> float:
    """Return the molar mass of a compound made of the given elements."""
    total = 0.0
    for element in elements:
        total += element.quantity * element.molar_mass
    return total


def build_formula(elements: list[Element]) -> str:
    """Return a formula like 'C2H6O', skipping elements with 0 atoms."""
    formula = ""
    for element in elements:
        if element.quantity == 1:
            formula += element.name
        elif element.quantity > 1:
            formula += element.name + str(element.quantity)
    return formula


def make_compound(carbon: int, hydrogen: int, oxygen: int) -> Compound:
    """Build a Compound from atom counts of C, H, and O."""
    elements = [
        Element("C", carbon, MOLAR_MASS["C"]),
        Element("H", hydrogen, MOLAR_MASS["H"]),
        Element("O", oxygen, MOLAR_MASS["O"]),
    ]
    mass = total_mass(elements)
    return Compound(build_formula(elements), 1, mass, mass, elements)


def valid_counts(carbon: str, hydrogen: str, oxygen: str) -> bool:
    """Check the three atom counts are whole numbers with C and H above 0."""
    if not (carbon.isdecimal() and hydrogen.isdecimal() and oxygen.isdecimal()):
        return False
    return int(carbon) > 0 and int(hydrogen) > 0


def get_quantity(compound: Compound, symbol: str) -> int:
    """Return how many atoms of an element the compound has."""
    for element in compound.elements:
        if element.name == symbol:
            return element.quantity
    return 0


def get_coefficients(fuel: Compound) -> list[int]:
    """Return [fuel, O2, CO2, H2O] coefficients, or [] if it can't combust."""
    carbon = get_quantity(fuel, "C")
    hydrogen = get_quantity(fuel, "H")
    oxygen = get_quantity(fuel, "O")

    # O2 needed per fuel molecule is oxygen_quarters / 4
    oxygen_quarters = 4 * carbon + hydrogen - 2 * oxygen
    if oxygen_quarters <= 0:
        return []

    # Smallest multiplier that makes every coefficient a whole number
    multiplier = 1
    while (multiplier * oxygen_quarters) % 4 != 0 or (multiplier * hydrogen) % 2 != 0:
        multiplier += 1

    return [multiplier,
            multiplier * oxygen_quarters // 4,
            multiplier * carbon,
            multiplier * hydrogen // 2]


def term(coefficient: int, formula: str) -> str:
    """Format one part of the equation, leaving off a coefficient of 1."""
    if coefficient == 1:
        return formula
    return str(coefficient) + " " + formula


def format_equation(fuel: Compound, coefficients: list[int]) -> str:
    """Return the balanced equation as text."""
    return (term(coefficients[FUEL], fuel.name) + " + "
            + term(coefficients[OXYGEN], "O2") + " → "
            + term(coefficients[CARBON_DIOXIDE], "CO2") + " + "
            + term(coefficients[WATER], "H2O"))


def parse_positive(text: str) -> float:
    """Turn text into a number above 0, or return -1 if it isn't valid."""
    # ADVANCED TECHNIQUE: try/except catches the ValueError that float()
    # raises for text like "abc", so the site shows a message instead of
    # crashing.
    try:
        value = float(text)
    except ValueError:
        return -1.0
    # float() also accepts the words "nan" and "inf", so require a real,
    # finite number above 0 (comparisons with nan are always False).
    if not (0 < value < float("inf")):
        return -1.0
    return value


def reaction_runs(grams: float, molar_mass: float, coefficient: int) -> float:
    """Return how many times the balanced reaction could run from this reactant."""
    return (grams / molar_mass) / coefficient


def product_weights(coefficients: list[int], runs: float) -> list[float]:
    """Return [grams of CO2, grams of H2O] made when the reaction runs `runs` times."""
    return [runs * coefficients[CARBON_DIOXIDE] * M_CO2,
            runs * coefficients[WATER] * M_H2O]


def history_lines(history: list[Compound]) -> list[str]:
    """Return one text line per compound in the history."""
    lines = []
    for compound in history:
        lines.append(compound.name + " (" + str(round(compound.molar_mass, 3)) + " g/mol)")
    return lines


def results_page(state: State, limiting: str, runs: float) -> Page:
    """Record the limiting reactant and build the product-weights page."""
    state.limiting_reactant = limiting
    weights = product_weights(get_coefficients(state.hydrocarbon), runs)
    return Page(state, [
        page_title("Results"),
        result_card(
            "Limiting reactant: " + state.limiting_reactant,
            "CO2 produced: " + str(round(weights[0], 3)) + " g",
            "H2O produced: " + str(round(weights[1], 3)) + " g",
        ),
        Button("Start over", index),
    ])


# ----------------------------------------------------------------- routes

@route
def index(state: State) -> Page:
    """Show the page where the user enters atom counts of C, H, and O."""
    return Page(state, [
        page_title("Hydrocarbon Reaction Balancer"),
        info_card("Enter the number of atoms of each element in your compound."),
        "Carbon (C):", TextBox("carbon", "1"),
        "Hydrogen (H):", TextBox("hydrogen", "4"),
        "Oxygen (O):", TextBox("oxygen", "0"),
        Button("Submit", set_hydrocarbon),
        Button("View history", show_history),
    ])


@route
def set_hydrocarbon(state: State, carbon: str, hydrogen: str, oxygen: str) -> Page:
    """Validate the inputs, store the new compound, and show its molar mass."""
    if not valid_counts(carbon, hydrogen, oxygen):
        return Page(state, [
            page_title("Invalid input"),
            error_card("Enter whole numbers only, with at least 1 carbon and 1 hydrogen."),
            Button("Try again", index),
        ])

    state.hydrocarbon = make_compound(int(carbon), int(hydrogen), int(oxygen))
    state.history.append(state.hydrocarbon)

    return Page(state, [
        page_title("Your Compound"),
        result_card(
            "Formula: " + state.hydrocarbon.name,
            "Molar mass: " + str(round(state.hydrocarbon.molar_mass, 3)) + " g/mol",
        ),
        Button("Balance combustion reaction", show_reaction),
        Button("Start over", index),
    ])


@route
def show_reaction(state: State) -> Page:
    """Show the balanced combustion equation for the current compound."""
    coefficients = get_coefficients(state.hydrocarbon)
    if len(coefficients) == 0:
        return Page(state, [
            page_title("Cannot combust"),
            error_card("This compound already has too much oxygen to combust with O2."),
            Button("Try again", index),
        ])

    return Page(state, [
        page_title("Balanced Reaction"),
        result_card(monospace(format_equation(state.hydrocarbon, coefficients))),
        Button("Calculate product weights", choose_oxygen),
        Button("Start over", index),
    ])


@route
def choose_oxygen(state: State) -> Page:
    """Ask whether the reaction has excess or limited oxygen."""
    return Page(state, [
        page_title("Oxygen Supply"),
        info_card("Does the reaction have excess or limited oxygen?"),
        Button("Excess oxygen", excess_page),
        Button("Limited oxygen", limited_page),
    ])


@route
def excess_page(state: State) -> Page:
    """Record excess oxygen and ask for the weight of the hydrocarbon."""
    state.oxygen_mode = "excess"
    return Page(state, [
        page_title("Excess Oxygen"),
        info_card("Oxygen is in excess, so " + state.hydrocarbon.name + " is limiting."),
        "Weight of " + state.hydrocarbon.name + " (grams):",
        TextBox("fuel_weight", "10"),
        Button("Calculate", calculate_excess),
    ])


@route
def limited_page(state: State) -> Page:
    """Record limited oxygen and ask for both reactant weights."""
    state.oxygen_mode = "limited"
    return Page(state, [
        page_title("Limited Oxygen"),
        info_card("Enter the weight of each reactant."),
        "Weight of " + state.hydrocarbon.name + " (grams):",
        TextBox("fuel_weight", "10"),
        "Weight of O2 (grams):",
        TextBox("oxygen_weight", "10"),
        Button("Calculate", calculate_limited),
    ])


@route
def calculate_excess(state: State, fuel_weight: str) -> Page:
    """Find product weights when the hydrocarbon is the limiting reactant."""
    grams_fuel = parse_positive(fuel_weight)
    if grams_fuel < 0:
        return Page(state, [
            page_title("Invalid input"),
            error_card("Please enter a number greater than 0."),
            Button("Try again", excess_page),
        ])

    fuel = state.hydrocarbon
    runs = reaction_runs(grams_fuel, fuel.molar_mass, get_coefficients(fuel)[FUEL])
    return results_page(state, fuel.name, runs)


@route
def calculate_limited(state: State, fuel_weight: str, oxygen_weight: str) -> Page:
    """Find the limiting reactant, then the product weights."""
    grams_fuel = parse_positive(fuel_weight)
    grams_oxygen = parse_positive(oxygen_weight)
    if grams_fuel < 0 or grams_oxygen < 0:
        return Page(state, [
            page_title("Invalid input"),
            error_card("Please enter numbers greater than 0 for both weights."),
            Button("Try again", limited_page),
        ])

    fuel = state.hydrocarbon
    coefficients = get_coefficients(fuel)
    runs_from_fuel = reaction_runs(grams_fuel, fuel.molar_mass, coefficients[FUEL])
    runs_from_oxygen = reaction_runs(grams_oxygen, M_O2, coefficients[OXYGEN])

    # The reactant that allows fewer runs is used up first
    if runs_from_fuel <= runs_from_oxygen:
        return results_page(state, fuel.name, runs_from_fuel)
    return results_page(state, "O2", runs_from_oxygen)


@route
def show_history(state: State) -> Page:
    """List every compound the user has entered this session."""
    if len(state.history) == 0:
        return Page(state, [
            page_title("History"),
            info_card("No compounds entered yet."),
            Button("Back", index),
        ])

    return Page(state, [
        page_title("History"),
        result_card(*history_lines(state.history)),
        Button("Back", index),
    ])


# ------------------------------------------------------------- unit tests

def new_state() -> State:
    """Return a fresh State (used by the tests and by start_server)."""
    return State(Compound("", 1, 0.0, 0.0, []), [], "", "")


def state_with(carbon: int, hydrogen: int, oxygen: int) -> State:
    """Return a State whose hydrocarbon has the given atom counts."""
    state = new_state()
    state.hydrocarbon = make_compound(carbon, hydrogen, oxygen)
    return state


def count_type(content: list, kind: type) -> int:
    """Test helper: count the items in a Page's content that are of a type."""
    count = 0
    for item in content:
        if isinstance(item, kind):
            count += 1
    return count


def is_balanced(fuel: Compound) -> bool:
    """Test helper: check C, H, and O atoms match on both sides of the equation."""
    coefficients = get_coefficients(fuel)
    if len(coefficients) == 0:
        return False
    fuel_count = coefficients[FUEL]
    carbon_ok = fuel_count * get_quantity(fuel, "C") == coefficients[CARBON_DIOXIDE]
    hydrogen_ok = fuel_count * get_quantity(fuel, "H") == 2 * coefficients[WATER]
    oxygen_left = fuel_count * get_quantity(fuel, "O") + 2 * coefficients[OXYGEN]
    oxygen_right = 2 * coefficients[CARBON_DIOXIDE] + coefficients[WATER]
    return carbon_ok and hydrogen_ok and oxygen_left == oxygen_right


def all_balanced() -> bool:
    """Test helper: check many different fuels all balance."""
    fuels = [(1, 4, 0), (2, 6, 0), (2, 4, 0), (2, 2, 0), (3, 8, 0), (4, 10, 0),
             (8, 18, 0), (1, 4, 1), (2, 6, 1), (1, 4, 3), (6, 12, 6)]
    for carbon, hydrogen, oxygen in fuels:
        if not is_balanced(make_compound(carbon, hydrogen, oxygen)):
            return False
    return True


# --- new_state, state_with, and the test helpers themselves
assert_equal(new_state().history, [])
assert_equal(new_state().oxygen_mode, "")
assert_equal(new_state().limiting_reactant, "")
assert_equal(new_state().hydrocarbon.name, "")
first_state = new_state()
first_state.history.append(make_compound(1, 4, 0))
assert_equal(len(new_state().history), 0)  # states must not share one list
assert_equal(state_with(2, 6, 0).hydrocarbon.name, "C2H6")
assert_equal(count_type([1, "a", 2], int), 2)
assert_equal(count_type([], int), 0)
assert_equal(is_balanced(make_compound(1, 2, 5)), False)  # can't combust
assert_equal(all_balanced(), True)

# --- total_mass
assert_equal(total_mass([]), 0.0)
assert_equal(round(total_mass(make_compound(1, 4, 0).elements), 3), 16.043)
assert_equal(round(total_mass(make_compound(2, 6, 0).elements), 3), 30.07)
assert_equal(round(total_mass(make_compound(2, 6, 1).elements), 3), 46.069)
assert_equal(round(total_mass([Element("H", 2, 1.008)]), 3), 2.016)

# --- build_formula
assert_equal(build_formula([]), "")
assert_equal(build_formula(make_compound(1, 4, 0).elements), "CH4")
assert_equal(build_formula(make_compound(2, 6, 1).elements), "C2H6O")
assert_equal(build_formula(make_compound(1, 1, 1).elements), "CHO")
assert_equal(build_formula(make_compound(10, 22, 0).elements), "C10H22")
assert_equal(build_formula(make_compound(6, 12, 6).elements), "C6H12O6")

# --- make_compound
methane = make_compound(1, 4, 0)
assert_equal(methane.name, "CH4")
assert_equal(methane.amount, 1)
assert_equal(len(methane.elements), 3)
assert_equal(methane.elements[0].name, "C")
assert_equal(methane.elements[1].quantity, 4)
assert_equal(methane.elements[2].quantity, 0)
assert_equal(round(methane.molar_mass, 3), 16.043)
assert_equal(methane.weight, methane.molar_mass)
assert_equal(make_compound(3, 8, 0).elements[0].molar_mass, 12.011)

# --- valid_counts
assert_equal(valid_counts("1", "4", "0"), True)
assert_equal(valid_counts("10", "22", "3"), True)
assert_equal(valid_counts("0", "4", "0"), False)    # needs carbon
assert_equal(valid_counts("1", "0", "0"), False)    # needs hydrogen
assert_equal(valid_counts("a", "4", "0"), False)
assert_equal(valid_counts("1", "4", "x"), False)
assert_equal(valid_counts("", "4", "0"), False)
assert_equal(valid_counts("1", "", "0"), False)
assert_equal(valid_counts("1", "4", ""), False)
assert_equal(valid_counts("-1", "4", "0"), False)
assert_equal(valid_counts("1.5", "4", "0"), False)

# --- get_quantity
assert_equal(get_quantity(make_compound(2, 6, 0), "C"), 2)
assert_equal(get_quantity(make_compound(2, 6, 0), "H"), 6)
assert_equal(get_quantity(make_compound(2, 6, 0), "O"), 0)
assert_equal(get_quantity(make_compound(2, 6, 1), "O"), 1)
assert_equal(get_quantity(make_compound(2, 6, 1), "N"), 0)   # not in compound
assert_equal(get_quantity(new_state().hydrocarbon, "C"), 0)  # empty compound

# --- get_coefficients (known answers, then a balance check)
assert_equal(get_coefficients(make_compound(1, 4, 0)), [1, 2, 1, 2])
assert_equal(get_coefficients(make_compound(2, 6, 0)), [2, 7, 4, 6])
assert_equal(get_coefficients(make_compound(2, 4, 0)), [1, 3, 2, 2])
assert_equal(get_coefficients(make_compound(2, 2, 0)), [2, 5, 4, 2])
assert_equal(get_coefficients(make_compound(3, 8, 0)), [1, 5, 3, 4])
assert_equal(get_coefficients(make_compound(8, 18, 0)), [2, 25, 16, 18])
assert_equal(get_coefficients(make_compound(1, 4, 1)), [2, 3, 2, 4])
assert_equal(get_coefficients(make_compound(2, 6, 1)), [1, 3, 2, 3])
assert_equal(get_coefficients(make_compound(6, 12, 6)), [1, 6, 6, 6])
assert_equal(get_coefficients(make_compound(1, 2, 5)), [])  # too much oxygen
assert_equal(get_coefficients(make_compound(1, 4, 4)), [])  # exactly zero O2
assert_equal(get_coefficients(new_state().hydrocarbon), [])  # empty compound

# --- term
assert_equal(term(1, "O2"), "O2")
assert_equal(term(3, "O2"), "3 O2")
assert_equal(term(12, "H2O"), "12 H2O")

# --- format_equation
assert_equal(format_equation(make_compound(1, 4, 0), [1, 2, 1, 2]),
             "CH4 + 2 O2 → CO2 + 2 H2O")
assert_equal(format_equation(make_compound(2, 6, 0), [2, 7, 4, 6]),
             "2 C2H6 + 7 O2 → 4 CO2 + 6 H2O")
assert_equal(format_equation(make_compound(2, 6, 1), [1, 3, 2, 3]),
             "C2H6O + 3 O2 → 2 CO2 + 3 H2O")

# --- parse_positive
assert_equal(parse_positive("2.5"), 2.5)
assert_equal(parse_positive("10"), 10.0)
assert_equal(parse_positive("0.001"), 0.001)
assert_equal(parse_positive("abc"), -1.0)
assert_equal(parse_positive(""), -1.0)
assert_equal(parse_positive("   "), -1.0)
assert_equal(parse_positive("0"), -1.0)
assert_equal(parse_positive("-3"), -1.0)
assert_equal(parse_positive("-0.5"), -1.0)
assert_equal(parse_positive("1,5"), -1.0)
assert_equal(parse_positive("nan"), -1.0)
assert_equal(parse_positive("inf"), -1.0)

# --- reaction_runs
assert_equal(reaction_runs(32.0, 16.0, 2), 1.0)
assert_equal(reaction_runs(16.043, 16.043, 1), 1.0)
assert_equal(reaction_runs(0.0, 16.043, 1), 0.0)
assert_equal(reaction_runs(64.0, 16.0, 2), 2.0)       # bigger coefficient, fewer runs
assert_equal(reaction_runs(64.0, 16.0, 4), 1.0)

# --- product_weights
assert_equal([round(w, 3) for w in product_weights([1, 2, 1, 2], 1.0)], [44.009, 36.03])
assert_equal([round(w, 3) for w in product_weights([1, 2, 1, 2], 2.0)], [88.018, 72.06])
assert_equal(product_weights([1, 2, 1, 2], 0.0), [0.0, 0.0])
assert_equal([round(w, 3) for w in product_weights([2, 7, 4, 6], 0.5)], [88.018, 54.045])

# --- history_lines
assert_equal(history_lines([]), [])
assert_equal(history_lines([make_compound(1, 4, 0)]), ["CH4 (16.043 g/mol)"])
assert_equal(history_lines([make_compound(1, 4, 0), make_compound(2, 6, 0)]),
             ["CH4 (16.043 g/mol)", "C2H6 (30.07 g/mol)"])

# --- style helpers: they only build Drafter components, whose exact contents
# can't be compared reliably, so each test checks that the right type is made.
assert_equal(isinstance(page_title("Hi"), Header), True)
assert_equal(isinstance(page_title(""), Header), True)
assert_equal(isinstance(info_card("Hi"), Div), True)
assert_equal(isinstance(result_card("Hi", "There"), Div), True)
assert_equal(isinstance(result_card(), Div), True)
assert_equal(isinstance(error_card("Oops"), Div), True)

# --- index: a Page with exactly 3 text boxes (C, H, O) and 2 buttons
home_page = index(new_state())
assert_equal(isinstance(home_page, Page), True)
assert_equal(count_type(home_page.content, TextBox), 3)
assert_equal(count_type(home_page.content, Button), 2)

# --- set_hydrocarbon
good_page = set_hydrocarbon(new_state(), "1", "4", "0")
assert_equal(good_page.state.hydrocarbon.name, "CH4")
assert_equal(len(good_page.state.history), 1)
assert_equal(good_page.state.history[0] is good_page.state.hydrocarbon, True)
assert_equal(count_type(good_page.content, Button), 2)
assert_equal(set_hydrocarbon(new_state(), "2", "6", "1").state.hydrocarbon.name, "C2H6O")
assert_equal(set_hydrocarbon(new_state(), "10", "22", "0").state.hydrocarbon.name, "C10H22")

# invalid input: nothing is stored and the old compound is kept
for bad_counts in [("x", "4", "0"), ("0", "4", "0"), ("1", "0", "0"), ("", "", ""),
                   ("-1", "4", "0"), ("1.5", "4", "0"), ("1", "4", "y")]:
    bad_page = set_hydrocarbon(new_state(), bad_counts[0], bad_counts[1], bad_counts[2])
    assert_equal(len(bad_page.state.history), 0)
    assert_equal(bad_page.state.hydrocarbon.name, "")
    assert_equal(count_type(bad_page.content, Button), 1)

kept_state = state_with(1, 4, 0)
assert_equal(set_hydrocarbon(kept_state, "x", "4", "0").state.hydrocarbon.name, "CH4")

# two submissions: history grows in order and hydrocarbon is the newest
two_state = set_hydrocarbon(new_state(), "1", "4", "0").state
two_state = set_hydrocarbon(two_state, "2", "6", "0").state
assert_equal(len(two_state.history), 2)
assert_equal(two_state.history[0].name, "CH4")
assert_equal(two_state.history[1].name, "C2H6")
assert_equal(two_state.hydrocarbon.name, "C2H6")

# --- show_reaction: 4 items when it works, 3 (with an error) when it can't
assert_equal(len(show_reaction(state_with(1, 4, 0)).content), 4)
assert_equal(len(show_reaction(state_with(6, 12, 6)).content), 4)
assert_equal(len(show_reaction(state_with(1, 2, 5)).content), 3)
assert_equal(len(show_reaction(state_with(1, 4, 4)).content), 3)
assert_equal(show_reaction(state_with(1, 4, 0)).state.hydrocarbon.name, "CH4")

# --- choose_oxygen
oxygen_choice_page = choose_oxygen(new_state())
assert_equal(isinstance(oxygen_choice_page, Page), True)
assert_equal(count_type(oxygen_choice_page.content, Button), 2)
assert_equal(count_type(oxygen_choice_page.content, TextBox), 0)

# --- excess_page and limited_page
excess_result = excess_page(state_with(1, 4, 0))
assert_equal(excess_result.state.oxygen_mode, "excess")
assert_equal(count_type(excess_result.content, TextBox), 1)
limited_result = limited_page(state_with(1, 4, 0))
assert_equal(limited_result.state.oxygen_mode, "limited")
assert_equal(count_type(limited_result.content, TextBox), 2)
switched_state = excess_page(state_with(1, 4, 0)).state
assert_equal(limited_page(switched_state).state.oxygen_mode, "limited")
assert_equal(excess_page(switched_state).state.oxygen_mode, "excess")

# --- results_page
assert_equal(results_page(state_with(1, 4, 0), "CH4", 1.0).state.limiting_reactant, "CH4")
assert_equal(results_page(state_with(1, 4, 0), "O2", 0.5).state.limiting_reactant, "O2")
assert_equal(isinstance(results_page(state_with(2, 6, 0), "C2H6", 2.0), Page), True)

# --- calculate_excess
assert_equal(calculate_excess(state_with(1, 4, 0), "16.043").state.limiting_reactant, "CH4")
assert_equal(calculate_excess(state_with(2, 6, 0), "1").state.limiting_reactant, "C2H6")
assert_equal(calculate_excess(state_with(2, 6, 1), "5.5").state.limiting_reactant, "C2H6O")
for bad_weight in ["abc", "", "0", "-5", "nan", "inf"]:
    bad_result = calculate_excess(state_with(1, 4, 0), bad_weight)
    assert_equal(bad_result.state.limiting_reactant, "")
    assert_equal(count_type(bad_result.content, Button), 1)

# --- calculate_limited
assert_equal(calculate_limited(state_with(1, 4, 0), "16.043", "32").state.limiting_reactant, "O2")
assert_equal(calculate_limited(state_with(1, 4, 0), "1", "100").state.limiting_reactant, "CH4")
assert_equal(calculate_limited(state_with(2, 6, 0), "30.07", "100").state.limiting_reactant, "O2")
assert_equal(calculate_limited(state_with(2, 6, 0), "1", "100").state.limiting_reactant, "C2H6")
assert_equal(calculate_limited(state_with(2, 6, 1), "1", "100").state.limiting_reactant, "C2H6O")
for bad_pair in [("abc", "10"), ("10", "abc"), ("0", "10"), ("10", "0"),
                 ("-1", "10"), ("10", "-1"), ("", ""), ("nan", "10")]:
    bad_result = calculate_limited(state_with(1, 4, 0), bad_pair[0], bad_pair[1])
    assert_equal(bad_result.state.limiting_reactant, "")
    assert_equal(count_type(bad_result.content, Button), 1)

# --- show_history
assert_equal(isinstance(show_history(new_state()), Page), True)
assert_equal(len(show_history(new_state()).state.history), 0)
history_state = state_with(1, 4, 0)
history_state.history.append(history_state.hydrocarbon)
history_state.history.append(make_compound(2, 6, 0))
history_page = show_history(history_state)
assert_equal(isinstance(history_page, Page), True)
assert_equal(len(history_page.state.history), 2)   # viewing doesn't change it
assert_equal(count_type(history_page.content, Button), 1)

# --- full workflow: enter a compound, choose oxygen, calculate
workflow_state = set_hydrocarbon(new_state(), "1", "4", "0").state
workflow_state = excess_page(workflow_state).state
workflow_state = calculate_excess(workflow_state, "16.043").state
assert_equal(workflow_state.oxygen_mode, "excess")
assert_equal(workflow_state.limiting_reactant, "CH4")
assert_equal(len(workflow_state.history), 1)

limited_workflow = set_hydrocarbon(new_state(), "2", "6", "0").state
limited_workflow = limited_page(limited_workflow).state
limited_workflow = calculate_limited(limited_workflow, "30.07", "100").state
assert_equal(limited_workflow.oxygen_mode, "limited")
assert_equal(limited_workflow.limiting_reactant, "O2")

# ------------------------------------------------------- site-wide styling
# Configuration calls: these run once at startup, so they are not variables.
set_website_title("Combustion Balancer")
set_website_style("skeleton")   # try other built-in style names to compare
set_website_framed(False)       # hides the Drafter frame around the site
hide_debug_information()        # removes the debug panel at the bottom

start_server(new_state())
