from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
import json
from dotenv import load_dotenv

# =========================================================
# ENVIRONMENT
# =========================================================

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# OpenRouter model
MODEL_NAME = "meta-llama/llama-3.1-8b-instruct"

if not OPENROUTER_API_KEY:
    raise ValueError("Missing OPENROUTER_API_KEY in .env")


# =========================================================
# FLASK APP
# =========================================================

app = Flask(__name__)
CORS(app)


# =========================================================
# HOME / HEALTH
# =========================================================

@app.route("/", methods=["GET"])
def home():
    return "Flask AI Service is Running"


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "service": "AI Code Reviewer",
        "model": MODEL_NAME
    })


# =========================================================
# LANGUAGE NORMALIZATION
# =========================================================

def normalize_language(language):
    if not language:
        return "javascript"

    language = str(language).strip().lower()

    aliases = {
        "js": "javascript",
        "jsx": "javascript",
        "ts": "typescript",
        "tsx": "typescript",
        "py": "python",
        "python3": "python",
        "java": "java",
        "c++": "cpp",
        "cc": "cpp",
        "cxx": "cpp",
        "c": "c"
    }

    return aliases.get(language, language)


# =========================================================
# LANGUAGE-SPECIFIC RULES
# =========================================================

def get_language_rules(language):

    language = normalize_language(language)

    rules = {

        "javascript": """
- Use JavaScript syntax only.
- Prefer const when a variable is not reassigned.
- Use let when reassignment is required.
- Do not recommend Java syntax.
- Do not recommend Python syntax.
- Do not recommend C/C++ syntax.
- Avoid var unless there is a specific compatibility requirement.
- Consider JavaScript-specific issues such as undefined variables,
  type coercion, async handling, promises, security, and array methods.
""",

        "typescript": """
- Use TypeScript syntax only.
- Prefer const when a variable is not reassigned.
- Use let when reassignment is required.
- Use appropriate TypeScript types.
- Consider interfaces, type safety, null handling, and strict typing.
- Do not recommend Java, Python, or C/C++ syntax.
""",

        "python": """
- Use Python syntax only.
- Prefer Pythonic and readable solutions.
- Use enumerate(), zip(), list comprehensions, sum(), etc. only when
  they improve readability.
- Consider exceptions, mutable defaults, None handling, resource
  management, security, and inefficient loops where applicable.
- Do not recommend JavaScript keywords such as let, const, or var.
- Do not recommend Java syntax.
""",

        "java": """
- Use Java syntax only.
- Do NOT use JavaScript keywords such as let or const.
- Do NOT claim that normal Java declarations such as int, double,
  String, boolean, or final are JavaScript-style variables.
- Do NOT recommend replacing Java declarations with let or const.
- Consider array bounds, integer division, null handling, exception
  handling, resource management, type safety, collections,
  access modifiers, and object-oriented design.
- Use valid Java syntax in improved_code.
""",

        "cpp": """
- Use C++ syntax only.
- Consider RAII, const correctness, references, smart pointers,
  STL usage, memory safety, and exception safety.
- Do not recommend Java, Python, or JavaScript syntax.
""",

        "c": """
- Use C syntax only.
- Consider pointers, memory safety, array bounds, resource management,
  buffer safety, return-value checking, and error handling.
- Do not recommend Java, Python, or JavaScript syntax.
"""
    }

    return rules.get(
        language,
        f"""
- Use ONLY valid {language} syntax.
- Apply ONLY best practices that belong to {language}.
- Never recommend syntax from another programming language.
"""
    )


# =========================================================
# SCHEMA VALIDATION
# =========================================================

def validate_schema(data):

    if not isinstance(data, dict):
        return False

    if "summary" not in data:
        return False

    if not isinstance(data["summary"], str):
        return False

    if "issues" not in data:
        return False

    if not isinstance(data["issues"], list):
        return False

    if "improved_code" not in data:
        return False

    if not isinstance(data["improved_code"], str):
        return False

    for issue in data["issues"]:

        if not isinstance(issue, dict):
            return False

        required_fields = [
            "line",
            "issue",
            "severity",
            "suggestion"
        ]

        if not all(field in issue for field in required_fields):
            return False

    return True


# =========================================================
# SAFE JSON PARSER
# =========================================================

def safe_json_parse(text):

    if not text:
        return None

    if not isinstance(text, str):
        return None

    text = text.strip()

    # Remove Markdown code fences
    if text.startswith("```json"):
        text = text[7:].strip()

    elif text.startswith("```"):
        text = text[3:].strip()

    if text.endswith("```"):
        text = text[:-3].strip()

    # Try direct parsing
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try extracting JSON object
    start = text.find("{")

    if start == -1:
        return None

    try:
        decoder = json.JSONDecoder()
        parsed, _ = decoder.raw_decode(text[start:])
        return parsed

    except json.JSONDecodeError:
        return None


# =========================================================
# STATIC CHECKS
# =========================================================

def static_checks(code, language):

    issues = []

    language = normalize_language(language)
    lines = code.split("\n")

    for i, line in enumerate(lines, start=1):

        stripped = line.strip()

        # -------------------------------------------------
        # JAVASCRIPT / TYPESCRIPT
        # -------------------------------------------------

        if language in ["javascript", "typescript"]:

            if "eval(" in line:

                issues.append({
                    "line": i,
                    "issue": "Use of eval() can create a security risk",
                    "severity": "high",
                    "suggestion": (
                        "Avoid eval() and use explicit logic "
                        "or safer parsing."
                    ),
                    "source": "static"
                })

            if language == "javascript" and "var " in line:

                issues.append({
                    "line": i,
                    "issue": "Use of var instead of let or const",
                    "severity": "low",
                    "suggestion": (
                        "Use const when the variable is not reassigned "
                        "or let when reassignment is required."
                    ),
                    "source": "static"
                })

        # -------------------------------------------------
        # PYTHON
        # -------------------------------------------------

        elif language == "python":

            if "eval(" in line:

                issues.append({
                    "line": i,
                    "issue": "Use of eval() can execute arbitrary code",
                    "severity": "high",
                    "suggestion": (
                        "Avoid eval() and use safer parsing "
                        "or explicit logic."
                    ),
                    "source": "static"
                })

            if "exec(" in line:

                issues.append({
                    "line": i,
                    "issue": "Use of exec() can execute arbitrary code",
                    "severity": "high",
                    "suggestion": (
                        "Avoid exec() unless absolutely necessary "
                        "and tightly controlled."
                    ),
                    "source": "static"
                })

        # -------------------------------------------------
        # JAVA
        # -------------------------------------------------

        elif language == "java":

            if "Runtime.getRuntime().exec(" in line:

                issues.append({
                    "line": i,
                    "issue": "External command execution detected",
                    "severity": "high",
                    "suggestion": (
                        "Avoid executing untrusted input and validate "
                        "commands carefully before execution."
                    ),
                    "source": "static"
                })

        # -------------------------------------------------
        # C / C++
        # -------------------------------------------------

        elif language in ["c", "cpp"]:

            if "gets(" in line:

                issues.append({
                    "line": i,
                    "issue": "Unsafe gets() function detected",
                    "severity": "high",
                    "suggestion": (
                        "Use a bounded input function such as fgets() "
                        "instead of gets()."
                    ),
                    "source": "static"
                })


    return issues


# =========================================================
# DEDUPLICATE ISSUES
# =========================================================

def deduplicate_issues(issues):

    seen = set()
    unique = []

    for issue in issues:

        issue_text = str(
            issue.get("issue", "")
        ).strip().lower()

        line_number = issue.get("line")

        key = (
            issue_text,
            line_number
        )

        if key not in seen:

            seen.add(key)
            unique.append(issue)

    return unique


# =========================================================
# NORMALIZE ISSUES
# =========================================================

def normalize_issues(issues):

    normalized = []

    if not isinstance(issues, list):
        return normalized

    for issue in issues:

        if not isinstance(issue, dict):
            continue

        try:
            line_number = int(
                issue.get("line", 0)
            )
        except (TypeError, ValueError):
            line_number = 0

        issue_text = str(
            issue.get(
                "issue",
                "Issue detected"
            )
        ).strip()

        severity = str(
            issue.get(
                "severity",
                "medium"
            )
        ).strip().lower()

        if severity not in [
            "low",
            "medium",
            "high"
        ]:
            severity = "medium"

        suggestion = str(
            issue.get(
                "suggestion",
                "Review this code."
            )
        ).strip()

        normalized.append({
            "line": line_number,
            "issue": issue_text,
            "severity": severity,
            "suggestion": suggestion,
            "source": issue.get(
                "source",
                "ai"
            )
        })

    return normalized


# =========================================================
# OPENROUTER AI CALL
# =========================================================

def call_ai(prompt, temperature=0.0):

    try:

        url = (
            "https://openrouter.ai/api/v1/"
            "chat/completions"
        )

        headers = {
            "Authorization": (
                f"Bearer {OPENROUTER_API_KEY}"
            ),
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:5173",
            "X-Title": "AI Code Reviewer"
        }

        payload = {
            "model": MODEL_NAME,

            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a professional senior software "
                        "engineer and code reviewer. "
                        "Return ONLY valid JSON. "
                        "Never return Markdown outside the JSON."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],

            "temperature": temperature,

            "response_format": {
                "type": "json_object"
            },

            "max_tokens": 3000
        }

        print("\n----------------------------------------")
        print("Sending request to OpenRouter")
        print("Model:", MODEL_NAME)
        print("----------------------------------------")

        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=40
        )

        print(
            "OpenRouter Status:",
            response.status_code
        )

        # -------------------------------------------------
        # API ERROR
        # -------------------------------------------------

        if response.status_code != 200:

            print(
                "❌ OpenRouter API Error:"
            )
            print(response.text)

            return None

        # -------------------------------------------------
        # RESPONSE JSON
        # -------------------------------------------------

        try:

            data = response.json()

        except ValueError:

            print(
                "❌ OpenRouter returned invalid JSON"
            )

            print(
                "Raw Response:",
                response.text
            )

            return None

        # -------------------------------------------------
        # CHECK CHOICES
        # -------------------------------------------------

        choices = data.get(
            "choices",
            []
        )

        if not choices:

            print(
                "❌ No choices returned"
            )

            print(
                "Full response:",
                data
            )

            return None

        # -------------------------------------------------
        # GET MESSAGE
        # -------------------------------------------------

        message = choices[0].get(
            "message",
            {}
        )

        if not isinstance(
            message,
            dict
        ):

            print(
                "❌ Invalid message structure"
            )

            print(
                "Message:",
                message
            )

            return None

        content = message.get(
            "content"
        )

        # -------------------------------------------------
        # HANDLE LIST CONTENT
        # -------------------------------------------------

        if isinstance(
            content,
            list
        ):

            text_parts = []

            for item in content:

                if isinstance(
                    item,
                    dict
                ):

                    if item.get(
                        "type"
                    ) == "text":

                        text_parts.append(
                            str(
                                item.get(
                                    "text",
                                    ""
                                )
                            )
                        )

            content = "".join(
                text_parts
            )

        # -------------------------------------------------
        # EMPTY CONTENT
        # -------------------------------------------------

        if not content:

            print(
                "❌ AI returned empty content"
            )

            print(
                "Message:",
                message
            )

            return None

        if not isinstance(
            content,
            str
        ):

            print(
                "❌ AI content is not a string"
            )

            print(
                "Content:",
                content
            )

            return None

        print("\nAI Raw Response:")
        print(content)
        print("----------------------------------------")

        # -------------------------------------------------
        # PARSE GENERATED JSON
        # -------------------------------------------------

        parsed = safe_json_parse(
            content
        )

        if parsed is None:

            print(
                "❌ AI response could not be parsed as JSON"
            )

            return None

        print(
            "✅ AI JSON parsed successfully"
        )

        return parsed

    except requests.exceptions.Timeout:

        print(
            "❌ OpenRouter request timed out"
        )

        return None

    except requests.exceptions.RequestException as e:

        print(
            "❌ OpenRouter request error:",
            str(e)
        )

        return None

    except Exception as e:

        print(
            "❌ Unexpected AI error:",
            str(e)
        )

        return None


# =========================================================
# BUILD REVIEW PROMPT
# =========================================================

def build_review_prompt(
    code_content,
    language,
    static_issues=None
):

    language = normalize_language(
        language
    )

    language_rules = get_language_rules(
        language
    )

    static_context = ""

    if static_issues:

        static_context = """

STATIC ANALYSIS HAS ALSO DETECTED THESE ITEMS:

"""

        for issue in static_issues:

            static_context += (
                f"- Line {issue.get('line')}: "
                f"{issue.get('issue')}\n"
            )

        static_context += """

Consider these findings, verify them against the code,
and include them in the final analysis when they are
actually applicable.

"""

    prompt = f"""
You are a senior software engineer performing a
professional code review.

PROGRAMMING LANGUAGE:
{language}

====================================================
LANGUAGE-SPECIFIC RULES
====================================================

{language_rules}

====================================================
IMPORTANT
====================================================

You MUST analyze the code using ONLY the rules,
syntax, conventions, and best practices of {language}.

NEVER transfer rules from another programming language.

For example:

- JavaScript uses let and const.
- Java uses int, String, boolean, double, final, etc.
- Python does NOT use let, const, or var.
- Java does NOT use let or const.
- C/C++ do NOT use Python or JavaScript syntax.

Do not report an issue merely because a different
programming language would use a different syntax.

Only report genuine issues that are actually present
in the supplied code.

{static_context}

====================================================
OUTPUT FORMAT
====================================================

Return ONLY valid JSON.

Use exactly this structure:

{{
  "summary": "2-3 sentence explanation of the code quality, important issues, and possible improvements.",
  "issues": [
    {{
      "line": 1,
      "issue": "Description of the actual issue",
      "severity": "low",
      "suggestion": "Specific actionable fix"
    }}
  ],
  "improved_code": "Full corrected version of the code"
}}

====================================================
STRICT RULES
====================================================

1. Analyze ONLY the supplied code.

2. Do NOT invent bugs.

3. Do NOT assume code that was not provided.

4. Do NOT report an issue unless there is evidence
   in the supplied code.

5. Every issue MUST contain:
   - line
   - issue
   - severity
   - suggestion

6. severity MUST be exactly:
   - low
   - medium
   - high

7. line must identify the approximate line where
   the problem occurs.

8. Distinguish between:
   - correctness bugs
   - security vulnerabilities
   - performance issues
   - maintainability issues
   - style suggestions

9. Do not present an optional style preference as
   a correctness bug.

10. Never apply JavaScript rules to Java.

11. Never apply JavaScript rules to Python.

12. Never apply Python rules to Java.

13. Never apply Java rules to JavaScript.

14. improved_code MUST remain in {language}.

15. improved_code MUST NOT contain syntax from another
    programming language.

16. improved_code MUST be the complete code, not only
    the changed section.

17. Fix all genuine problems found in the supplied code.

18. Preserve the intended functionality.

19. Do not make unnecessary architectural changes.

20. If the original code is already correct, do not
    invent errors.

21. If the code is correct but can be improved,
    optional improvements may be reported as LOW.

22. Make improved_code consistent with the issues
    reported.

23. If you report a problem and the improved_code fixes
    it, the fix MUST actually be present.

24. Do not return Markdown code fences inside
    improved_code.

25. Return valid JSON only.

====================================================
CODE TO REVIEW
====================================================

{code_content}
"""

    return prompt


# =========================================================
# REVIEW ENDPOINT
# =========================================================

@app.route(
    "/review",
    methods=["POST"]
)
def review_code():

    try:

        # -------------------------------------------------
        # GET REQUEST DATA
        # -------------------------------------------------

        data = request.get_json(
            silent=True
        )

        if not data:

            return jsonify({
                "error": "Invalid JSON request"
            }), 400

        if "code" not in data:

            return jsonify({
                "error": "Missing code input"
            }), 400

        code_content = data.get(
            "code",
            ""
        )

        language = normalize_language(
            data.get(
                "language",
                "javascript"
            )
        )

        # -------------------------------------------------
        # VALIDATE CODE
        # -------------------------------------------------

        if not isinstance(
            code_content,
            str
        ):

            return jsonify({
                "error": "Code must be a string"
            }), 400

        if not code_content.strip():

            return jsonify({
                "error": "Code cannot be empty"
            }), 400

        print("\n========================================")
        print("NEW CODE REVIEW")
        print("Language:", language)
        print("Code length:", len(code_content))
        print("========================================")

        # -------------------------------------------------
        # STATIC ANALYSIS FIRST
        # -------------------------------------------------

        static_issues = static_checks(
            code_content,
            language
        )

        # -------------------------------------------------
        # BUILD PROMPT
        # -------------------------------------------------

        prompt = build_review_prompt(
            code_content,
            language,
            static_issues
        )

        # -------------------------------------------------
        # FIRST AI CALL
        # -------------------------------------------------

        parsed_output = call_ai(
            prompt,
            temperature=0.0
        )

        # -------------------------------------------------
        # AI FAILED
        # -------------------------------------------------

        if not parsed_output:

            raise ValueError(
                "OpenRouter did not return a valid response"
            )

        # -------------------------------------------------
        # SCHEMA VALIDATION
        # -------------------------------------------------

        if not validate_schema(
            parsed_output
        ):

            print(
                "❌ AI response failed schema validation"
            )

            print(
                "AI Output:",
                parsed_output
            )

            raise ValueError(
                "Invalid AI response structure"
            )

        # -------------------------------------------------
        # NORMALIZE AI ISSUES
        # -------------------------------------------------

        ai_issues = normalize_issues(
            parsed_output.get(
                "issues",
                []
            )
        )

        for issue in ai_issues:

            issue["source"] = "ai"

        # -------------------------------------------------
        # COMBINE AI + STATIC ISSUES
        # -------------------------------------------------

        all_issues = (
            ai_issues +
            static_issues
        )

        # -------------------------------------------------
        # DEDUPLICATE
        # -------------------------------------------------

        all_issues = deduplicate_issues(
            all_issues
        )

        # -------------------------------------------------
        # SORT ISSUES BY LINE
        # -------------------------------------------------

        all_issues.sort(
            key=lambda x: (
                x.get("line", 0),
                x.get("severity", "")
            )
        )

        # -------------------------------------------------
        # SUMMARY
        # -------------------------------------------------

        summary = str(
            parsed_output.get(
                "summary",
                ""
            )
        ).strip()

        if len(
            summary.split()
        ) < 8:

            summary = (
                "The code was analyzed for correctness, "
                "security, maintainability, performance, "
                "and language-specific best practices. "
                "Specific improvements are included in "
                "the corrected code where applicable."
            )

        # -------------------------------------------------
        # IMPROVED CODE
        # -------------------------------------------------

        improved_code = parsed_output.get(
            "improved_code",
            ""
        )

        if not isinstance(
            improved_code,
            str
        ):

            improved_code = code_content

        improved_code = improved_code.strip()

        if not improved_code:

            improved_code = code_content

        # -------------------------------------------------
        # RETRY IF IMPROVED CODE IS IDENTICAL
        # -------------------------------------------------

        if (
            improved_code ==
            code_content.strip()
        ):

            print(
                "⚠️ Improved code is identical."
            )

            retry_prompt = prompt + """

IMPORTANT:

The improved_code must fix every genuine issue
identified in the review.

Return the COMPLETE corrected code.

The code must remain valid {language} syntax.

Do not change the programming language.
""".format(
                language=language
            )

            retry_output = call_ai(
                retry_prompt,
                temperature=0.2
            )

            if (
                retry_output
                and validate_schema(
                    retry_output
                )
            ):

                retry_code = retry_output.get(
                    "improved_code",
                    ""
                )

                if (
                    isinstance(
                        retry_code,
                        str
                    )
                    and
                    retry_code.strip()
                    and
                    retry_code.strip()
                    != code_content.strip()
                ):

                    improved_code = (
                        retry_code.strip()
                    )

        # -------------------------------------------------
        # FINAL RESULT
        # -------------------------------------------------

        result = {
            "summary": summary,
            "issues": all_issues,
            "issue_count": len(all_issues),
            "improved_code": improved_code
        }

        print("\n========================================")
        print("FINAL REVIEW")
        print("Issue count:", len(all_issues))
        print("========================================")

        return jsonify(result), 200

    except Exception as e:

        print("\n========================================")
        print("❌ AI REVIEW ERROR")
        print(str(e))
        print("========================================")

        return jsonify({
            "summary": "AI could not generate the full analysis.",
            "issues": [],
            "issue_count": 0,
            "improved_code": "",
            "error": str(e)
        }), 500


# =========================================================
# START SERVER
# =========================================================

if __name__ == "__main__":

    print("========================================")
    print("AI CODE REVIEWER SERVICE")
    print("========================================")
    print("Model:", MODEL_NAME)
    print("Port: 8000")
    print("========================================")

    app.run(
        host="127.0.0.1",
        port=8000,
        debug=True
    )