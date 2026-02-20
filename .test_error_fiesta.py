import importlib
import math

def ex_syntax_error():
    bad_code = "def broken(:\n    pass"
    exec(bad_code)

def ex_indentation_error():
    bad_code = "def f():\nprint('no indent')"
    exec(bad_code)

def ex_name_error():
    return undefined_variable

def ex_type_error():
    return 5 + "five"

def ex_value_error():
    return int("not-an-int")

def ex_index_error():
    a = [1, 2, 3]
    return a[10]

def ex_key_error():
    d = {"a": 1}
    return d["missing"]

def ex_zero_division_error():
    return 1 / 0

def ex_attribute_error():
    return (42).nope

def ex_module_not_found_error():
    importlib.import_module("this_module_does_not_exist_12345")

def ex_file_not_found_error():
    open("definitely_nonexistent_file_xyz.txt", "r")

def ex_os_error():
    raise OSError("simulated OSError")

def ex_recursion_error():
    def recurse(n=0):
        return recurse(n+1)
    recurse()

def ex_overflow_error():
    math.exp(10000)

def ex_memory_error():
    raise MemoryError("simulated MemoryError for testing")

def ex_assertion_error():
    assert False, "simulated assertion"

def ex_runtime_error():
    raise RuntimeError("simulated runtime error")

def ex_not_implemented_error():
    raise NotImplementedError("simulated not implemented")

def ex_unicode_decode_error():
    raise UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid start byte")

def ex_unicode_encode_error():
    raise UnicodeEncodeError("utf-8", "😊", 0, 1, "simulated encode error")

def ex_stop_iteration():
    it = iter([])
    next(it)

def ex_permission_error():
    raise PermissionError("simulated permission denied")

def ex_floating_point_error():
    raise FloatingPointError("simulated floating point error")

def ex_lookup_error():
    raise LookupError("simulated lookup error")

def ex_zero_length_slice_error():
    raise ValueError("simulated zero-length slice / value error")
