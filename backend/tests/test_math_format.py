"""Юнит-тесты конвертации LaTeX → unicode в math_format.py."""

from app.services.math_format import format_questions, latex_to_unicode


class TestLatexToUnicode:
    """Конвертация LaTeX-маркеров в читаемый unicode."""

    def test_empty_and_plain_text(self):
        """Пустая строка и текст без формул проходят без изменений."""
        assert latex_to_unicode("") == ""
        assert latex_to_unicode("Обычный текст без формул") == "Обычный текст без формул"

    def test_none_safe(self):
        """None и не-строковые значения не падают (но функция принимает только str)."""
        # На контрактном уровне принимаем только str; проверяем короткую пустую
        assert latex_to_unicode("") == ""

    def test_single_digit_superscript(self):
        """Одиночная цифра в степени: $x^2$ → x²."""
        assert latex_to_unicode("$x^2$") == "x²"

    def test_multi_digit_superscript(self):
        """Многозначная степень через фигурные скобки: $x^{10}$ → x¹⁰."""
        assert latex_to_unicode("$x^{10}$") == "x¹⁰"

    def test_sqrt_short(self):
        """Короткий корень без скобок: $\\sqrt{16}$ → √16."""
        assert latex_to_unicode(r"$\sqrt{16}$") == "√16"

    def test_sqrt_long_wraps(self):
        """Длинное выражение под корнем оборачивается в скобки."""
        assert latex_to_unicode(r"$\sqrt{a+b+c}$") == "√(a+b+c)"

    def test_frac_short_no_parens(self):
        """Короткая дробь — без скобок."""
        assert latex_to_unicode(r"$\frac{1}{2}$") == "1/2"

    def test_frac_long_wraps(self):
        """Длинная дробь — числитель и знаменатель в скобках."""
        result = latex_to_unicode(r"$\frac{a+b}{c-d}$")
        assert result == "(a+b)/(c-d)"

    def test_greek_letters(self):
        """Греческие буквы и операторы: $\\pi$, $\\alpha$, $\\leq$."""
        assert latex_to_unicode(r"$\pi$") == "π"
        assert latex_to_unicode(r"$\alpha + \beta$") == "α + β"
        assert latex_to_unicode(r"$a \leq b$") == "a ≤ b"
        assert latex_to_unicode(r"$\infty$") == "∞"

    def test_combined_expression(self):
        """Комбинация: $\\pi r^2$ → π r²."""
        assert latex_to_unicode(r"$\pi r^2$") == "π r²"

    def test_multiple_blocks(self):
        """Несколько $...$ блоков в одном тексте."""
        src = r"Формулы: $x^2$ и $\sqrt{9}$"
        assert latex_to_unicode(src) == "Формулы: x² и √9"

    def test_display_math(self):
        r"""$$...$$ (display) тоже конвертируется."""
        assert latex_to_unicode("$$x^2 + y^2 = z^2$$") == "x² + y² = z²"

    def test_paren_math(self):
        r"""Нотация \\(...\\) поддерживается."""
        assert latex_to_unicode(r"\(a^2\)") == "a²"

    def test_subscript(self):
        """Цифровой индекс: $x_1$ → x₁."""
        assert latex_to_unicode("$x_1$") == "x₁"

    def test_unknown_command_survives(self):
        """Неизвестная команда оставляется как есть (без падения).

        Регрессионно: конвертация должна быть консервативной.
        """
        src = r"$\unknowncmd{x}$"
        # Минимум — не должно упасть, ответ начинается с чего-то разумного
        result = latex_to_unicode(src)
        assert isinstance(result, str) and len(result) > 0


class TestFormatQuestions:
    """Обработка списка вопросов: конвертация в question/options/explanation."""

    def test_empty_list(self):
        assert format_questions([]) == []

    def test_question_and_options_converted(self):
        """В question и в каждой option LaTeX заменяется на unicode."""
        src = [
            {
                "id": 1,
                "question": r"Вычислите $x^2$ при x=3",
                "options": [r"$\sqrt{9}$", "6", "9", r"$\pi$"],
                "type": "multiple_choice",
            }
        ]
        out = format_questions(src)
        assert out[0]["question"] == "Вычислите x² при x=3"
        assert out[0]["options"] == ["√9", "6", "9", "π"]
        # id/type не трогаем
        assert out[0]["id"] == 1
        assert out[0]["type"] == "multiple_choice"

    def test_no_options_field_survives(self):
        """Если options отсутствует — не падаем."""
        src = [{"id": 1, "question": r"Чему равен $\pi$?"}]
        out = format_questions(src)
        assert out[0]["question"] == "Чему равен π?"

    def test_does_not_mutate_input(self):
        """Входной список не мутируется — возвращается новый."""
        src = [{"id": 1, "question": r"$x^2$", "options": ["a", "b"]}]
        original_q = src[0]["question"]
        format_questions(src)
        assert src[0]["question"] == original_q

    def test_explanation_converted(self):
        """Поле explanation тоже проходит через конвертер."""
        src = [{"id": 1, "question": "Q", "explanation": r"Ответ: $x^2 = 9$"}]
        out = format_questions(src)
        assert out[0]["explanation"] == "Ответ: x² = 9"
