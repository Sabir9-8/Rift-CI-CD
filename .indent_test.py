import re

# Simulating the exact regex logic from agent.py
def check_file(content, label):
    lines = content.splitlines(keepends=True)
    errors = []
    for lineno, line in enumerate(lines, 1):
        stripped = line.rstrip('\n')
        if stripped and not stripped.strip().startswith('#'):
            prev_non_empty = ''
            for prev in reversed(lines[:lineno - 1]):
                if prev.strip():
                    prev_non_empty = prev.rstrip()
                    break
            is_flow_block = (
                prev_non_empty.endswith(':')
                and re.match(r'^\s*(?:if|elif|else|for|while|try|except|finally|with)\b',
                             prev_non_empty)
            )
            prev_indent = len(prev_non_empty) - len(prev_non_empty.lstrip())
            curr_indent = len(stripped) - len(stripped.lstrip())
            if is_flow_block and curr_indent <= prev_indent and stripped.strip():
                errors.append((lineno, repr(prev_non_empty[-40:]), repr(stripped.strip()[:40])))
    print(f"{label}: {len(errors)} errors")
    for e in errors:
        print(f"  line {e[0]}: prev={e[1]} curr={e[2]}")

# Test: valid code with for/except that should NOT fire
valid = """
def ex_recursion_error():
    def recurse(n=0):
        return recurse(n+1)
    recurse()

def run_all_tests():
    report = []
    for name, func in TESTS:
        try:
            func()
            report.append((name, "NO EXCEPTION"))
        except Exception as e:
            ex_type = type(e).__name__
            report.append((name, f"{ex_type}: {e!s}"))
    for name, result in report:
        print(f"{name} -> {result}")

if __name__ == "__main__":
    run_all_tests()
"""
check_file(valid, "valid test.py patterns")

# Test: real indentation error (test4.py style)
invalid = """
if x > 5:
print("Greater")
"""
check_file(invalid, "real IndentationError")
