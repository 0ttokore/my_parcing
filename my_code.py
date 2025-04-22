import xml.etree.ElementTree as ET
import logging
from collections import defaultdict
from decimal import Decimal
from typing import List
import re
from instance2 import (
    open_lookup_file,
    find_filter,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def integer_essence(
    input_str: str, context: str = None, varmap: list = None
) -> Decimal:
    if context is None:
        return integer_essence(input_str, "0")
    elif varmap is None:
        return num_essence(parse_essence(input_str), context)
    else:
        return num_essence(
            prune_essence(prune_essence(input_str), context, varmap, 0), context
        )


def text_essence():
    pass


def num_essence(
    in_list: list, context: str, warning="recover"
) -> Decimal:  # evaluate syntax tree for a numeric target
    if in_list.get("kind") == "and":
        return (
            0
            if (
                num_essence(in_list[0], context) == 0
                or num_essence(in_list[1], context) == 0
            )
            else 1
        )
    elif in_list.get("kind") == "or":
        return (
            0
            if (
                num_essence(in_list[0], context) == 0
                or num_essence(in_list[1], context) == 0
            )
            else 1
        )
    if in_list.get("kind") == "xor":
        return (
            0
            if (num_essence(in_list[0], context) == num_essence(in_list[1], context))
            else 1
        )
    elif (
        in_list.get("kind") in ("ge", "le", "lt", "gt", "eq", "ne", "nm", "ma")
        and in_list[0].get("type") == "string"
        or in_list[1].get("type") == "string"
    ):
        left = text_essence(in_list[0], context)
        right = text_essence(in_list[1], context)
        if in_list.get("kind") == "nm":
            return 0 if str(right) in str(left) else 1
        elif in_list.get("kind") == "ma":
            return 1 if str(right) in str(left) else 0
        elif in_list.get("kind") == "eq":
            return 1 if compare(left, right) == 0 else 0
        elif in_list.get("kind") == "ne":
            return 0 if compare(left, right) == 0 else 1
        elif in_list.get("kind") == "lt":
            return 1 if compare(left, right) < 0 else 0
        elif in_list.get("kind") == "ge":
            return 0 if compare(left, right) < 0 else 1
        elif in_list.get("kind") == "gt":
            return 1 if compare(left, right) > 0 else 0
        elif in_list.get("kind") == "le":
            return 0 if compare(left, right) > 0 else 1
    elif in_list.get("kind") == "ge":
        return (
            0
            if num_essence(in_list[0], context) < num_essence(in_list[1], context)
            else 1
        )
    elif in_list.get("kind") == "le":
        return (
            0
            if num_essence(in_list[0], context) > num_essence(in_list[1], context)
            else 1
        )
    elif in_list.get("kind") == "gt":
        return (
            1
            if num_essence(in_list[0], context) > num_essence(in_list[1], context)
            else 0
        )
    elif in_list.get("kind") == "lt":
        return (
            1
            if num_essence(in_list[0], context) < num_essence(in_list[1], context)
            else 0
        )
    elif in_list.get("kind") == "eq":
        return (
            1
            if num_essence(in_list[0], context) == num_essence(in_list[1], context)
            else 0
        )
    elif in_list.get("kind") == "ne":
        return (
            0
            if num_essence(in_list[0], context) == num_essence(in_list[1], context)
            else 1
        )
    elif in_list.get("kind") == "add":
        return num_essence(in_list[0], context) + num_essence(in_list[1], context)
    elif in_list.get("kind") == "sub":
        return num_essence(in_list[0], context) - num_essence(in_list[1], context)
    elif in_list.get("kind") == "mul":
        return num_essence(in_list[0], context) * num_essence(in_list[1], context)
    elif in_list.get("kind") == "div":
        divisor = num_essence(in_list[1], context)
        if divisor == 0:
            raise ValueError("ERROR: Divide by 0!")
        return num_essence(in_list[0], context) // divisor
    elif in_list.get("kind") == "mod":
        class_var = num_essence(in_list[1], context)
        if class_var == 0:
            raise ValueError("ERROR: modulo 0!")
        return num_essence(in_list[0], context) % class_var
    elif in_list.get("kind") == "exp":
        b = num_essence(in_list[0], context)
        e = num_essence(in_list[1], context)
        if b == 1:
            return 1
        elif b == 0:
            return 0
        elif e < 1:
            return 1
        elif e == 1:
            return b
        elif False and b % 2 == 0 and e > 63:
            return power(2, 64)
        elif False and b != 2 and b % 2 == 0:
            h = power(b / 2, int(e))
            return int((h % power(2, 64 - e)) * power(2, e))
        elif b == 2:
            return Decimal(power2(int(e)))
        else:
            return Decimal(power(b, int(e)))
    elif in_list.get("kind") == "not":
        return 1 if num_essence(in_list[0], context) == 0 else 0
    elif in_list.get("kind") == "const" and in_list.get("type") in ("int", "bool"):
        if in_list.text.upper().startswith("0B"):
            return str2base(in_list.text[2:], 2)
        elif in_list.text.upper().startswith("0X"):
            return str2base(in_list.text[2:], 16)
        elif in_list.text.upper().startswith("0O"):
            return str2base(in_list.text[2:], 8)
        else:
            return in_list.text
    elif (
        in_list.get("kind") == "const"
        and in_list.get("type") == "string"
        and re.match(r"^\d+$", in_list.text)
    ):
        return Decimal(in_list.text)
    elif in_list.get("kind") == "const":
        if warning == "fatal":
            raise ValueError(f"ERROR: Non-numeric value {in_list}")
        else:
            print("Replaced by -1")
            return -1
    elif in_list.get("kind") == "var":
        get_parameter = ""  # дописать
    elif in_list.get("kind") == "func" and len(in_list) != 3:
        raise ValueError(
            f"ERROR: Wrong number of parameters for function {in_list[0].text}"
        )
    elif in_list.get("kind") == "func" and in_list[0].text == "min":
        paras = [int(num_essence(par, context)) for par in in_list.findall("./*")[1:]]
        return paras[0] if paras[0] < paras[1] else paras[1]
    elif in_list.get("kind") == "func" and in_list[0].text == "max":
        paras = [int(num_essence(par, context)) for par in in_list.findall("./*")[1:]]
        return paras[0] if paras[0] > paras[1] else paras[1]
    elif in_list.get("kind") == "func" and in_list[0].text == "rshift":
        paras = [int(num_essence(par, context)) for par in in_list.findall("./*")[1:]]
        if paras[1] == 0:
            return paras[0]
        elif paras[1] < 0:
            return paras[0] * Decimal(power(2, int(-paras[1])))
        else:
            return paras[0] // Decimal(power(2, int(paras[1])))
    elif in_list.get("kind") == "func" and in_list[0].text == "lshift":
        paras = [int(num_essence(par, context)) for par in in_list.findall("./*")[1:]]
        if paras[1] == 0:
            return paras[0]
        elif paras[1] < 0:
            return paras[0] // Decimal(power(2, int(-paras[1])))
        else:
            return paras[0] * Decimal(power(2, int(paras[1])))
    elif in_list.get("kind") == "func" and in_list[0].text == "log":
        paras = [int(num_essence(par, context)) for par in in_list.findall("./*")[1:]]
        return log(paras[0], paras[1])
    elif in_list.get("kind") == "func" and in_list[0].text == "pos":
        index = Decimal(num_essence(in_list[2], context))
        paras = []
        if in_list[1].get("kind") == "func" and in_list[1][0].text == "list":  # ???
            for i, p in enumerate(in_list[1]):
                if i - 2 == index:  # ???
                    paras.append(p)
        elif in_list[1].get("kind") == "var":
            get_parameter = ""  # дописать
            if len(get_parameter) > 0 and len(get_parameter[0]) > 0:
                tree = parse_essence(get_parameter[0])
                if tree.get("kind") == "func" and tree[0].text == "list":
                    for i, tr in enumerate(tree):
                        if i - 2 == index:  # ???
                            paras.append(tr)
                else:
                    raise ValueError(
                        f'ERROR: Invalid first parameter in "pos({in_list[1].text})!"'
                    )
            else:
                if warning == "fatal":
                    raise ValueError(f"ERROR: Unresolved parameter {in_list.text}!")
                else:
                    print("Replaced by -1")
                    return -1
        else:
            raise ValueError('ERROR: Invalid first parameter in "pos()"!')
        if len(paras) > 0:
            return num_essence(paras[0], context)
        else:
            if warning == "fatal":
                raise ValueError(
                    f"ERROR: pos({in_list[1]}, {index}) index out of bounds!"
                )
            else:
                print("pos(...) replaced by -1")
                return -1
    else:
        if warning == "fatal":
            raise ValueError(f"ERROR: Non-numeric value !")
        else:
            print("Replaced by -1<")
            return -1


def log(number: Decimal, base: Decimal) -> Decimal:
    return logh(number, base, base * base, 0)


def logh(number: Decimal, base: Decimal, base2: Decimal, n: Decimal) -> Decimal:
    if number < base:
        return n
    elif number < base2:
        return n + 1
    elif number == base2:
        return n + 2
    else:
        return logh(number // base2, base, base2, n + 2)


def power(base: float, exp: int) -> float:
    if exp < 0:
        return powerh(1.0 / base, -exp)
    elif exp == 0:
        return 1.0
    else:
        return powerh(base, exp)


def powerh(base: float, exp: int) -> float:
    if exp == 1:
        return base
    elif exp == 2:
        return base * base
    elif exp == 3:
        return base * base * base
    else:
        h = powerh(base, exp // 2)
        return h * h if exp % 2 == 0 else base * h * h


def power2(exp: int) -> Decimal:
    if exp < 0:
        return Decimal(1.0 / power2(-exp))
    elif exp == 0:
        return 1
    elif exp == 1:
        return 2
    elif exp == 2:
        return 4
    elif exp == 3:
        return 8
    else:
        h = Decimal(power2(exp // 2))
        return h * h if exp % 2 == 0 else 2 * h * h


def str2base(input_str: str, base: int) -> Decimal:
    input_str = re.sub(r"^0[xyzob]", "", input_str, flags=re.IGNORECASE).upper()
    symbols = "0123456789ABCDEF"
    if len(input_str) == 0 or not all(c in symbols for c in input_str):
        raise ValueError("ERROR: the string contains invalid characters or is empty!")
    value = Decimal(0)
    for i, char in enumerate(reversed(input_str)):
        digit_value = symbols.index(char)
        value += Decimal(digit_value) * (Decimal(base) ** i)
    return value


def compare(left, right):
    if left == right:
        return 0
    return -1 if left < right else 1


def prune_essence():
    pass


def parse_essence():
    pass


def main():
    try:
        Iproot = "C:/python_projects/work/my_parcing/parsed_context_spirit.xml"
        filter = None
        filter_params = [
            "audience",
            "platform",
            "product",
            "package",
            "props",
            "otherprops",
        ]
        input_file = "./instance_sheet_TC49x.xml"
        filter = find_filter(
            input_file="C:/python_projects/work/my_parcing/instance_sheet_TC49x.xml",
            filter=filter,
        )
        data = open_lookup_file(Iproot)
        drive = "file:"
        disc = ""

        root = ET.Element("Essence")
        op = ET.SubElement(
            root, "op", attrib={"kind": "func", "type": "string", "prio": "8"}
        )
        ET.SubElement(
            op, "op", attrib={"kind": "const", "type": "string", "prio": "8"}
        ).text = "'eng'"
        ET.SubElement(
            op, "op", attrib={"kind": "const", "type": "string", "prio": "8"}
        ).text = "'ru'"

        ET.dump(root[0])

        ch = root.findall("./*")
        ET.dump(ch[0])

    except Exception as e:
        logger.error(f"Conversion failed: {e}")
        raise


if __name__ == "__main__":
    main()
