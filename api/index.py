from pathlib import Path
import math
import random
import re

import sympy as sp
from flask import Flask, jsonify, render_template, request


# ============================================================
# FLASK SETUP
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

app = Flask(
    __name__,
    template_folder=str(PROJECT_ROOT / "templates"),
    static_folder=str(PROJECT_ROOT / "static"),
)


# ============================================================
# NUMBER FORMATTING
# ============================================================

def format_number(value, decimals=6):
    """Format a number for human-readable display."""

    try:
        value = float(value)
    except (TypeError, ValueError):
        return str(value)

    if not math.isfinite(value):
        return "undefined"

    if abs(value) < 1e-12:
        return "0"

    if abs(value - round(value)) < 1e-10:
        return str(int(round(value)))

    return f"{value:.{decimals}f}".rstrip("0").rstrip(".")


def safe_float(value):
    """Convert a value to a finite float."""

    try:
        value = float(value)

        if math.isfinite(value):
            return value

    except (TypeError, ValueError):
        pass

    return 0.0


# ============================================================
# PROPORTIONAL ERROR
# ============================================================

def proportional_delta(
    value,
    min_percent=0.01,
    max_percent=0.05,
):
    """
    Create an error proportional to the magnitude of a number.

    The important thing is that this is based on RELATIVE size.

    Example:

        10       -> tiny delta
        1,000    -> larger delta
        100,000  -> much larger delta

    This is useful when making a large intermediate calculation
    slightly inaccurate.
    """

    magnitude = max(abs(value), 1.0)

    percentage = random.uniform(
        min_percent,
        max_percent,
    ) / 100

    direction = random.choice(
        [-1, 1]
    )

    return magnitude * percentage * direction


# ============================================================
# RANDOM "MATHEMATICAL" COEFFICIENTS
# ============================================================

# Deliberately avoiding obvious powers of ten.
#
# These should look like numbers a strange calculator might
# have chosen for some completely unnecessary reason.

COEFFICIENTS = [
    137,
    211,
    283,
    347,
    419,
    563,
    691,
    719,
    827,
    847,
    913,
    1043,
    1171,
    1283,
    1429,
    1571,
    1639,
    1783,
    1931,
    2143,
    2267,
    2381,
    2543,
    2677,
    2837,
    3011,
    3187,
    3371,
    3529,
    3761,
    3911,
    4093,
    4217,
    4481,
    4723,
    5021,
]


def random_coefficient():
    """Return a random non-obvious scaling coefficient."""

    return random.choice(
        COEFFICIENTS
    )


# ============================================================
# REAL MATHEMATICAL ANSWER
# ============================================================

def calculate_real_answer(expression):
    """
    Calculate the actual answer using SymPy.

    Only basic arithmetic is accepted here.
    """

    expression = expression.strip()

    if not expression:
        raise ValueError(
            "You forgot to give me something to calculate."
        )

    # --------------------------------------------------------
    # Only basic arithmetic.
    # --------------------------------------------------------

    allowed_pattern = r"[0-9+\-*/().\s^√]+"

    if not re.fullmatch(
        allowed_pattern,
        expression,
    ):
        raise ValueError(
            "Only basic arithmetic is supported."
        )

    # Calculator-style square root.
    expression = expression.replace(
        "√",
        "sqrt",
    )

    # Allow ^ as exponent.
    expression = expression.replace(
        "^",
        "**",
    )

    try:

        result = sp.sympify(
            expression,
            locals={
                "sqrt": sp.sqrt,
            },
        )

    except Exception:

        raise ValueError(
            "I could not understand that equation."
        )

    if not result.is_number:
        raise ValueError(
            "That does not produce a number."
        )

    try:

        evaluated = complex(
            result.evalf()
        )

    except Exception:

        raise ValueError(
            "I could not evaluate that equation."
        )

    # --------------------------------------------------------
    # Reject imaginary answers.
    # --------------------------------------------------------

    if abs(evaluated.imag) > 1e-10:
        raise ValueError(
            "That calculation produced an imaginary number."
        )

    answer = evaluated.real

    if not math.isfinite(answer):
        raise ValueError(
            "That calculation produced an invalid number."
        )

    return float(answer)


# ============================================================
# SPECIAL EXPRESSIONS
# ============================================================

TRIG_FUNCTIONS = (
    "sin",
    "cos",
    "tan",
    "cot",
    "sec",
    "csc",
    "arcsin",
    "arccos",
    "arctan",
    "sinh",
    "cosh",
    "tanh",
    "log",
    "ln",
)


def detect_special_expression(expression):
    """
    Detect calculations that should be redirected to YouTube.
    """

    lowered = (
        expression
        .lower()
        .replace(" ", "")
    )

    # --------------------------------------------------------
    # FACTORIAL
    # --------------------------------------------------------

    if "!" in lowered:

        return {
            "type": "redirect",
            "category": "factorial",
            "message": (
                "Factorial detected. "
                "The calculator has decided this is above "
                "its emotional pay grade."
            ),
            "url": (
                "https://youtu.be/TGHR18RmtxI"
            ),
        }

    elif "integral(" in lowered :
        return {
            "type" : "redirect",
            "category" : "integral",
            "message" : ("Do you really want me to do this ?!🫩"),
            "url" : ("https://youtu.be/DvTQ7h6-m5I"),
        }

    # --------------------------------------------------------
    # TRIG / LOG FUNCTIONS
    # --------------------------------------------------------

    for function in TRIG_FUNCTIONS:

        if lowered.startswith(
            function + "("
        ):

            return {
                "type": "redirect",
                "category": "advanced_math",
                "message": (
                    f"{function} detected. "
                    "Please consult a more qualified calculator."
                ),
                "url": (
                    "https://youtu.be/FGNj7BCO050"
                ),
            }

    return None


# ============================================================
# INTENTIONALLY WRONG STEP ENGINE
# ============================================================

# These operations are deliberately consequential: unlike the old
# "x * n / n" style operations, each one changes the current value.
#
# The real answer is kept private and is used only to steer the final
# result toward a believable wrong answer.

def random_nonzero(low, high):
    value = 0
    while value == 0:
        value = random.randint(low, high)
    return value


def step_add(x):
    amount = random.randint(-97, 113)
    if amount == 0:
        amount = 17

    result = x + amount

    return (
        result,
        "Applying an offset correction",
        f"{format_number(x)} + ({amount})",
    )


def step_subtract(x):
    amount = random.randint(7, 89)
    result = x - amount

    return (
        result,
        "Removing an intermediate adjustment",
        f"{format_number(x)} - {amount}",
    )


def step_multiply(x):
    factor = random.choice([
        1.13, 1.27, 1.41, 1.63, 1.87,
        2.17, 2.31, 2.73, 3.11,
    ])

    result = x * factor

    return (
        result,
        "Applying a scaling transformation",
        f"{format_number(x)} × {format_number(factor)}",
    )


def step_divide(x):
    divisor = random.choice([
        1.17, 1.29, 1.43, 1.61, 1.83,
        2.07, 2.37, 2.71, 3.13,
    ])

    result = x / divisor

    return (
        result,
        "Reducing the intermediate magnitude",
        f"{format_number(x)} ÷ {format_number(divisor)}",
    )


def step_affine(x):
    factor = random.choice([
        0.73, 0.81, 0.93, 1.07, 1.19, 1.31,
    ])
    offset = random.randint(-31, 37)

    result = (x * factor) + offset

    return (
        result,
        "Applying a weighted numerical adjustment",
        f"({format_number(x)} × {format_number(factor)}) + ({offset})",
    )


def step_percentage(x):
    percentage = random.choice([
        7, 11, 13, 17, 19, 23, 29, 31
    ])

    result = x * (1 + percentage / 100)

    return (
        result,
        "Applying a percentage-based correction",
        f"{format_number(x)} × (1 + {percentage}%)",
    )


def step_root(x):
    # Keep the operation real and non-identity.
    magnitude = abs(x)
    result = math.sqrt(magnitude + 1)

    if x < 0:
        result = -result

    return (
        result,
        "Compressing the numerical magnitude",
        f"sgn({format_number(x)}) × √(|{format_number(x)}| + 1)",
    )


def step_logarithmic(x):
    magnitude = abs(x)
    result = math.log1p(magnitude)

    if x < 0:
        result = -result

    return (
        result,
        "Applying a logarithmic normalization",
        f"sgn({format_number(x)}) × ln(|{format_number(x)}| + 1)",
    )


def step_power(x):
    # A bounded power transformation. The cube-root-like branch prevents
    # enormous values while still producing a meaningful change.
    if abs(x) <= 20:
        result = x * x + 1
        formula = f"({format_number(x)})² + 1"
    else:
        result = math.copysign(abs(x) ** 0.73, x)
        formula = f"sgn({format_number(x)}) × |{format_number(x)}|^0.73"

    return (
        result,
        "Applying a nonlinear magnitude transformation",
        formula,
    )


def step_sine_adjustment(x):
    result = x + math.sin(x) * random.choice([
        3.7, 5.3, 7.1, 8.9
    ])

    return (
        result,
        "Applying a periodic numerical adjustment",
        f"{format_number(x)} + sin({format_number(x)}) × adjustment",
    )


def step_weighted_average(x):
    anchor = random.randint(-40, 80)
    weight = random.choice([0.27, 0.41, 0.58, 0.67, 0.79])

    result = (x * weight) + (anchor * (1 - weight))

    return (
        result,
        "Reweighting the intermediate value",
        f"{format_number(x)} × {format_number(weight)} + "
        f"{anchor} × {format_number(1 - weight)}",
    )


def step_precision_shift(x):
    # This is not merely formatting: the rounded value is fed into the
    # following calculation, so it genuinely changes the state.
    decimals = random.choice([2, 3, 4, 5])
    rounded = round(x, decimals)

    shift = random.choice([
        -0.037, -0.019, 0.013, 0.027, 0.041
    ])

    result = rounded + shift

    return (
        result,
        "Applying a finite-precision correction",
        f"round({format_number(x, 7)}, {decimals}) + {format_number(shift)}",
    )


def step_reciprocal_shift(x):
    # Avoid zero and avoid an exact reciprocal-only operation.
    safe_x = x if abs(x) > 0.05 else (x + 0.37)
    adjustment = random.choice([0.13, 0.21, 0.34, 0.47])

    result = (1 / safe_x) + adjustment

    return (
        result,
        "Transforming the intermediate reciprocal",
        f"(1 ÷ {format_number(safe_x)}) + {format_number(adjustment)}",
    )


def step_calibration(x, real_answer):
    """
    Steer the wandering calculation toward a subtly wrong destination.

    The target is never displayed directly. The displayed operation is
    expressed as a small correction of the current value.
    """
    if abs(real_answer) > 1e-12:
        error_size = random.uniform(0.0015, 0.012)
        error_direction = random.choice([-1, 1])
        target = real_answer * (1 + error_size * error_direction)
    else:
        target = random.uniform(-0.05, 0.05)

    # A multiplicative correction is used where possible.
    if abs(x) > 1e-9:
        factor = target / x
        result = x * factor

        return (
            result,
            "Applying a final numerical calibration",
            f"{format_number(x)} × {format_number(factor, 8)}",
        )

    offset = target - x
    result = x + offset

    return (
        result,
        "Applying a final numerical calibration",
        f"{format_number(x)} + {format_number(offset, 8)}",
    )


OPERATIONS = [
    {
        "name": "add",
        "family": "offset",
        "run": step_add,
    },
    {
        "name": "subtract",
        "family": "offset",
        "run": step_subtract,
    },
    {
        "name": "multiply",
        "family": "scaling",
        "run": step_multiply,
    },
    {
        "name": "divide",
        "family": "scaling",
        "run": step_divide,
    },
    {
        "name": "affine",
        "family": "weighted",
        "run": step_affine,
    },
    {
        "name": "percentage",
        "family": "percentage",
        "run": step_percentage,
    },
    {
        "name": "root",
        "family": "nonlinear",
        "run": step_root,
    },
    {
        "name": "logarithmic",
        "family": "nonlinear",
        "run": step_logarithmic,
    },
    {
        "name": "power",
        "family": "nonlinear",
        "run": step_power,
    },
    {
        "name": "sine_adjustment",
        "family": "periodic",
        "run": step_sine_adjustment,
    },
    {
        "name": "weighted_average",
        "family": "weighted",
        "run": step_weighted_average,
    },
    {
        "name": "precision_shift",
        "family": "precision",
        "run": step_precision_shift,
    },
    {
        "name": "reciprocal_shift",
        "family": "reciprocal",
        "run": step_reciprocal_shift,
    },
]


def choose_operation(available, previous_name, previous_family):
    """
    Prefer a different operation and conceptual family so the calculation
    does not visibly repeat itself.
    """
    candidates = [
        operation
        for operation in available
        if operation["name"] != previous_name
        and operation["family"] != previous_family
    ]

    if not candidates:
        candidates = [
            operation
            for operation in available
            if operation["name"] != previous_name
        ]

    if not candidates:
        return None

    return random.choice(candidates)


def determine_step_count(expression):
    """
    Produce a variable number of steps. The calculation is deliberately
    long enough to feel absurd, but not so long that it becomes tedious.
    """
    operators = len(re.findall(r"[+\-*/^]", expression))
    numbers = len(re.findall(r"\d+(?:\.\d+)?", expression))

    base = random.randint(12, 17)
    complexity_bonus = operators * random.randint(1, 3)
    number_bonus = min(max(numbers - 2, 0), 4)

    return min(base + complexity_bonus + number_bonus, 24)


def generate_initial_value(expression, real_answer):
    """
    Produce the first displayed numerical value without revealing the
    correct answer.

    The expression itself is evaluated privately, then immediately passed
    through a non-reversible transformation.
    """
    coefficient = random.choice([
        137, 211, 283, 347, 419, 563, 691, 719,
        827, 913, 1043, 1171, 1283, 1429
    ])

    offset = random.choice([-37, -23, 17, 29, 41])

    result = (real_answer * coefficient) + offset

    return (
        result,
        "Initializing the numerical transformation",
        f"({expression}) × {coefficient} + ({offset})",
    )


def generate_calculation(expression, real_answer):
    """
    Generate the intentionally wrong calculation.

    Important differences from the old engine:
      * Step 1 does NOT display the real answer.
      * Every ordinary step changes the numerical state.
      * The real answer is never inserted into an ordinary step.
      * A private final calibration produces a believable small error.
    """
    target_steps = determine_step_count(expression)

    # Step 1 starts from the expression but immediately transforms it.
    current_value, description, formula = generate_initial_value(
        expression,
        real_answer,
    )

    steps = [
        {
            "number": 1,
            "description": description,
            "formula": formula,
            "result": format_number(current_value),
        }
    ]

    previous_name = "initialization"
    previous_family = "initialization"
    available = OPERATIONS.copy()

    # Reserve calibration for the end.
    normal_operations = [
        operation
        for operation in available
        if operation["name"] != "calibration"
    ]

    # We deliberately use fewer operations than the old engine because the
    # new operations actually alter the value.
    while len(steps) < target_steps - 1 and normal_operations:
        operation = choose_operation(
            normal_operations,
            previous_name,
            previous_family,
        )

        if operation is None:
            break

        normal_operations.remove(operation)

        old_value = current_value

        try:
            new_value, description, formula = operation["run"](
                current_value
            )
            new_value = safe_float(new_value)
        except Exception:
            current_value = old_value
            continue

        if not math.isfinite(new_value):
            current_value = old_value
            continue

        # Prevent pathological explosions without forcing the value to stay
        # near the real answer.
        if abs(new_value) > 1e12:
            current_value = old_value
            continue

        # Avoid accidental no-op steps caused by floating-point rounding.
        if abs(new_value - old_value) <= max(
            1e-12,
            abs(old_value) * 1e-12,
        ):
            current_value = old_value
            continue

        current_value = new_value

        steps.append(
            {
                "number": len(steps) + 1,
                "description": description,
                "formula": formula,
                "result": format_number(current_value),
            }
        )

        previous_name = operation["name"]
        previous_family = operation["family"]

    # Final calibration is the only stage allowed to know the true answer.
    calibrated_value, description, formula = step_calibration(
        current_value,
        real_answer,
    )

    current_value = calibrated_value

    steps.append(
        {
            "number": len(steps) + 1,
            "description": description,
            "formula": formula,
            "result": format_number(current_value),
        }
    )

    # Final rounding creates the displayed answer.
    current_value = round(current_value, 4)
    steps[-1]["result"] = format_number(current_value)

    if abs(real_answer) > 1e-12:
        error_percentage = (
            abs(current_value - real_answer)
            / abs(real_answer)
        ) * 100
    else:
        error_percentage = abs(current_value)

    if error_percentage < 0.05:
        confidence = random.uniform(99.6, 100.0)
    elif error_percentage < 0.2:
        confidence = random.uniform(99.0, 99.8)
    elif error_percentage < 0.7:
        confidence = random.uniform(98.0, 99.5)
    else:
        confidence = random.uniform(96.5, 99.2)

    return {
        "type": "calculation",
        "steps": steps,
        "answer": format_number(current_value),
        "confidence": round(confidence, 1),
    }


# ============================================================
# HOME ROUTE
# ============================================================

@app.route("/")
def home():

    return render_template(
        "index.html"
    )


# ============================================================
# CALCULATE ROUTE
# ============================================================

@app.route(
    "/calculate",
    methods=["POST"],
)
def calculate():

    data = request.get_json(
        silent=True
    ) or {}

    expression = str(
        data.get(
            "expression",
            "",
        )
    ).strip()

    # --------------------------------------------------------
    # Empty expression.
    # --------------------------------------------------------

    if not expression:

        return jsonify(
            {
                "type": "error",

                "message": (
                    "You forgot to give me "
                    "something to calculate."
                ),
            }
        ), 400

    # --------------------------------------------------------
    # Special expressions.
    # --------------------------------------------------------

    special = (
        detect_special_expression(
            expression
        )
    )

    if special:

        return jsonify(
            special
        )

    # --------------------------------------------------------
    # Calculate.
    # --------------------------------------------------------

    try:

        real_answer = (
            calculate_real_answer(
                expression
            )
        )

        result = (
            generate_calculation(
                expression,
                real_answer,
            )
        )

        return jsonify(
            result
        )

    except ValueError as error:

        return jsonify(
            {
                "type": "error",
                "message": str(error),
            }
        ), 400

    except Exception as error:

        print(
            "Unexpected calculation error:",
            error,
        )

        return jsonify(
            {
                "type": "error",

                "message": (
                    "The calculator encountered "
                    "an unexpected mathematical situation."
                ),
            }
        ), 500


# ============================================================
# LOCAL DEVELOPMENT
# ============================================================

if __name__ == "__main__":

    print()
    print(
        "======================================"
    )
    print(
        "     EQUAL TO CALCULATOR"
    )
    print(
        "======================================"
    )
    print(
        "Running at:"
    )
    print(
        "http://127.0.0.1:5000"
    )
    print(
        "======================================"
    )
    print()

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True,
    )
