> **You**

>
> I am creating a beginner blockpy drafter website that allows the user to input the quantity of each element in a hydrocarbon and the website outputs a balanced reaction from the input. I am using data classes: Element(containing: name, qunatity, and molar mass) and Compound (containing: name, amount, molar\_mass, weight, and list\[elements\]. My first priority is making an initial page that presents the user with a text box that allows them to enter the quantity of C,O, and H for their hydrocarbon, and once inputted, is then assigned to that hydrocarbon instance. How would I go about doing this?

Here's a minimal Drafter setup that does this. The key idea is that the page's `TextBox` names become the parameter names of the function the `Button` calls, and everything arrives as a string, so you validate and convert before storing it in your dataclasses.

```
from drafter import *
from dataclasses import dataclass

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
    hydrocarbon: Compound

# Molar masses in g/mol
MOLAR_MASS = {"C": 12.011, "H": 1.008, "O": 15.999}

@route
def index(state: State) -> Page:
    return Page(state, [
        "Hydrocarbon Reaction Balancer",
        "Enter the number of atoms of each element in your compound:",
        "Carbon (C):",   TextBox("carbon", "1"),
        "Hydrogen (H):", TextBox("hydrogen", "4"),
        "Oxygen (O):",   TextBox("oxygen", "0"),
        Button("Submit", set_hydrocarbon),
    ])

@route
def set_hydrocarbon(state: State, carbon: str, hydrogen: str, oxygen: str) -> Page:
    # TextBox values come in as strings, so validate first
    if not (carbon.isdigit() and hydrogen.isdigit() and oxygen.isdigit()):
        return Page(state, [
            "Please enter whole numbers only (0 or greater).",
            Button("Try again", index),
        ])

    c, h, o = int(carbon), int(hydrogen), int(oxygen)

    if c == 0 or h == 0:
        return Page(state, [
            "A hydrocarbon needs at least one carbon and one hydrogen.",
            Button("Try again", index),
        ])

    elements = [
        Element("C", c, MOLAR_MASS["C"]),
        Element("H", h, MOLAR_MASS["H"]),
        Element("O", o, MOLAR_MASS["O"]),
    ]

    # Build a formula name like "C2H6O", skipping elements with 0 atoms
    name = ""
    for e in elements:
        if e.quantity == 1:
            name += e.name
        elif e.quantity > 1:
            name += e.name + str(e.quantity)

    total_mass = 0.0
    for e in elements:
        total_mass += e.quantity * e.molar_mass

    # Assign to the hydrocarbon instance held in state
    state.hydrocarbon = Compound(name, 1, total_mass, total_mass, elements)

    return Page(state, [
        "Your compound: " + state.hydrocarbon.name,
        "Molar mass: " + str(round(state.hydrocarbon.molar_mass, 3)) + " g/mol",
        Button("Start over", index),
    ])

start_server(State(Compound("", 1, 0.0, 0.0, [])))
```

**How it works**

- **State** holds one `Compound`. You give it an empty placeholder at `start_server(...)`, then replace it once the user submits.
- **`index`** shows the three text boxes. The first argument to `TextBox` is its name, and the second is the default text.
- **`set_hydrocarbon`** has parameters named `carbon`, `hydrogen`, and `oxygen`. Drafter matches them to the text box names automatically, so the names must match exactly.
- **Validation** uses `.isdigit()` to reject blanks, letters, and negatives before calling `int()`, which would otherwise crash.
- **Assignment** builds the `Element` list and the `Compound` and stores them in `state.hydrocarbon`, so any later page can read it.

**Notes**

- Technically a pure hydrocarbon has no oxygen. Since you're asking for O, I allowed it (things like ethanol), but you may want to keep it at 0 for your target reactions.
- I set `amount` to 1 and `weight` equal to the molar mass as placeholders. Change those once you decide what they should mean (e.g., amount in moles, weight = amount × molar mass).
- For the balancing step later, a common approach is combustion: CₓHᵧO\_z + O₂ → CO₂ + H₂O, where you can solve the coefficients from the atom counts you're storing.

Would you like me to go on to the next page, the balanced combustion equation?

> **You**

>
> The next step in my code is I want there be a button to press that produces a balanced combustion reaction based off the hydrocarbon inputted by the user.

Here's the next piece. For a fuel CₓHᵧO\_z burning in oxygen:

CₓHᵧO\_z + a O₂ → x CO₂ + (y/2) H₂O

Balancing oxygen gives a = x + y/4 − z/2, which is often a fraction. To avoid fractions (and keep it beginner-friendly), the code multiplies everything by the smallest whole number that clears them.

**1. Change the end of `set_hydrocarbon`** so the results page has a button:

```
    return Page(state, [
        "Your compound: " + state.hydrocarbon.name,
        "Molar mass: " + str(round(state.hydrocarbon.molar_mass, 3)) + " g/mol",
        Button("Balance combustion reaction", show_reaction),
        Button("Start over", index),
    ])
```

**2. Add these new pieces** (above `start_server`):

```
def get_quantity(compound: Compound, symbol: str) -> int:
    """Return how many atoms of an element the compound has."""
    for e in compound.elements:
        if e.name == symbol:
            return e.quantity
    return 0

def term(coefficient: int, formula: str) -> str:
    """Format one part of the equation, leaving off a coefficient of 1."""
    if coefficient == 1:
        return formula
    return str(coefficient) + " " + formula

@route
def show_reaction(state: State) -> Page:
    fuel = state.hydrocarbon
    x = get_quantity(fuel, "C")
    y = get_quantity(fuel, "H")
    z = get_quantity(fuel, "O")

    # O2 needed per fuel molecule is (4x + y - 2z) / 4
    oxygen_times_4 = 4 * x + y - 2 * z

    if oxygen_times_4 <= 0:
        return Page(state, [
            "This compound already has too much oxygen to combust with O2.",
            Button("Try again", index),
        ])

    # Find the smallest multiplier that makes every coefficient a whole number
    k = 1
    while (k * oxygen_times_4) % 4 != 0 or (k * y) % 2 != 0:
        k = k + 1

    fuel_coef = k
    o2_coef = k * oxygen_times_4 // 4
    co2_coef = k * x
    h2o_coef = k * y // 2

    equation = (term(fuel_coef, fuel.name) + " + " + term(o2_coef, "O2")
                + " → " + term(co2_coef, "CO2") + " + " + term(h2o_coef, "H2O"))

    return Page(state, [
        "Balanced combustion reaction:",
        equation,
        Button("Start over", index),
    ])
```

**How it works**

- `get_quantity` looks through the compound's `elements` list and returns the count for a symbol, so you can read C, H, and O back out of your dataclass.
- `oxygen_times_4` is the numerator of a, using only integers. If it's zero or negative, the fuel can't be burned with O₂, so the page says so instead of printing nonsense.
- The `while` loop tries k = 1, 2, 3, 4 until O₂ (k × n/4) and H₂O (k × y/2) are both whole numbers. Since the denominators can only be 1, 2, or 4, it always stops by 4.
- `term` just keeps the output tidy, so you get `O2` instead of `1 O2`.

**Check it with these inputs**

| C | H | O | Result |
|---|---|---|---|
| 1 | 4 | 0 | CH4 + 2 O2 → CO2 + 2 H2O |
| 2 | 6 | 0 | 2 C2H6 + 7 O2 → 4 CO2 + 6 H2O |
| 2 | 6 | 1 | C2H6O + 3 O2 → 2 CO2 + 3 H2O |

A note on the subscripts: the output uses plain `CO2` and `H2O` since Drafter's text is plain. If you later want real subscripts, you can swap digits for characters like ₂, but plain text is fine for now.

Would you like to add the next step, such as using the molar masses to show how many grams of O₂ are needed for a given amount of fuel?

> **You**

>
> The next thing I want to do is provide the user with the option to, when a weight of hydrocarbon is inputted, outputs the weight of water and carbon dioxide produced based off the balanced reaction. Before this can be done however. the user needs to be prompted with a page that asks if the reaction has limited or excess oxygen. If excess oxygen is selected, then the weight of the reaction can be calculated assuming the hydrocarbon is the limiting reactant. If limited oxygen is chosen, then the user has to input both the weight of the hydrocarbon and the weight of oxygen. Then, the code must calculate to find which is the limiting reactant then find the weight of the products using the limiting reactant.

This step needs the coefficients in more than one place, so first move the balancing math out of `show_reaction` into a helper that both pages can call. Then add the oxygen choice page, the two input pages, and the calculations.

**1. Add these helpers**

(above your routes):

```
M_O2 = 2 * MOLAR_MASS["O"]
M_CO2 = MOLAR_MASS["C"] + 2 * MOLAR_MASS["O"]
M_H2O = 2 * MOLAR_MASS["H"] + MOLAR_MASS["O"]

def get_coefficients(fuel: Compound) -> list[int]:
    """Return [fuel, O2, CO2, H2O] coefficients, or an empty list if it can't combust."""
    x = get_quantity(fuel, "C")
    y = get_quantity(fuel, "H")
    z = get_quantity(fuel, "O")

    oxygen_times_4 = 4 * x + y - 2 * z
    if oxygen_times_4 <= 0:
        return []

    k = 1
    while (k * oxygen_times_4) % 4 != 0 or (k * y) % 2 != 0:
        k = k + 1

    return [k, k * oxygen_times_4 // 4, k * x, k * y // 2]

def parse_positive(text: str) -> float:
    """Turn text into a positive number, or return -1 if it isn't valid."""
    try:
        value = float(text)
    except ValueError:
        return -1.0
    if value <= 0:
        return -1.0
    return value
```

**2. Replace `show_reaction`** so it uses the helper and offers the next step:

```
@route
def show_reaction(state: State) -> Page:
    fuel = state.hydrocarbon
    c = get_coefficients(fuel)

    if len(c) == 0:
        return Page(state, [
            "This compound already has too much oxygen to combust with O2.",
            Button("Try again", index),
        ])

    equation = (term(c[0], fuel.name) + " + " + term(c[1], "O2")
                + " → " + term(c[2], "CO2") + " + " + term(c[3], "H2O"))

    return Page(state, [
        "Balanced combustion reaction:",
        equation,
        Button("Calculate product weights", choose_oxygen),
        Button("Start over", index),
    ])
```

**3. Add the new pages:**

```
@route
def choose_oxygen(state: State) -> Page:
    return Page(state, [
        "Does the reaction have excess or limited oxygen?",
        Button("Excess oxygen", excess_page),
        Button("Limited oxygen", limited_page),
    ])

@route
def excess_page(state: State) -> Page:
    return Page(state, [
        "Oxygen is in excess, so " + state.hydrocarbon.name + " is the limiting reactant.",
        "Weight of " + state.hydrocarbon.name + " (grams):",
        TextBox("fuel_weight", "10"),
        Button("Calculate", calculate_excess),
    ])

@route
def limited_page(state: State) -> Page:
    return Page(state, [
        "Enter the weight of each reactant:",
        "Weight of " + state.hydrocarbon.name + " (grams):",
        TextBox("fuel_weight", "10"),
        "Weight of O2 (grams):",
        TextBox("oxygen_weight", "10"),
        Button("Calculate", calculate_limited),
    ])

@route
def calculate_excess(state: State, fuel_weight: str) -> Page:
    grams_fuel = parse_positive(fuel_weight)
    if grams_fuel < 0:
        return Page(state, [
            "Please enter a number greater than 0.",
            Button("Try again", excess_page),
        ])

    fuel = state.hydrocarbon
    c = get_coefficients(fuel)

    # Fuel is limiting, so it decides how many times the reaction runs
    reaction_amount = (grams_fuel / fuel.molar_mass) / c[0]

    grams_co2 = reaction_amount * c[2] * M_CO2
    grams_h2o = reaction_amount * c[3] * M_H2O

    return Page(state, [
        "Limiting reactant: " + fuel.name,
        "CO2 produced: " + str(round(grams_co2, 3)) + " g",
        "H2O produced: " + str(round(grams_h2o, 3)) + " g",
        Button("Start over", index),
    ])

@route
def calculate_limited(state: State, fuel_weight: str, oxygen_weight: str) -> Page:
    grams_fuel = parse_positive(fuel_weight)
    grams_o2 = parse_positive(oxygen_weight)
    if grams_fuel < 0 or grams_o2 < 0:
        return Page(state, [
            "Please enter numbers greater than 0 for both weights.",
            Button("Try again", limited_page),
        ])

    fuel = state.hydrocarbon
    c = get_coefficients(fuel)

    # How many times could the reaction run if each reactant were used up?
    runs_from_fuel = (grams_fuel / fuel.molar_mass) / c[0]
    runs_from_o2 = (grams_o2 / M_O2) / c[1]

    if runs_from_fuel <= runs_from_o2:
        limiting = fuel.name
        reaction_amount = runs_from_fuel
    else:
        limiting = "O2"
        reaction_amount = runs_from_o2

    grams_co2 = reaction_amount * c[2] * M_CO2
    grams_h2o = reaction_amount * c[3] * M_H2O

    return Page(state, [
        "Limiting reactant: " + limiting,
        "CO2 produced: " + str(round(grams_co2, 3)) + " g",
        "H2O produced: " + str(round(grams_h2o, 3)) + " g",
        Button("Start over", index),
    ])
```

**How it works**

- **`get_coefficients`** is the balancing logic from before, now returning a list `[fuel, O2, CO2, H2O]` so any page can use it.
- **The excess branch** converts grams of fuel to moles (grams ÷ molar mass), then divides by the fuel's coefficient to get how many times the balanced reaction runs. Each product's moles are that number times its coefficient, and moles × molar mass gives grams.
- **The limited branch** computes how many times the reaction could run from each reactant (`runs_from_fuel` and `runs_from_o2`). The smaller number is the limiting reactant, because it runs out first. That smaller number then feeds the same product calculation.
- **Dividing by the coefficient is the key step.** It makes the comparison fair, since a reactant with a larger coefficient is used up faster.
- **`parse_positive`** uses `try/except` to catch letters or blanks, which would otherwise crash `float()`.

**Test values**

| Case | Input | Expected |
|---|---|---|
| Excess O₂ | CH₄, 16.043 g | CO₂ ≈ 44.009 g, H₂O ≈ 36.030 g |
| Limited O₂ | CH₄ 16.043 g, O₂ 32 g | O₂ limiting, CO₂ ≈ 22.0 g, H₂O ≈ 18.015 g |
| Limited O₂ | CH₄ 1 g, O₂ 100 g | CH₄ limiting |

In the second case, 16.043 g of CH₄ is 1 mol, which needs 2 mol of O₂ (64 g). Only 32 g (1 mol) is available, so oxygen runs out first.

Would you like to also show how much of the excess reactant is left over after the reaction?

> **You**

>
> can you check that the total code created abides by the following requirements:

>

> Site Functionality Requirements

>
> Below are the requirements that your site must fulfill. Plan ahead so that meeting these requirements is easier as you develop your project.

>
> \* At least 7 routes.

>
> \* At least 5 Pages, or 10 FragmentsLinks to an external site., or a combination thereof.

>
> \* The implementation of the State dataclass must have at least 4 fields.

>
> \* At least one field must be a list of class instances or a dictionary of class instances.

>
> \* This means that there must be a second dataclass.

>
> \* At least 4 state fields, including the list or dictionary of class instances, must each be meaningfully modified in at least one route; those 4 state fields cannot be constants.

>
> \* At least 3 input fields (TextBox, CheckBox, SelectBox, TextArea). They don't have to be the same type.

>
> \* At least 3 meaningful if statements.

>
> \* At least 1 loop that iterates over an attribute of the list of class instances or dictionary of class instances in a meaningful way.

>
> \* The site should have a legitimate purpose or functionality.

>
> \* No global variables (global constantsLinks to an external site. are fine).

>
> \* You must use the Drafter library.

>
> \* Any advanced coding techniques (i.e. that weren't covered in this course) used are thoroughly documented in the code.

>
> More creative and impressive designs are given flexibility on the above requirements - impress us! However, impressive websites tend to do more than the above requirements. Further, if you miss more than 2 requirements, you will get no credit for that submission. For example, missing a second dataclass means you would be missing not only that requirement, but also the list or dictionary of such dataclass instances, and the loop iterating over that list. This would mean that the submission would get a zero.

>
> Code Requirements

>
> Make sure your program and website runs; broken programs do not earn points. This means that if your program contains a syntax error or runs and doesn't deploy a website, you get zero points for this assignment, and are subject to any other penalties listed in the syllabus.

>
> Once you are finished with your project code, check over the following:

>

> \* Chosen good variable names (check last two sections of Chapter 1B1Links to an external site.)

>
> \* Unit tested your functions where possible, being valid and thoroughLinks to an external site.: each route must have at least one unit test, if possible (routes that have randomization are difficult to unit test, so they are not required to).

>
> \* If a function can't be unit tested, you must note as much in a docstring or comment.

>
> \* Broke up excessively long lines (80 characters is a good rule of thumb, but we'll be strict about not exceeding 120 characters)

>
> \* Included types in your function headers

>
> \* Included good docstrings Links to an external site.as the first line of your function's body

>
> \* Decomposed complicated functions with helper functions

I traced the full code against your checklist, and as written it would **not** pass. Here's the audit:

| Requirement | Status |
|---|---|
| At least 7 routes | ✅ 8 routes |
| At least 5 Pages | ✅ |
| State has at least 4 fields | ❌ State only has `hydrocarbon` |
| A State field is a list/dict of class instances | ❌ `Compound.elements` is inside a Compound, not a State field |
| 4 State fields meaningfully modified in routes | ❌ only 1 |
| At least 3 input fields | ✅ |
| At least 3 meaningful `if` statements | ✅ |
| A loop over the State's list/dict of instances | ❌ the loops go over `elements`, not a State field |
| No global variables | ✅ the all-caps molar masses count as constants |
| Uses Drafter | ✅ |
| Advanced techniques documented | ⚠️ `try/except` should get a comment |
| Good variable names | ⚠️ `c`, `x`, `y`, `z`, `k` need renaming |
| A unit test per route | ❌ none yet |
| Types and docstrings | ⚠️ routes have no docstrings |
| Long functions decomposed | ⚠️ `calculate_excess` and `calculate_limited` duplicate logic |

Missing the State list also kills the loop requirement, so that's three misses. Here's a revised version that fixes everything. I added a `history` list of compounds the user has entered, a **View history** page that loops over it, and two more State fields.

```
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
    if value <= 0:
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
        "Limiting reactant: " + state.limiting_reactant,
        "CO2 produced: " + str(round(weights[0], 3)) + " g",
        "H2O produced: " + str(round(weights[1], 3)) + " g",
        Button("Start over", index),
    ])

# ----------------------------------------------------------------- routes

@route
def index(state: State) -> Page:
    """Show the page where the user enters atom counts of C, H, and O."""
    return Page(state, [
        "Hydrocarbon Reaction Balancer",
        "Enter the number of atoms of each element in your compound:",
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
            "Enter whole numbers only, with at least 1 carbon and 1 hydrogen.",
            Button("Try again", index),
        ])

    state.hydrocarbon = make_compound(int(carbon), int(hydrogen), int(oxygen))
    state.history.append(state.hydrocarbon)

    return Page(state, [
        "Your compound: " + state.hydrocarbon.name,
        "Molar mass: " + str(round(state.hydrocarbon.molar_mass, 3)) + " g/mol",
        Button("Balance combustion reaction", show_reaction),
        Button("Start over", index),
    ])

@route
def show_reaction(state: State) -> Page:
    """Show the balanced combustion equation for the current compound."""
    coefficients = get_coefficients(state.hydrocarbon)
    if len(coefficients) == 0:
        return Page(state, [
            "This compound already has too much oxygen to combust with O2.",
            Button("Try again", index),
        ])

    return Page(state, [
        "Balanced combustion reaction:",
        format_equation(state.hydrocarbon, coefficients),
        Button("Calculate product weights", choose_oxygen),
        Button("Start over", index),
    ])

@route
def choose_oxygen(state: State) -> Page:
    """Ask whether the reaction has excess or limited oxygen."""
    return Page(state, [
        "Does the reaction have excess or limited oxygen?",
        Button("Excess oxygen", excess_page),
        Button("Limited oxygen", limited_page),
    ])

@route
def excess_page(state: State) -> Page:
    """Record excess oxygen and ask for the weight of the hydrocarbon."""
    state.oxygen_mode = "excess"
    return Page(state, [
        "Oxygen is in excess, so " + state.hydrocarbon.name + " is limiting.",
        "Weight of " + state.hydrocarbon.name + " (grams):",
        TextBox("fuel_weight", "10"),
        Button("Calculate", calculate_excess),
    ])

@route
def limited_page(state: State) -> Page:
    """Record limited oxygen and ask for both reactant weights."""
    state.oxygen_mode = "limited"
    return Page(state, [
        "Enter the weight of each reactant:",
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
            "Please enter a number greater than 0.",
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
            "Please enter numbers greater than 0 for both weights.",
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
        return Page(state, ["No compounds entered yet.", Button("Back", index)])

    content = ["Compounds entered this session:"]
    content.extend(history_lines(state.history))
    content.append(Button("Back", index))
    return Page(state, content)

# ------------------------------------------------------------- unit tests

def new_state() -> State:
    """Return a fresh State (used by the tests and by start_server)."""
    return State(Compound("", 1, 0.0, 0.0, []), [], "", "")

def state_with(carbon: int, hydrogen: int, oxygen: int) -> State:
    """Return a State whose hydrocarbon has the given atom counts."""
    state = new_state()
    state.hydrocarbon = make_compound(carbon, hydrogen, oxygen)
    return state

# Helpers
assert_equal(build_formula(make_compound(2, 6, 1).elements), "C2H6O")
assert_equal(round(total_mass(make_compound(1, 4, 0).elements), 3), 16.043)
assert_equal(valid_counts("1", "4", "0"), True)
assert_equal(valid_counts("0", "4", "0"), False)
assert_equal(valid_counts("a", "4", "0"), False)
assert_equal(get_quantity(make_compound(2, 6, 0), "H"), 6)
assert_equal(get_coefficients(make_compound(1, 4, 0)), [1, 2, 1, 2])
assert_equal(get_coefficients(make_compound(2, 6, 0)), [2, 7, 4, 6])
assert_equal(get_coefficients(make_compound(2, 6, 1)), [1, 3, 2, 3])
assert_equal(get_coefficients(make_compound(1, 2, 5)), [])
assert_equal(term(1, "O2"), "O2")
assert_equal(term(3, "O2"), "3 O2")
assert_equal(format_equation(make_compound(1, 4, 0), [1, 2, 1, 2]),
             "CH4 + 2 O2 → CO2 + 2 H2O")
assert_equal(parse_positive("2.5"), 2.5)
assert_equal(parse_positive("abc"), -1.0)
assert_equal(parse_positive("-3"), -1.0)
assert_equal(reaction_runs(32.0, 16.0, 2), 1.0)
assert_equal([round(w, 3) for w in product_weights([1, 2, 1, 2], 1.0)],
             [44.009, 36.03])
assert_equal(history_lines([make_compound(1, 4, 0)]), ["CH4 (16.043 g/mol)"])

# Routes (checked through the state and content of the returned Page)
assert_equal(len(index(new_state()).content) > 0, True)

good_page = set_hydrocarbon(new_state(), "1", "4", "0")
assert_equal(good_page.state.hydrocarbon.name, "CH4")
assert_equal(len(good_page.state.history), 1)
bad_page = set_hydrocarbon(new_state(), "x", "4", "0")
assert_equal(len(bad_page.state.history), 0)

assert_equal(show_reaction(state_with(1, 4, 0)).content[1], "CH4 + 2 O2 → CO2 + 2 H2O")
assert_equal(len(choose_oxygen(new_state()).content), 3)
assert_equal(excess_page(state_with(1, 4, 0)).state.oxygen_mode, "excess")
assert_equal(limited_page(state_with(1, 4, 0)).state.oxygen_mode, "limited")

assert_equal(calculate_excess(state_with(1, 4, 0), "16.043").state.limiting_reactant, "CH4")
assert_equal(calculate_excess(state_with(1, 4, 0), "abc").state.limiting_reactant, "")
assert_equal(calculate_limited(state_with(1, 4, 0), "16.043", "32").state.limiting_reactant, "O2")
assert_equal(calculate_limited(state_with(1, 4, 0), "1", "100").state.limiting_reactant, "CH4")

assert_equal(show_history(new_state()).content[0], "No compounds entered yet.")
history_state = state_with(1, 4, 0)
history_state.history.append(history_state.hydrocarbon)
assert_equal(show_history(history_state).content[1], "CH4 (16.043 g/mol)")

start_server(new_state())
```

**How this now maps to the requirements**

- **State fields:** `hydrocarbon`, `history`, `oxygen_mode`, and `limiting_reactant`. They are changed in `set_hydrocarbon`, `excess_page`/`limited_page`, and `results_page`, which `calculate_excess` and `calculate_limited` call. The `history` list is the list of class instances.
- **Loop over the State list:** `history_lines` loops over `state.history`. It runs on the new History page.
- **Decomposition:** the repeated math is split into `reaction_runs`, `product_weights`, and `results_page`.
- **Naming and docs:** variable names are descriptive, and every function has types and a docstring. The `try/except` is documented as an advanced technique.

**Things to double-check**

- I can't run Drafter here, so please run the file once. If a test fails, the message will tell you which one.
- The tests read `.state` and `.content` from the returned Page. If your version of Drafter lets `assert_equal` compare whole Pages, you can use that instead.
- If Drafter wraps routes in a way that stops you calling them directly, tell me the error and I'll adjust the tests.
- A couple of lines (like the `assert_equal` calls on `calculate_limited`) are close to 100 characters. They're under the 120 limit, but you can break them up if you want to be safe.

> **You**

>
> How would I change the theme of the drafter website to make it look more appealing

Drafter gives you three ways to restyle a site, from easiest to most customizable. I can't run Drafter here, so function names and available themes can vary between versions. If one raises a `NameError` or an unknown-name error, check the Drafter docs (drafter-edu.github.io/drafter) or tell me the error and I'll adjust.

**1. Set a site-wide theme (easiest)**

Add this before `start_server`:

```
set_website_title("Combustion Balancer")
set_website_style("skeleton")   # try other built-in styles to compare
set_website_framed(False)       # hides the Drafter frame around your site
hide_debug_information()        # removes the debug panel at the bottom
```

If your version supports `set_website_style`, changing that one string restyles every page. Run it with a few different style names and keep the one you like best.

**2. Style individual components**

Drafter has helper functions that wrap a component and change how it looks:

```
return Page(state, [
    Header("Hydrocarbon Reaction Balancer", 1),
    change_color("Enter the number of atoms of each element:", "darkgreen"),
    "Carbon (C):", TextBox("carbon", "1"),
    "Hydrogen (H):", TextBox("hydrogen", "4"),
    "Oxygen (O):", TextBox("oxygen", "0"),
    Button("Submit", set_hydrocarbon),
])
```

Other helpers include `change_background_color`, `change_text_size`, `change_text_align`, `change_border`, `change_padding`, `change_width`, `bold`, `italic`, and `monospace`.

**3. Group content with `Div`**

A `Div` lets you apply one style to a whole block, like a card:

```
Div(
    Header("Result", 2),
    "Limiting reactant: " + state.limiting_reactant,
    style_background_color="#eef7ee",
    style_padding="12px",
    style_border="2px solid #4a8f4a",
)
```

**Design tips for this site**

- Give the equation a `monospace` look so it reads like chemistry.
- Put the equation and the product weights each in their own colored `Div` so the results stand out.
- Use `Header` for page titles instead of plain strings, so each page has a clear hierarchy.
- Keep a consistent palette, such as one accent color plus a light background, across all pages.

**Two things to keep in mind**

- Styling calls like `set_website_style` run once at the top level of the file. They're configuration, not variables, so they don't violate the "no global variables" rule.
- Styling code is easy to bloat, so put repeated styling in a helper such as `result_card(text: str) -> Div`. It needs a type header and docstring like your other functions, plus a unit test or a comment explaining why it can't be tested.

If you tell me which of these your version of Drafter accepts, I can restyle your actual pages for you.

> **You**

>
> can you help make this website look a lot better using those things, and where would I put the code you produce in my code

I restyled the whole site and put it in a single file. Replace your current code with it, since the styling touches almost every page. I can't run Drafter here, so run it once. If a style function raises a `NameError`, that function isn't in your Drafter version. Delete that one line (or its helper) and tell me the error.

I put the full restyled site in `combustion_balancer.py`. Paste it over your whole program, because the styling changes almost every page.

**Where each piece goes**

| Piece | Location in the file |
|---|---|
| Color constants (`ACCENT_COLOR`, etc.) | Top, under the molar mass constants |
| Style helpers (`page_title`, `info_card`, `result_card`, `error_card`) | Right after the dataclasses, before your other helpers |
| Restyled routes | Same place as before, using the helpers |
| Site-wide settings (`set_website_title`, `set_website_style`, `set_website_framed`, `hide_debug_information`) | Just before `start_server` |
| Tests for the new helpers | In the unit test section |

**What changed visually**

- Every page has a green `Header` title through `page_title`.
- Instructions sit in a light gray `info_card`.
- Results, such as the molar mass, the equation, and the product weights, sit in a green `result_card`. The equation is `monospace`.
- Errors appear in a red `error_card`, so they're hard to miss.
- Repeated styling lives in four small helpers, so you can change the palette by editing the constants at the top.

**Things to know**

- **Tests changed.** Pages now contain styled components, so comparing `content[1]` to a string would break. The route tests now check that a `Page` is returned and that the State changed. The route tests that check state (`oxygen_mode`, `limiting_reactant`, `history`) are unchanged.
- **Style names.** If `"skeleton"` isn't accepted, try another built-in name or delete that line. The site still works without it.
- **Possible `NameError`.** If `monospace`, `change_color`, or `hide_debug_information` isn't found, delete or replace that call. Tell me which one and I'll adjust.
- **Line length.** A few test lines are close to 100 characters, which is under the 120 limit.

Try a few `set_website_style` names and see which looks best with the green cards.

| [Combustion balancerPY · Click to download](https://claude.ai/api/organizations/c12953ab-2083-4373-9cdd-2afc477c4f8c/conversations/113cce42-1ab9-49e2-bc4a-2cd4b3e99181/wiggle/download-file?path=%2Fmnt%2Fuser-data%2Foutputs%2Fcombustion_balancer.py)

> **You**

>
> could you give me way more unit tests for my code please

I updated `combustion_balancer.py` with a much larger test section, and replacing your whole file with it is the easiest way to use it. The old tests are replaced, not duplicated. There are now well over 150 assertions, and they all pass.

**How I checked them:** I ran the file against a small stand-in for Drafter, which confirmed the expected values and the logic. I couldn't run real Drafter, so run it once in BlockPy. If something fails there, it will most likely be a route test that reads `.state` or `.content`, or one that uses `isinstance(..., TextBox)` or `Button`. Send me the error and I'll adjust.

**A bug I found and fixed**

Python's `float()` accepts the words `"nan"` and `"inf"`, so `parse_positive("nan")` would have passed validation and produced garbage weights. It now rejects both, with a comment explaining why, and the tests cover it.

**What's tested now**

| Area | Examples |
|---|---|---|
| Helpers | empty inputs, 0 or 1 atoms in formulas, big formulas like `C10H22` and glucose |
| `valid_counts` | blanks, negatives, decimals, letters, and zero carbon or hydrogen |
| `get_coefficients` | 9 known fuels, plus the cases that can't combust (too much oxygen, exactly zero O₂ needed) |
| Balancing | `all_balanced()` loops over 11 fuels and checks C, H, and O atoms match on both sides, which catches wrong coefficients that a hand-written answer might miss |
| `parse_positive` | `""`, spaces, `0`, negatives, `1,5`, `nan`, `inf` |
| Math | `reaction_runs` with different coefficients, `product_weights` at 0, 0.5, 1, and 2 runs |
| Routes | each route's page contents (3 text boxes on `index`, 1 or 2 on the weight pages), invalid input leaving the State unchanged, and history growing in order |
| Calculations | limiting reactant for 5 fuel and oxygen combinations, plus 14 bad inputs across both calculate routes |
| Workflows | two full runs, enter compound → choose oxygen mode → calculate |

**Notes**

- Route tests count components with a helper, `count_type`, instead of comparing page text. That keeps them working after styling changes.
- The test helpers (`count_type`, `is_balanced`, `all_balanced`) have types and docstrings, so they meet the requirements too.
- No line is over 100 characters.

| [Combustion balancerPY · Click to download](https://claude.ai/api/organizations/c12953ab-2083-4373-9cdd-2afc477c4f8c/conversations/113cce42-1ab9-49e2-bc4a-2cd4b3e99181/wiggle/download-file?path=%2Fmnt%2Fuser-data%2Foutputs%2Fcombustion_balancer.py)

> **You**

>
> When code was run in github, an error was detected, can you please figure out the origin and fix it. The error message is pasted below:

>

> 3s

>
> Run set -o pipefail

>
> set -o pipefail

>
> MAIN\_FILE="main.py"

>
> MYPY\_CONFIG="mypy.ini"

>
> # Respect a student/instructor-provided config. Otherwise use the

>
> # same Bakery compatibility rule as the previous workflow, without

>
> # modifying the repository during the build.

>
> if \[\[ ! -f "$MYPY\_CONFIG" \]\]; then

>
> MYPY\_CONFIG="$RUNNER\_TEMP/drafter-mypy.ini"

>
> cat > "$MYPY\_CONFIG" <<'INI'

>
> \[mypy\]

>
> \[mypy-bakery.\*\]

>
> ignore\_missing\_imports = True

>
> INI

>
> fi

>
> "$DIAGNOSTIC\_VENV/bin/python" -m mypy \\

>
> \--config-file "$MYPY\_CONFIG" \\

>
> "$MAIN\_FILE" \\

>
> 2>&1 | tee \_site/dashboard/type.txt

>
> shell: /usr/bin/bash --noprofile --norc -e -o pipefail {0}

>
> env:

>

> DRAFTER\_SPEC: drafter>=2,<3

>
> DIAGNOSTIC\_VENV: .venv

>
> STUDENT\_REQUIREMENTS: .drafter-student-requirements.txt

>
> UV\_CACHE\_DIR: /home/runner/work/\_temp/setup-uv-cache

>
> main.py:266: error: Argument 1 to "result\_card" has incompatible type "Component | int | float | Sequence\[Component | str | int | float | bool\]"; expected "str" \[arg-type\]

>
> Found 1 error in 1 file (checked 1 source file)

>
> Error: Process completed with exit code 1.

I fixed the mypy error in `combustion_balancer.py`. Copy it into your `main.py`.

**What changed**

- **New helper `equation_card(equation: str) -> Div`.** It builds the same green card as `result_card`, but wraps the equation in `monospace(...)` itself.
- **`show_reaction` now calls `equation_card(...)`.** Before, it called `result_card(monospace(...))`, which was the line mypy flagged (line 266 in your file).
- **One new unit test** checks that `equation_card` returns a `Div`, so every function still has a test.

`result_card`, `info_card`, and `error_card` are unchanged. They still take plain text, which is what their `str` type hints say.

**Verification:** The tests still pass against my stand-in for Drafter. I couldn't run mypy here because it isn't installed in my environment, so your GitHub check is the real test. mypy only reported one error in your run, so this should clear it. If it reports a new one, paste it and I'll fix that too.

**Tip:** Any helper that takes a styled item, like `monospace(...)`, `bold(...)`, or `change_color(...)`, can't be typed `str`. Either give it a dedicated helper like this one, or pass it straight into `Div(...)`, which accepts components.

| [Combustion balancerPY · Click to download](https://claude.ai/api/organizations/c12953ab-2083-4373-9cdd-2afc477c4f8c/conversations/113cce42-1ab9-49e2-bc4a-2cd4b3e99181/wiggle/download-file?path=%2Fmnt%2Fuser-data%2Foutputs%2Fcombustion_balancer.py)
