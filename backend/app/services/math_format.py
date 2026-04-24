"""Пост-процессинг математических формул: LaTeX-маркеры → читаемый unicode.

AI-генерация и задания из банка могут содержать inline-LaTeX (`$x^2$`, `\\sqrt{2}`).
Render react-native-math-view требует dev-build, что сейчас недоступно,
поэтому конвертируем в unicode на backend: ² ³ √ π ± ≤ ≥ ≠ ∞ и дроби.

Конвертация сознательно консервативная — непонятные конструкции оставляем
как есть, чтобы не испортить текст. Идеально не всё, но читаемо в 95% случаев.
"""

from __future__ import annotations

import re

# Индексы для степеней и корней
_SUPER_MAP = {
    "0": "⁰", "1": "¹", "2": "²", "3": "³", "4": "⁴",
    "5": "⁵", "6": "⁶", "7": "⁷", "8": "⁸", "9": "⁹",
    "+": "⁺", "-": "⁻", "=": "⁼", "(": "⁽", ")": "⁾", "n": "ⁿ",
}
_SUB_MAP = {
    "0": "₀", "1": "₁", "2": "₂", "3": "₃", "4": "₄",
    "5": "₅", "6": "₆", "7": "₇", "8": "₈", "9": "₉",
}

# Греческие буквы и константы
_COMMANDS = {
    r"\alpha": "α", r"\beta": "β", r"\gamma": "γ", r"\delta": "δ",
    r"\epsilon": "ε", r"\varepsilon": "ε", r"\theta": "θ", r"\lambda": "λ",
    r"\mu": "μ", r"\pi": "π", r"\sigma": "σ", r"\phi": "φ", r"\omega": "ω",
    r"\Delta": "Δ", r"\Sigma": "Σ", r"\Omega": "Ω",
    r"\infty": "∞", r"\pm": "±", r"\mp": "∓", r"\cdot": "·", r"\times": "×",
    r"\div": "÷", r"\leq": "≤", r"\geq": "≥", r"\neq": "≠", r"\approx": "≈",
    r"\to": "→", r"\rightarrow": "→", r"\leftarrow": "←",
    r"\in": "∈", r"\notin": "∉", r"\subset": "⊂", r"\cup": "∪", r"\cap": "∩",
    r"\forall": "∀", r"\exists": "∃", r"\sqrt": "√",
}


def _to_superscript(s: str) -> str:
    return "".join(_SUPER_MAP.get(ch, "^" + ch) for ch in s)


def _to_subscript(s: str) -> str:
    return "".join(_SUB_MAP.get(ch, "_" + ch) for ch in s)


def _convert_inline(expr: str) -> str:
    """Конвертируем содержимое одного $...$ или \\(...\\) блока."""
    s = expr

    # Команды — простые подстановки
    for cmd, rep in _COMMANDS.items():
        s = s.replace(cmd, rep)

    # Степени: x^{abc} и x^2
    s = re.sub(
        r"\^\{([^{}]+)\}",
        lambda m: _to_superscript(m.group(1)),
        s,
    )
    s = re.sub(
        r"\^([0-9a-zA-Z+\-])",
        lambda m: _to_superscript(m.group(1)),
        s,
    )

    # Индексы: x_{ij} и x_1
    s = re.sub(
        r"_\{([^{}]+)\}",
        lambda m: _to_subscript(m.group(1)),
        s,
    )
    s = re.sub(
        r"_([0-9a-zA-Z])",
        lambda m: _to_subscript(m.group(1)),
        s,
    )

    # Дроби: \frac{a}{b} → (a)/(b); простые числители/знаменатели оставляем без скобок
    def _frac_repl(m: re.Match) -> str:
        num = m.group(1).strip()
        den = m.group(2).strip()
        # Если и числитель, и знаменатель короткие — без скобок
        if len(num) <= 3 and len(den) <= 3 and num.isalnum() and den.isalnum():
            return f"{num}/{den}"
        return f"({num})/({den})"

    s = re.sub(r"\\frac\{([^{}]+)\}\{([^{}]+)\}", _frac_repl, s)

    # \sqrt{expr} → √(expr); однозначные — без скобок
    def _sqrt_repl(m: re.Match) -> str:
        inner = m.group(1).strip()
        if len(inner) <= 2:
            return f"√{inner}"
        return f"√({inner})"

    s = re.sub(r"√\{([^{}]+)\}", _sqrt_repl, s)

    # Пробелы: \, \; \: — стилевые в LaTeX, заменим на обычные
    s = re.sub(r"\\[,:; ]", " ", s)

    # Фигурные скобки, которые остались от \command{arg} — удаляем
    s = s.replace("{", "").replace("}", "")

    return s


def latex_to_unicode(text: str) -> str:
    """Найти LaTeX-блоки ($...$, $$...$$, \\(...\\)) и заменить их на unicode."""
    if not text or ("$" not in text and "\\(" not in text and "\\[" not in text):
        return text

    # $$...$$ (display) и $...$ (inline) — обрабатываем одним regex
    text = re.sub(
        r"\$\$([^$]+)\$\$",
        lambda m: _convert_inline(m.group(1)),
        text,
    )
    text = re.sub(
        r"\$([^$]+)\$",
        lambda m: _convert_inline(m.group(1)),
        text,
    )
    # \( ... \) и \[ ... \]
    text = re.sub(
        r"\\\(([^)]+)\\\)",
        lambda m: _convert_inline(m.group(1)),
        text,
    )
    text = re.sub(
        r"\\\[([^\]]+)\\\]",
        lambda m: _convert_inline(m.group(1)),
        text,
    )
    return text


def format_questions(questions: list[dict]) -> list[dict]:
    """Пройтись по списку вопросов и сконвертировать LaTeX в тексте и опциях."""
    result = []
    for q in questions:
        new_q = dict(q)
        if isinstance(new_q.get("question"), str):
            new_q["question"] = latex_to_unicode(new_q["question"])
        opts = new_q.get("options")
        if isinstance(opts, list):
            new_q["options"] = [
                latex_to_unicode(o) if isinstance(o, str) else o for o in opts
            ]
        if isinstance(new_q.get("explanation"), str):
            new_q["explanation"] = latex_to_unicode(new_q["explanation"])
        result.append(new_q)
    return result
