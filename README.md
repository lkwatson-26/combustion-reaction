# Hydrocarbon Combustion Balancer

A website built with the [Drafter](https://drafter-edu.github.io/drafter/) library (Python).
The user enters the number of carbon (C), hydrogen (H), and oxygen (O) atoms in a compound.
The site then:

1. builds the compound and calculates its molar mass,
2. balances its complete combustion reaction with O₂,
3. finds the limiting reactant, and
4. calculates the mass (in grams) of CO₂ and H₂O produced.

## Scope

| Supported | Not supported |
|---|---|
| Compounds containing only C, H, and O | Other elements (N, S, etc.) |
| Complete combustion: fuel + O₂ → CO₂ + H₂O | Incomplete combustion (CO, soot) |
| Whole-number atom counts | Decimal or negative atom counts |
| Mass input in grams | Other units, or input in moles |
| History for the current session only | Saving data between sessions |

Compounds that need no extra O₂ (when 4C + H − 2O ≤ 0, for example C=1, H=2, O=5) cannot be
balanced by this method. `get_coefficients` returns an empty list for them, and
`show_reaction` displays an error message instead.

## Using the site

| Step | Page | User action | Result |
|---|---|---|---|
| 1 | Hydrocarbon Reaction Balancer (`index`) | Enter atom counts of C, H, O. Press **Submit**. | Valid if all are whole numbers, C ≥ 1, and H ≥ 1. Otherwise an error page appears. |
| 2 | Your Compound (`set_hydrocarbon`) | Press **Balance combustion reaction**. | Shows the formula and molar mass (g/mol, 3 decimals). The compound is added to the history. |
| 3 | Balanced Reaction (`show_reaction`) | Press **Calculate product weights**. | Shows the balanced equation. |
| 4 | Oxygen Supply (`choose_oxygen`) | Choose **Excess oxygen** or **Limited oxygen**. | Goes to step 5a or 5b. |
| 5a | Excess Oxygen (`excess_page`) | Enter grams of hydrocarbon. Press **Calculate**. | The hydrocarbon is the limiting reactant. |
| 5b | Limited Oxygen (`limited_page`) | Enter grams of hydrocarbon and grams of O₂. Press **Calculate**. | The program finds the limiting reactant. |
| 6 | Results (`results_page`) | Read the output. | Limiting reactant, grams of CO₂, and grams of H₂O (3 decimals). |

The **View history** button on the first page (`show_history`) lists every compound entered
this session.

## How the calculations work

**Balancing** (`get_coefficients`). For a fuel with x C, y H, and z O atoms:

```
CxHyOz + a O2 → x CO2 + (y/2) H2O,   where a = x + y/4 − z/2
```

The code works with integers only: it computes `4x + y − 2z` (which equals 4a) and multiplies
all coefficients by the smallest multiplier (1 to 4) that makes `a` and `y/2` whole numbers.
It returns `[fuel, O2, CO2, H2O]`.

**Mass calculation** (`reaction_runs`, `product_weights`):

1. `runs = (grams ÷ molar mass) ÷ coefficient`, calculated for each reactant provided.
2. The reactant with the **smaller** `runs` is the limiting reactant. On a tie, the hydrocarbon
   is reported.
3. Grams of product = `runs × product coefficient × product molar mass`.

**Constants:** molar masses of C = 12.011, H = 1.008, O = 15.999 g/mol, giving
O₂ = 31.998, CO₂ = 44.009, and H₂O = 18.015 g/mol.

### Worked examples (outputs produced by the program)

| Input | Balanced equation | Limiting reactant | CO₂ (g) | H₂O (g) |
|---|---|---|---|---|
| CH₄, 16.043 g, excess O₂ | CH4 + 2 O2 → CO2 + 2 H2O | CH4 | 44.009 | 36.03 |
| CH₄, 16.043 g; O₂, 32 g | CH4 + 2 O2 → CO2 + 2 H2O | O2 | 22.006 | 18.016 |
| C₂H₆, 30.07 g; O₂, 100 g | 2 C2H6 + 7 O2 → 4 CO2 + 6 H2O | O2 | 78.592 | 48.257 |

## Code structure (`main.py`)

**Dataclasses**

| Class | Fields |
|---|---|
| `Element` | `name: str`, `quantity: int`, `molar_mass: float` |
| `Compound` | `name: str`, `amount: int`, `molar_mass: float`, `weight: float`, `elements: list[Element]` |
| `State` | `hydrocarbon: Compound`, `history: list[Compound]`, `oxygen_mode: str`, `limiting_reactant: str` |

**Where each State field is changed**

| Field | Changed in |
|---|---|
| `hydrocarbon` | `set_hydrocarbon` (replaced with the new compound) |
| `history` | `set_hydrocarbon` (new compound appended) |
| `oxygen_mode` | `excess_page` (`"excess"`) and `limited_page` (`"limited"`) |
| `limiting_reactant` | `results_page`, called by `calculate_excess` and `calculate_limited` |

**Routes (9):** `index`, `set_hydrocarbon`, `show_reaction`, `choose_oxygen`, `excess_page`,
`limited_page`, `calculate_excess`, `calculate_limited`, `show_history`.

**Helper functions**

| Group | Functions |
|---|---|
| Style | `page_title`, `info_card`, `result_card`, `equation_card`, `error_card` |
| Compound building | `make_compound`, `total_mass`, `build_formula`, `get_quantity`, `valid_counts` |
| Chemistry | `get_coefficients`, `term`, `format_equation`, `reaction_runs`, `product_weights` |
| Other | `parse_positive`, `history_lines`, `results_page` |

**Input handling.** There are 6 `TextBox` inputs: 3 on `index` (`carbon`, `hydrogen`, `oxygen`),
1 on `excess_page` (`fuel_weight`), and 2 on `limited_page` (`fuel_weight`, `oxygen_weight`).
All values arrive as strings. Atom counts are checked with `valid_counts`, and weights with
`parse_positive`, which accepts only finite numbers greater than 0.

**Advanced technique.** `parse_positive` uses `try/except ValueError` to handle text such as
`"abc"` without crashing. It also rejects `"nan"` and `"inf"`, which Python's `float()`
accepts. This is documented in a comment in the code.

## Testing

`main.py` contains 152 `assert_equal` calls (several are inside loops, so more checks run than
calls appear). They cover every helper function and every route.

- Helper functions are tested against known values (for example, CH₄ molar mass = 16.043).
- `all_balanced()` checks 11 fuels and confirms that the C, H, and O atom counts match on both
  sides of each balanced equation.
- Invalid input (blank, letters, zero, negatives, decimals, `nan`, `inf`) is tested to confirm
  the State is not changed.
- Route tests check the State after the route runs and the type and number of components on the
  returned `Page`. They do not compare page text, because styled pages contain Drafter
  components.
- Two full workflows are tested from compound entry through to the limiting reactant.

The GitHub workflow also runs `mypy` on `main.py` as a type check.

## Requirements checklist

| Requirement | How it is met |
|---|---|
| At least 7 routes | 9 routes (listed above) |
| At least 5 pages | 8 normal pages (`index`, `set_hydrocarbon`, `show_reaction`, `choose_oxygen`, `excess_page`, `limited_page`, results, history) plus error pages |
| State with at least 4 fields | `hydrocarbon`, `history`, `oxygen_mode`, `limiting_reactant` |
| A State field holds class instances | `history: list[Compound]` |
| 4 State fields modified in routes | See "Where each State field is changed" |
| At least 3 input fields | 6 `TextBox` inputs |
| At least 3 meaningful `if` statements | Input validation (`set_hydrocarbon`, `calculate_excess`, `calculate_limited`), limiting-reactant comparison (`calculate_limited`), empty-history check (`show_history`), and more |
| Loop over the State list | `history_lines` loops over `state.history`; it is called by `show_history` |
| No global variables | Only all-caps constants at the top level |
| Types, docstrings, helper functions, tests | Every function has type hints and a docstring; every route has tests |

## Running the project

1. Install Drafter: `pip install drafter` (or run in BlockPy).
2. Run `main.py`.
3. Open the local address that Drafter prints in the console.

## How AI was used

I used **Claude** (made by Anthropic) as a coding assistant, one step at a time, across these
stages. *(Edit the "My part" column so it states exactly what you did.)*

| Stage | My part | What Claude did |
|---|---|---|
| Input page | Specified the `Element` and `Compound` dataclasses and the C, H, O input | Showed how Drafter `TextBox` values arrive as strings and wrote the validation and the code that builds the `Compound` |
| Balancing | Requested a balanced combustion reaction from the stored compound | Derived `a = x + y/4 − z/2` and wrote the integer-only method that finds whole-number coefficients |
| Excess / limited oxygen | Specified the excess/limited choice and what to calculate for each | Wrote `reaction_runs`, `product_weights`, and the limiting-reactant comparison |
| Requirements check | Provided the assignment requirements | Found missing items (State list, 4 fields, loop over the list, per-route tests) and added `history` and the History page to fix them |
| Styling | Asked for a more appealing design | Wrote the style helpers and the site-wide settings |
| Unit tests | Asked for more tests | Wrote the expanded test suite and found the `"nan"` / `"inf"` bug in `parse_positive` |
| Debugging | Ran the GitHub check and supplied the mypy error | Identified that a styled component was passed to a `str` parameter and fixed it with `equation_card` |
| Documentation | Requested this README | Drafted it from the finished code |

**Limits of the AI's work.** Claude could not run Drafter. It checked the pure logic and tests
using a stand-in for the Drafter library, so Drafter-specific code (styling functions, page
components) was verified only by running it myself. Some function names and style options
depend on the installed Drafter version.

**How I verified the result** *(keep only what is true for you)*

- Ran the program and the unit tests myself.
- Compared outputs to hand calculations, for example 16.043 g of CH₄ producing 44.009 g of CO₂
  and 36.03 g of H₂O.
- Checked that the GitHub `mypy` check passes.
- Read through the code so I can explain each function.
