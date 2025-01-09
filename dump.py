import json
import traceback

def cvt(s):
    """Convert a value to a readable string representation.
    
    Args:
        s: The value to convert. Can be any type.
        
    Returns:
        str: The string representation of the value. If the value is already a string,
             it's returned as-is. For other types, attempts to convert to JSON with
             pretty-printing. Falls back to str() if JSON conversion fails.
    """
    if isinstance(s, str):
        return s
    try:
        return json.dumps(s, indent=4)
    except TypeError:
        return str(s)


def dump(*vals):
    """Print debug information about variables, including their names and values.
    
    This function is designed to be used as a debugging tool. When called with one or
    more values, it will:
    1. Capture the calling line of code using traceback
    2. Extract the variable names from the calling line
    3. Convert each value to a readable string format
    4. Print the variable names and their values in a readable format
    
    The output format adapts based on content:
    - Single-line output for simple values
    - Multi-line output for values containing newlines
    
    Example usage:
        x = 42
        y = {'a': 1, 'b': 2}
        dump(x, y)
        
    Would output something like:
        x, y: 42, {
            "a": 1,
            "b": 2
        }
    """
    # Get the call stack to find where dump() was called from
    stack = traceback.extract_stack()
    # Get the actual line of code that called dump()
    vars = stack[-2][3]

    # Extract just the variable names from the calling line
    # Remove the "dump(" prefix and ")" suffix
    vars = "(".join(vars.split("(")[1:])
    vars = ")".join(vars.split(")")[:-1])

    # Convert all values to readable strings
    vals = [cvt(v) for v in vals]
    
    # Check if any values contain newlines (complex structures)
    has_newline = sum(1 for v in vals if "\n" in v)
    
    # Format output based on content complexity
    if has_newline:
        print("%s:" % vars)
        print(", ".join(vals))
    else:
        print("%s:" % vars, ", ".join(vals))
