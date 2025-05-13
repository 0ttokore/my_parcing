import xml.etree.ElementTree as ET
import re
import math
from typing import List


# blocks: 'dec', 'hex', 'bin', 'list' and 'pos' from to_tree_essence() / num_essence() / text_essence()
# are needed to be finished
# as well as prune_essence(), but they are not used yet


def to_tree_essence(input_str: str, consts: list) -> list:
    if re.match(r"^\s*\$curlyLeft\s*$", input_str):
        op = ET.Element("op", attrib={"kind": "const", "type": "string", "prio": "8"})
        op.text = "{"
        return op
    elif re.match(r"^\s*\$curlyRight\s*$", input_str):
        op = ET.Element("op", attrib={"kind": "const", "type": "string", "prio": "8"})
        op.text = "}"
        return op
    elif re.match(r"^\s*true\s*$", input_str, re.IGNORECASE):
        op = ET.Element("op", attrib={"kind": "const", "type": "bool", "prio": "8"})
        op.text = "1"
        return op
    elif re.match(r"^\s*false\s*$", input_str, re.IGNORECASE):
        op = ET.Element("op", attrib={"kind": "const", "type": "bool", "prio": "8"})
        op.text = "0"
        return op
    # prio 1: ( )
    elif ")" in input_str:
        sub_str = input_str.split(")", 1)[0]
        bracket = re.sub(r"^.*\(", "", sub_str)
        brack = len(sub_str) + 1
        lbrack = re.sub(r"\s*\([^\(]*$", "", sub_str)
        rbrack = input_str[brack:]

        if len(lbrack) == 0:
            subtree = to_tree_essence(bracket, consts)
            return to_tree_essence(f"$${len(consts) + 1}{rbrack}", consts + [subtree])
        elif lbrack.endswith("min"):
            op = ET.Element("op", attrib={"kind": "func", "type": "int", "prio": "8"})
            op_sub = ET.SubElement(
                op, "op", attrib={"kind": "const", "type": "string", "prio": "8"}
            )
            op_sub.text = "min"
            for token in bracket.split(","):
                elements = to_tree_essence(token, consts)
                op.append(elements)
            return to_tree_essence(
                f"{lbrack.replace('min', '')}$${len(consts) + 1}{rbrack}",
                consts + [op],
            )
        elif lbrack.endswith("max"):
            op = ET.Element("op", attrib={"kind": "func", "type": "int", "prio": "8"})
            op_sub = ET.SubElement(
                op, "op", attrib={"kind": "const", "type": "string", "prio": "8"}
            )
            op_sub.text = "max"
            for token in bracket.split(","):
                elements = to_tree_essence(token, consts)
                op.append(elements)
            return to_tree_essence(
                f"{lbrack.replace('max', '')}$${len(consts) + 1}{rbrack}",
                consts + [op],
            )
        elif lbrack.endswith("rshift"):
            op = ET.Element("op", attrib={"kind": "func", "type": "int", "prio": "8"})
            op_sub = ET.SubElement(
                op, "op", attrib={"kind": "const", "type": "string", "prio": "8"}
            )
            op_sub.text = "rshift"
            for token in bracket.split(","):
                elements = to_tree_essence(token, consts)
                op.append(elements)
            return to_tree_essence(
                f"{lbrack.replace('rshift', '')}$${len(consts) + 1}{rbrack}",
                consts + [op],
            )
        elif lbrack.endswith("lshift"):
            op = ET.Element("op", attrib={"kind": "func", "type": "int", "prio": "8"})
            op_sub = ET.SubElement(
                op, "op", attrib={"kind": "const", "type": "string", "prio": "8"}
            )
            op_sub.text = "lshift"
            for token in bracket.split(","):
                elements = to_tree_essence(token, consts)
                op.append(elements)
            return to_tree_essence(
                f"{lbrack.replace('lshift', '')}$${len(consts) + 1}{rbrack}",
                consts + [op],
            )
        elif lbrack.endswith("log"):
            op = ET.Element("op", attrib={"kind": "func", "type": "int", "prio": "8"})
            op_sub = ET.SubElement(
                op, "op", attrib={"kind": "const", "type": "string", "prio": "8"}
            )
            op_sub.text = "log"
            for token in bracket.split(","):
                elements = to_tree_essence(token, consts)
                op.append(elements)
            return to_tree_essence(
                f"{lbrack.replace('log', '')}$${len(consts) + 1}{rbrack}",
                consts + [op],
            )
        elif re.match(r"dec\d*$", lbrack):
            op = ET.Element(
                "op", attrib={"kind": "func", "type": "string", "prio": "8"}
            )
            op_sub = ET.SubElement(
                op, "op", attrib={"kind": "const", "type": "string", "prio": "8"}
            )
            op_sub.text = "dec"
            op_sub2 = ET.SubElement(
                op, "op", attrib={"kind": "const", "type": "int", "prio": "8"}
            )
            op_sub2.text = "1" if lbrack.endswith("dec") else lbrack.split("dec", 1)[-1]
            op.append(to_tree_essence(bracket, consts))
            return to_tree_essence(
                f"{lbrack.replace(r'dec\d*$', '')}$${len(consts) + 1}{rbrack}",
                consts + [op],
            )
        elif re.match(r"hex\d*$", lbrack):
            op = ET.Element(
                "op", attrib={"kind": "func", "type": "string", "prio": "8"}
            )
            op_sub = ET.SubElement(
                op, "op", attrib={"kind": "const", "type": "string", "prio": "8"}
            )
            op_sub.text = "hex"
            op_sub2 = ET.SubElement(
                op, "op", attrib={"kind": "const", "type": "int", "prio": "8"}
            )
            op_sub2.text = "1" if lbrack.endswith("hex") else lbrack.split("hex", 1)[-1]
            op.append(to_tree_essence(bracket, consts))
            return to_tree_essence(
                f"{lbrack.replace(r'hex\d*$', '')}$${len(consts) + 1}{rbrack}",
                consts + [op],
            )
        elif re.match(r"bin\d*$", lbrack):
            op = ET.Element(
                "op", attrib={"kind": "func", "type": "string", "prio": "8"}
            )
            op_sub = ET.SubElement(
                op, "op", attrib={"kind": "const", "type": "string", "prio": "8"}
            )
            op_sub.text = "bin"
            op_sub2 = ET.SubElement(
                op, "op", attrib={"kind": "const", "type": "int", "prio": "8"}
            )
            op_sub2.text = "1" if lbrack.endswith("bin") else lbrack.split("bin", 1)[-1]
            op.append(to_tree_essence(bracket, consts))
            return to_tree_essence(
                f"{lbrack.replace(r'bin\d*$', '')}$${len(consts) + 1}{rbrack}",
                consts + [op],
            )
        elif re.match(r"eng$", lbrack):
            op = ET.Element(
                "op", attrib={"kind": "func", "type": "string", "prio": "8"}
            )
            op_sub = ET.SubElement(
                op, "op", attrib={"kind": "const", "type": "string", "prio": "8"}
            )
            op_sub.text = "eng"
            op.append(to_tree_essence(bracket, consts))
            return to_tree_essence(
                f"{lbrack.replace('eng', '')}$${len(consts) + 1}{rbrack}",
                consts + [op],
            )
        elif lbrack.endswith("list"):
            op = ET.Element("op", attrib={"kind": "func", "type": "int", "prio": "8"})
            op_sub = ET.SubElement(
                op, "op", attrib={"kind": "const", "type": "string", "prio": "8"}
            )
            op_sub.text = "list"
            for token in bracket.split(","):
                elements = to_tree_essence(token, consts)
                for element in elements:
                    op.append(element)
            return to_tree_essence(
                f"{lbrack.replace('list$', '')}$${len(consts) + 1}{rbrack}",
                consts + [op],
            )
        elif lbrack.endswith("pos"):
            op = ET.Element("op", attrib={"kind": "func", "type": "int", "prio": "8"})
            op_sub = ET.SubElement(
                op, "op", attrib={"kind": "const", "type": "string", "prio": "8"}
            )
            op_sub.text = "pos"
            for token in bracket.split(","):
                elements = to_tree_essence(token, consts)
                for element in elements:
                    op.append(element)
            return to_tree_essence(
                f"{lbrack.replace('pos$', '')}$${len(consts) + 1}{rbrack}",
                consts + [op],
            )
        else:
            subtree = to_tree_essence(bracket, consts)
            return to_tree_essence(
                f"{lbrack}$${len(consts) + 1}{rbrack}", consts + [subtree]
            )

    elif "|" in input_str or "&" in input_str or "^" in input_str:
        orr = re.sub(r"^.*\|+", "", input_str)
        or_length = len(orr)
        andr = re.sub(r"^.*&+", "", input_str)
        and_length = len(andr)
        xorr = re.sub(r"^.*\^", "", input_str)
        xor_length = len(xorr)

        if and_length < or_length and and_length < xor_length:
            andl = re.sub(r"&+$", "", input_str[: len(input_str) - and_length])
            op = ET.Element("op", attrib={"kind": "and", "type": "bool", "prio": "1"})
            op.append(to_tree_essence(andl, consts))
            op.append(to_tree_essence(andr, consts))
            return op
        elif or_length < and_length and or_length < xor_length:
            orl = re.sub(r"\|+$", "", input_str[: len(input_str) - or_length])
            op = ET.Element("op", attrib={"kind": "or", "type": "bool", "prio": "1"})
            op.append(to_tree_essence(orl, consts))
            op.append(to_tree_essence(orr, consts))
            return op
        elif xor_length < and_length and xor_length < or_length:
            xorl = input_str[: len(input_str) - xor_length - 1]
            right = to_tree_essence(xorr, consts)
            left = to_tree_essence(xorl, consts)
            if ((right.get("type") == "bool" or right.get("type") == "int")
            and (left.get("type") == "bool" or left.get("type") == "int")):
                op = ET.Element(
                    "op", attrib={"kind": "xor", "type": "bool", "prio": "1"}
                )
                op.append(left)
                op.append(right)
                return op
            else:
                return to_tree_essence(f"{xorl}%%{xorr}", consts)
        else:
            raise ValueError(f'ERROR: Parsing error in "{input_str}"!')
    elif (
        "=" in input_str or "<" in input_str or ">" in input_str or "~" in input_str
    ):  # comparison operators
        ltr = re.sub(r"^.*<", "", input_str)
        lt = len(ltr)

        gtr = re.sub(r"^.*>", "", input_str)
        gt = len(gtr)

        eqr = re.sub(r"^.*==", "", input_str)
        eq = len(eqr)

        ler = re.sub(r"^.*<=", "", input_str)
        le = len(ler)

        ger = re.sub(r"^.*>=", "", input_str)
        ge = len(ger)

        ner = re.sub(r"^.*!=", "", input_str)
        ne = len(ner)

        mar = re.sub(r"^.*=~", "", input_str)
        ma = len(mar)

        nmr = re.sub(r"^.*!~", "", input_str)
        nm = len(nmr)

        if (
            ne < lt
            and ne < gt
            and ne < eq
            and ne < le
            and ne < ge
            and ne < ma
            and ne < nm
        ):
            nel = input_str[: len(input_str) - ne - 2]
            op = ET.Element("op", attrib={"kind": "ne", "type": "bool", "prio": "2"})
            op.append(to_tree_essence(nel, consts))
            op.append(to_tree_essence(ner, consts))
            return op
        elif (
            ge < lt
            and ge < gt
            and ge < eq
            and ge < le
            and ge < ne
            and ge < ma
            and ge < nm
        ):
            gel = input_str[: len(input_str) - ge - 2]
            op = ET.Element("op", attrib={"kind": "ge", "type": "bool", "prio": "2"})
            op.append(to_tree_essence(gel, consts))
            op.append(to_tree_essence(ger, consts))
            return op
        elif (
            le < lt
            and le < gt
            and le < eq
            and le < ne
            and le < ge
            and le < ma
            and le < nm
        ):
            lel = input_str[: len(input_str) - le - 2]
            op = ET.Element("op", attrib={"kind": "le", "type": "bool", "prio": "2"})
            op.append(to_tree_essence(lel, consts))
            op.append(to_tree_essence(ler, consts))
            return op
        elif (
            eq < lt
            and eq < gt
            and eq < ne
            and eq < le
            and eq < ge
            and eq < ma
            and eq < nm
        ):
            eql = input_str[: len(input_str) - eq - 2]
            op = ET.Element("op", attrib={"kind": "eq", "type": "bool", "prio": "2"})
            op.append(to_tree_essence(eql, consts))
            op.append(to_tree_essence(eqr, consts))
            return op
        elif (
            gt < lt
            and gt < eq
            and gt < ne
            and gt < le
            and gt < ge
            and gt < ma
            and gt < nm
        ):
            gtl = input_str[: len(input_str) - gt - 2]
            op = ET.Element("op", attrib={"kind": "gt", "type": "bool", "prio": "2"})
            op.append(to_tree_essence(gtl, consts))
            op.append(to_tree_essence(gtr, consts))
            return op
        elif (
            lt < ne
            and lt < gt
            and lt < eq
            and lt < le
            and lt < ge
            and lt < ma
            and lt < nm
        ):
            ltl = input_str[: len(input_str) - lt - 2]
            op = ET.Element("op", attrib={"kind": "lt", "type": "bool", "prio": "2"})
            op.append(to_tree_essence(ltl, consts))
            op.append(to_tree_essence(ltr, consts))
            return op
        elif (
            nm < lt
            and nm < gt
            and nm < eq
            and nm < le
            and nm < ge
            and nm < ma
            and nm < ne
        ):
            nml = input_str[: len(input_str) - nm - 2]
            op = ET.Element("op", attrib={"kind": "nm", "type": "bool", "prio": "2"})
            op.append(to_tree_essence(nml, consts))
            op.append(to_tree_essence(nmr, consts))
            return op
        elif (
            ma < lt
            and ma < gt
            and ma < eq
            and ma < le
            and ma < ge
            and ma < ne
            and ma < nm
        ):
            mal = input_str[: len(input_str) - ma - 2]
            op = ET.Element("op", attrib={"kind": "ma", "type": "bool", "prio": "2"})
            op.append(to_tree_essence(mal, consts))
            op.append(to_tree_essence(mar, consts))
            return op
        else:
            raise ValueError(f'ERROR: Parsing error in "{input_str}"!')

    elif "+" in input_str or "-" in input_str:  # add/sub: + -
        addr = re.sub(r"^.*\+", "", input_str)
        subr = re.sub(r"^.*-", "", input_str)
        add = len(addr)
        sub = len(subr)
        addl = input_str[: len(input_str) - add - 1]  # before last +
        subl = input_str[: len(input_str) - sub - 1]  # before last -

        if input_str.strip().startswith("+"):
            return to_tree_essence(input_str.split("+", 1)[1], consts)
        elif input_str.strip().startswith("-"):
            return to_tree_essence(f"§{input_str.split('-', 1)[1]}", consts)
        elif add < sub and addl.endswith("-"):
            left = to_tree_essence(subl, consts)
            right = to_tree_essence(addr, consts)
            op = ET.Element("op", attrib={"kind": "sub", "prio": "3"})
            if left.get("type") == "int" and right.get("type") == "int":
                op.set("type", "int")
            op.append(left)
            op.append(right)
            return op
        elif add < sub:
            left = to_tree_essence(re.sub(r"\+\s*$", "", addl), consts)
            right = to_tree_essence(addr, consts)
            # left and right elements dont have inner elements, so we'll call 'em themselves
            if left.get("kind") == "cat" or right.get("kind") == "cat":
                op = ET.Element("op", attrib={"kind": "cat", "prio": "3"})
                op.append(left)
                op.append(right)
                return op
            elif (left.get("type") == "string" and left.text != "#") or (
                right.get("type") == "string" and right.text != "#"
            ):
                op = ET.Element("op", attrib={"kind": "cat", "type": "string", "prio": "3"})
                op.append(left)
                op.append(right)
                return op
            elif left.get("kind") == "const" and len(left.text) == 0:
                return right
            elif right.get("kind") == "const" and len(right.text) == 0:
                return left
            else:
                op = ET.Element("op", attrib={"kind": "add", "prio": "3"})
                if left.get("type") == "int" and right.get("type") == "int":
                    op.set("type", "int")
                op.append(left)
                op.append(right)
                return op
        elif sub < add and subl.strip().endswith("+"):
            op = ET.Element("op", attrib={"kind": "sub", "type": "int", "prio": "3"})
            op.append(to_tree_essence(addl, consts))
            op.append(to_tree_essence(subr, consts))
            return op
        elif sub < add and subl.strip().endswith("-"):
            op = ET.Element("op", attrib={"kind": "add", "type": "int", "prio": "3"})
            op.append(to_tree_essence(re.sub(r"-\s*$"), "", subl), consts)
            op.append(to_tree_essence(subr, consts))
            return op
        elif sub < add and re.match(r"(\*|\||%)\s*$", subl):
            return to_tree_essence(f"{subl}§{subr}", consts)
        elif sub < add:
            op = ET.Element("op", attrib={"kind": "sub", "type": "int", "prio": "3"})
            op.append(to_tree_essence(subl, consts))
            op.append(to_tree_essence(subr, consts))
            return op
        else:
            raise ValueError(f'ERROR: Parsing error in "{input_str}"!')
    elif "*" in input_str or "/" in input_str:  # mul/div: * /
        mulr = re.sub(r"^.*\*", "", input_str)
        divr = re.sub(r"^.*/", "", input_str)
        mul = len(mulr)
        div = len(divr)

        if mul < div:
            mull = input_str[: len(input_str) - mul - 1]
            op = ET.Element("op", attrib={"kind": "mul", "type": "int", "prio": "4"})
            op.append(to_tree_essence(mull, consts))
            op.append(to_tree_essence(mulr, consts))
            return op
        elif div < mul:
            divl = input_str[: len(input_str) - div - 1]
            op = ET.Element("op", attrib={"kind": "div", "type": "int", "prio": "4"})
            op.append(to_tree_essence(divl, consts))
            op.append(to_tree_essence(divr, consts))
            return op
        else:
            raise ValueError(f'ERROR: Parsing error in "{input_str}"!')
    elif "%" in input_str:  # mod: % %% (was ^)
        # First check for %% (exponentiation)
        if "%%" in input_str:
            expr = re.sub("^.*%%", "", input_str)
            expl = input_str[: len(input_str) - len(expr) - 2]  # before last %%
            op = ET.Element("op", attrib={"kind": "exp", "type": "int", "prio": "5"})
            op.append(to_tree_essence(expl, consts))
            op.append(to_tree_essence(expr, consts))
            return op
        # Then check for % (modulo)
        elif "%" in input_str:
            modr = re.sub("^.*%", "", input_str)
            modl = input_str[: len(input_str) - len(modr) - 1]  # before last %
            op = ET.Element("op", attrib={"kind": "mod", "type": "int", "prio": "5"})
            op.append(to_tree_essence(modl, consts))
            op.append(to_tree_essence(modr, consts))
            return op
        else:
            raise ValueError(f'ERROR: Parsing error in "{input_str}"!')
    elif "!" in input_str:  # monadic operators
        op = ET.Element("op", attrib={"kind": "not", "type": "bool", "prio": "6"})
        op.append(to_tree_essence(input_str.split("!", 1)[-1], consts))
        return op
    elif input_str.strip().startswith("§"):
        op = ET.Element("op", attrib={"kind": "sub", "type": "int", "prio": "3"})
        op_sub = ET.SubElement(
            op, "op", attrib={"kind": "const", "type": "int", "prio": "8"}
        )
        op_sub.text = "0"
        op.append(to_tree_essence(input_str.split("§", 1)[1], consts))
        return op
    elif input_str.strip().startswith("$$"):  # constants $$
        try:
            # Extract the index after $$
            index_str = input_str.split("$$", 1)[1].strip()
            # Find the first non-digit character
            index_end = 0
            while index_end < len(index_str) and index_str[index_end].isdigit():
                index_end += 1
            # Get just the number part
            index = int(index_str[:index_end]) - 1
            if 0 <= index < len(consts):
                return consts[index]
            else:
                raise ValueError(f"Constant index {index + 1} out of range")
        except (ValueError, IndexError) as e:
            raise ValueError(f"Invalid constant reference in '{input_str}': {str(e)}")
    elif input_str.strip().startswith("$"):  # variables $
        op = ET.Element("op", attrib={"kind": "var", "prio": "7"})
        if re.match(r"^\s*\$[a-z]\s*$", input_str):
            op.set("type", "int")
        op.text = input_str.split("$", 1)[1].strip()
        return op
    elif input_str.strip().upper().startswith("0B"):  # numeric litarals
        op = ET.Element("op", attrib={"kind": "const", "type": "int", "prio": "8"})
        op.text = str(str2base(input_str.strip()[2:], 2))
        return op
    elif input_str.strip().upper().startswith("0X"):
        op = ET.Element("op", attrib={"kind": "const", "type": "int", "prio": "8"})
        op.text = str(str2base(input_str.strip()[2:], 16))
        return op
    elif input_str.strip().upper().startswith("0O"):
        op = ET.Element("op", attrib={"kind": "const", "type": "int", "prio": "8"})
        op.text = str(str2base(input_str.strip()[2:], 8))
        return op
    elif re.match(r"^\d+$", input_str.strip()):
        op = ET.Element("op", attrib={"kind": "const", "type": "int", "prio": "8"})
        op.text = str(str2base(input_str.strip(), 10))
        return op
    else:
        op = ET.Element("op", attrib={"kind": "const", "type": "string", "prio": "8"})
        op.text = input_str
        return op


def str2base(input_str: str, base: int):
    # Remove prefix if present
    input_str = re.sub(r"^0[xyzob]", "", input_str, flags=re.IGNORECASE).upper()
    # Define valid symbols for each base
    symbols = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"[:base]

    if len(input_str) == 0:
        raise ValueError("ERROR: the string is empty!")

    if base < 2:
        raise ValueError(f"ERROR: base {base} is not supportet!")

    if not all(c in symbols for c in input_str):
        raise ValueError(
            f"ERROR: the string contains invalid characters for base {base}!"
        )

    # For base 10, we use Python's built-in int conversion
    if base == 10:
        return int(input_str)
    # For other bases, use the manual conversion
    value = 0
    for i, char in enumerate(reversed(input_str)):
        digit_value = symbols.index(char)
        value += digit_value * (base**i)
    return value


def extract_quoted(input_str: str, consts: List[str] = []) -> List[str]:
    quot = '"'
    apos = "'"

    double_length = (
        len(input_str.split(quot, 1)[0]) if quot in input_str else len(input_str)
    )
    single_length = (
        len(input_str.split(apos, 1)[0]) if apos in input_str else len(input_str)
    )

    if double_length < single_length:
        sub_str = input_str.split(quot, 1)[1] if quot in input_str else ""
        sub_s = sub_str.split(quot, 1)[1] if quot in sub_str else ""
        if double_length == 0 and len(sub_str) == 0:  # just a single ": string = '"'
            return extract_quoted(sub_s, consts + [quot])
        elif sub_str.startswith(quot):
            return extract_quoted(sub_s, consts)
        else:
            before_s = sub_str.split(quot, 1)[0] if quot in sub_str else ""
            return extract_quoted(sub_s, consts + [before_s])
    elif double_length > single_length:
        sub_str = input_str.split(apos, 1)[1] if apos in input_str else ""
        sub_s = sub_str.split(apos, 1)[1] if apos in sub_str else ""
        if single_length == 0 and len(sub_str) == 0:  # just a single ': string = "'"
            return extract_quoted(sub_s, consts + [apos])
        elif sub_str.startswith(apos):
            return extract_quoted(sub_s, consts)
        else:
            before_s = sub_str.split(apos, 1)[0] if apos in sub_str else ""
            return extract_quoted(sub_s, consts + [before_s])
    else:
        return consts


def patch_quoted(input_str: str, consts: list) -> str:
    quot = '"'
    apos = "'"

    double_length = (
        len(input_str.split(quot, 1)[0]) if quot in input_str else len(input_str)
    )
    single_length = (
        len(input_str.split(apos, 1)[0]) if apos in input_str else len(input_str)
    )

    if double_length < single_length:
        s = input_str.split(quot, 1)[1]
        if double_length == 0 and len(s) == 0:
            return f"$$ {next((c.get('pos') for c in consts if c.text == quot), None)}"
        elif s.startswith(quot):
            return f"{input_str[:double_length]}$$1{patch_quoted(s[1:], consts)}"
        else:
            before_s = s.split(quot, 1)[0]
            pos = next((c.get("pos") for c in consts if c.text == before_s), None)
            return f"{input_str[:double_length]}$${pos}{patch_quoted(s[len(before_s) + 1:], consts)}"

    elif double_length > single_length:
        s = input_str.split(apos, 1)[1]
        if single_length == 0 and len(s) == 0:
            return f"$$ {next((c.get('pos') for c in consts if c.text == apos), None)}"
        elif s.startswith(apos):
            return f"{input_str[:single_length]}$$1{patch_quoted(s[1:], consts)}"
        else:
            before_s = s.split(apos, 1)[0]
            pos = next((c.get("pos") for c in consts if c.text == before_s), None)
            return f"{input_str[:single_length]}$${pos}{patch_quoted(s[len(before_s) + 1:], consts)}"

    else:
        return input_str


def decimal_to_hex(decimal_number: int) -> str:
    hex_digits = "0123456789ABCDEF"
    upper_digits = decimal_to_hex(decimal_number // 16) if decimal_number >= 16 else ""
    current_digit = hex_digits[decimal_number % 16]
    return upper_digits + current_digit


def parse_essence(input_str: str) -> list:
    consts = []
    for position, const in enumerate(
        extract_quoted(input_str, []), start=1
    ):  # we start from 1, bc we need position, not index
        op = ET.Element(
            "op",
            {"kind": "const", "type": "string", "prio": "8", "pos": str(position)},
        )
        op.text = const
        consts.append(op)
    patched_str = patch_quoted(input_str, consts)
    return to_tree_essence(patched_str, consts)


def num_essence(
    in_list, context: str, paramaps2, warning="recover"
):  # evaluate syntax tree for a numeric target
    # in_list is xml-element extracted from list (in_list[0])
    if in_list.get("kind") == "and" and len(in_list) > 1:
        return (
            0
            if (
                num_essence(in_list[0], context, paramaps2) == 0
                or num_essence(in_list[1], context, paramaps2) == 0
            )
            else 1
        )
    elif in_list.get("kind") == "or" and len(in_list) > 1:
        return (
            1
            if (
                num_essence(in_list[0], context, paramaps2) == 1
                or num_essence(in_list[1], context, paramaps2) == 1
            )
            else 0
        )
    elif in_list.get("kind") == "xor" and len(in_list) > 1:
        return (
            0
            if (
                num_essence(in_list[0], context, paramaps2)
                == num_essence(in_list[1], context, paramaps2)
            )
            else 1
        )
    elif (
        in_list.get("kind") in ("ge", "le", "lt", "gt", "eq", "ne", "nm", "ma")
        and len(in_list) > 1
        and (in_list[0].get("type") == "string" or in_list[1].get("type") == "string")
    ):
        left = text_essence(in_list[0], context, paramaps2)
        right = text_essence(in_list[1], context, paramaps2)
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
    elif in_list.get("kind") == "ge" and len(in_list) > 1:
        return (
            0
            if num_essence(in_list[0], context, paramaps2)
            < num_essence(in_list[1], context, paramaps2)
            else 1
        )
    elif in_list.get("kind") == "le" and len(in_list) > 1:
        return (
            0
            if num_essence(in_list[0], context, paramaps2)
            > num_essence(in_list[1], context, paramaps2)
            else 1
        )
    elif in_list.get("kind") == "gt" and len(in_list) > 1:
        return (
            1
            if num_essence(in_list[0], context, paramaps2)
            > num_essence(in_list[1], context, paramaps2)
            else 0
        )
    elif in_list.get("kind") == "lt" and len(in_list) > 1:
        return (
            1
            if num_essence(in_list[0], context, paramaps2)
            < num_essence(in_list[1], context, paramaps2)
            else 0
        )
    elif in_list.get("kind") == "eq" and len(in_list) > 1:
        return (
            1
            if num_essence(in_list[0], context, paramaps2)
            == num_essence(in_list[1], context, paramaps2)
            else 0
        )
    elif in_list.get("kind") == "ne" and len(in_list) > 1:
        return (
            0
            if num_essence(in_list[0], context, paramaps2)
            == num_essence(in_list[1], context, paramaps2)
            else 1
        )
    elif in_list.get("kind") == "add" and len(in_list) > 1:
        return num_essence(in_list[0], context, paramaps2) + num_essence(
            in_list[1], context, paramaps2
        )
    elif in_list.get("kind") == "sub" and len(in_list) > 1:
        return num_essence(in_list[0], context, paramaps2) - num_essence(
            in_list[1], context, paramaps2
        )
    elif in_list.get("kind") == "mul" and len(in_list) > 1:
        return num_essence(in_list[0], context, paramaps2) * num_essence(
            in_list[1], context, paramaps2
        )
    elif in_list.get("kind") == "div" and len(in_list) > 1:
        divisor = num_essence(in_list[1], context, paramaps2)
        if divisor == 0:
            raise ValueError("ERROR: Divide by 0!")
        return num_essence(in_list[0], context, paramaps2) // divisor
    elif in_list.get("kind") == "mod" and len(in_list) > 1:
        class_var = num_essence(in_list[1], context, paramaps2)
        if class_var == 0:
            raise ValueError("ERROR: modulo 0!")
        return num_essence(in_list[0], context, paramaps2) % class_var
    elif in_list.get("kind") == "exp" and len(in_list) > 1:
        b = num_essence(in_list[0], context, paramaps2)
        e = num_essence(in_list[1], context, paramaps2)
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
            return power2(int(e))
        else:
            return power(b, int(e))
    elif in_list.get("kind") == "not" and len(in_list) > 0:
        return 1 if num_essence(in_list[0], context, paramaps2) == 0 else 0
    elif in_list.get("kind") == "const" and in_list.get("type") in ("int", "bool"):
        if in_list.text.upper().startswith("0B"):
            return str2base(in_list.text[2:], 2)
        elif in_list.text.upper().startswith("0X"):
            return str2base(in_list.text[2:], 16)
        elif in_list.text.upper().startswith("0O"):
            return str2base(in_list.text[2:], 8)
        elif re.match(r"^\d+$", in_list.text):
            return int(in_list.text)
        else:
            raise ValueError(f"ERROR: Non-numeric value {in_list.text}")
    elif in_list.get("kind") == "const" and in_list.get("type") == "string":
        # Try to convert string to number if it's a numeric string
        if re.match(r"^\d+$", in_list.text):
            return int(in_list.text)
        # For non-numeric strings, return the string value
        return in_list.text
    elif in_list.get("kind") == "const":
        if warning == "fatal":
            raise ValueError(f"ERROR: Non-numeric value {in_list}")
        else:
            print("Replaced by -1")
            return -1
    elif in_list.get("kind") == "var":
        try:
            root = ET.parse(paramaps2).getroot()
        except Exception as e:
            print(e)

        get_parameter = []
        key = f"{context}:{in_list.text}"

        # Find the parameter element with matching Int_Class_ID
        for param in root.findall(f".//parameter[@Int_Class_ID='{key}']"):
            # Find all elements that end with 'Value' and sort by length of tag name
            value_elements = []
            for elem in param.iter():
                if elem.tag.endswith("Value"):
                    text = elem.text or ""
                    value_elements.append((len(elem.tag), text))

            # Sort by length of tag name
            value_elements.sort(key=lambda x: x[0])
            get_parameter.extend(text for _, text in value_elements)

        if len(get_parameter) > 0 and len(get_parameter[0]):
            return num_essence(parse_essence(get_parameter[0], context, paramaps2))
        else:
            if warning == "fatal":
                raise ValueError(f"ERROR: Unresolved parameter {in_list.text}!")
            else:
                print("Replaced by -1")
                return -1
    
    elif in_list.get('kind') == 'func' and len(in_list) == 2 and in_list[0].text == 'eng':
        return text_essence(in_list, context, paramaps2)
    
    elif in_list.get("kind") == "func" and len(in_list) != 3:
        raise ValueError(
            f"ERROR: Wrong number of parameters for function {in_list[0].text}"
        )
    elif (
        in_list.get("kind") == "func" and in_list[0].text == "min"
    ):
        paras = [
            int(num_essence(par, context, paramaps2))
            for par in in_list.findall("./*")[1:]
        ]
        return paras[0] if paras[0] < paras[1] else paras[1]
    elif (
        in_list.get("kind") == "func" and in_list[0].text == "max"
    ):
        paras = [
            int(num_essence(par, context, paramaps2))
            for par in in_list.findall("./*")[1:]
        ]
        return paras[0] if paras[0] > paras[1] else paras[1]
    elif (
        in_list.get("kind") == "func"
        and in_list[0].text == "rshift"
    ):
        paras = [
            int(num_essence(par, context, paramaps2))
            for par in in_list.findall("./*")[1:]
        ]
        if paras[1] == 0:
            return paras[0]
        elif paras[1] < 0:
            return paras[0] * power(2, int(-paras[1]))
        else:
            return paras[0] // power(2, int(paras[1]))
    elif (
        in_list.get("kind") == "func"
        and in_list[0].text == "lshift"
    ):
        paras = [
            int(num_essence(par, context, paramaps2))
            for par in in_list.findall("./*")[1:]
        ]
        if paras[1] == 0:
            return paras[0]
        elif paras[1] < 0:
            return paras[0] // power(2, int(-paras[1]))
        else:
            return paras[0] * power(2, int(paras[1]))
    elif (
        in_list.get("kind") == "func" and in_list[0].text == "log"
    ):
        paras = [
            int(num_essence(par, context, paramaps2))
            for par in in_list.findall("./*")[1:]
        ]
        return log(paras[0], paras[1])
    elif (
        in_list.get("kind") == "func" and in_list[0].text == "pos"
    ):
        index = num_essence(in_list[2], context, paramaps2)
        paras = []
        if in_list[1].get("kind") == "func" and in_list[1][0].text == "list":
            for i, p in enumerate(in_list[1]):
                if i - 2 == index:
                    paras.append(p)
        elif in_list[1].get("kind") == "var":
            try:
                root = ET.parse(paramaps2).getroot()
            except Exception as e:
                print(e)

            get_parameter = []
            key = f"{context}:{in_list[1].text}"

            # Find the parameter element with matching Int_Class_ID
            for param in root.findall(f".//parameter[@Int_Class_ID='{key}']"):
                # Find all elements that end with 'Value' and sort by length of tag name
                value_elements = []
                for elem in param.iter():
                    if elem.tag.endswith("Value"):
                        text = elem.text or ""
                        value_elements.append((len(elem.tag), text))

                # Sort by length of tag name
                value_elements.sort(key=lambda x: x[0])
                get_parameter.extend(text for _, text in value_elements)

            if len(get_parameter) > 0 and len(get_parameter[0]) > 0:
                tree = parse_essence(get_parameter[0])
                if tree.get("kind") == "func" and tree[0].text == "list":
                    for i, tr in enumerate(tree):
                        if i - 2 == index:
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
            return num_essence(paras[0], context, paramaps2)
        else:
            if warning == "fatal":
                raise ValueError(
                    f"ERROR: pos({in_list[1]},{index}) index out of bounds!"
                )
            else:
                print("pos(...) replaced by -1")
                return -1
    elif ((in_list.get('kind') == 'cat' and len(in_list) > 1) 
          and (in_list[0].get('type') == 'string' or in_list[1].get('type') == 'string')):
        return text_essence(in_list, context, paramaps2)
    
    else:
        if warning == "fatal":
            raise ValueError(f"ERROR: Non-numeric value !")
        else:
            print("Replaced by -1<")
            return -1


def integer_essence(
    input_str: str, context: str = None, paramaps2=None, varmap: list = None
):
    if context is None:
        return integer_essence(input_str, context="0", paramaps2=paramaps2)
    elif varmap is None:
        return num_essence(
            parse_essence(input_str), context=context, paramaps2=paramaps2
        )
    else:
        return num_essence(
            prune_essence(prune_essence(input_str), context, varmap, 0),
            context=context,
            paramaps2=paramaps2,
        )


def text_essence(
    input_data, context: str = "0", para_maps2=None, warning="fatal", suppress=""
):
    # input_data is xml-element extracted from list (input_data[0])
    if not input_data.get("kind"):
        return ""

    kind = input_data.get("kind")

    try:
        root = ET.parse(para_maps2).getroot()
    except Exception as e:
        print(e)

    if kind == "cat":
        return text_essence(
            input_data[0], context, para_maps2, warning, suppress
        ) + text_essence(input_data[1], context, para_maps2, warning, suppress)

    elif kind == "const" and input_data.text == "#":
        return input_data.text

    elif kind == "const":
        return re.sub(r"&amp;amp;", "&amp;", input_data.text)

    elif kind == "var" and input_data.text == "suppress" and len(suppress) > 0:
        return suppress

    elif kind == "var":
        get_parameter = []
        key = f"{context}:{input_data.text}"

        # Find the parameter element with matching Int_Class_ID
        for param in root.findall(f".//parameter[@Int_Class_ID='{key}']"):
            # Find all elements that end with 'Value' and sort by length of tag name
            value_elements = []
            for elem in param.iter():
                if elem.tag.endswith("Value"):
                    # Remove quotes from text if present
                    text = elem.text or ""
                    if text.startswith('"') and text.endswith('"'):
                        text = text[1:-1]
                    value_elements.append((len(elem.tag), text))

            # Sort by length of tag name (equivalent to XSLT sort)
            value_elements.sort(key=lambda x: x[0])
            get_parameter.extend(text for _, text in value_elements)

        # Add filter values if filter exists for this context
        if root.find(f".//filter[@Int_Class_ID='{context}']") is not None:
            filter_values = get_filter(input_data.text, context, root)
            get_parameter.extend(filter_values)

        # Add the parameter name itself as fallback
        get_parameter.append(input_data.text)

        if len(get_parameter) < 2:
            error_msg = f'ERROR: Unresolved parameter "{input_data.get("text")}"!'
            if warning == "fatal":
                raise ValueError(error_msg)
            else:
                print(error_msg)
                print(f'Replaced by "{get_parameter[0]}"')

        return get_parameter[0]

    elif kind == "func" and input_data[0].text == "pos" and len(input_data) == 3:
        index = num_essence(input_data[2], context, para_maps2, warning)
        paras = []

        if input_data[1].get("kind") == "func" and input_data[1][0].text == "list":
            for pos, child in enumerate(input_data[1]):
                if pos - 2 == index:
                    paras.append(child)
        elif input_data[1].get("kind") == "var":
            get_parameter = []
            key = f"{context}:{input_data[1].text}"

            # Find the parameter element with matching Int_Class_ID
            for param in root.findall(f".//parameter[@Int_Class_ID='{key}']"):
                # Find all elements that end with 'Value'
                for elem in param.iter():
                    if elem.tag.endswith("Value"):
                        if elem.text:
                            get_parameter.append(elem.text)

            if len(get_parameter) > 0 and len(get_parameter[0]) > 0:
                tree = parse_essence(get_parameter[0])
                if tree.get("kind") == "func" and tree[0].text == "list":
                    for pos, child in enumerate(tree[1]):
                        if pos - 2 == index:
                            paras.append(child)
                else:
                    raise ValueError(
                        f'ERROR: Invalid first parameter in "pos({input_data[1].text},...)"!'
                    )
            else:
                if warning == "fatal":
                    raise ValueError(f'ERROR: Unresolved parameter "{input_data.text}"')
                else:
                    print("Replaced by -1")
                    return "-1"
        else:
            raise ValueError("ERROR: Invalid first parameter in 'pos()'!")

        if len(paras) > 0:
            return text_essence(paras[0], context, para_maps2, warning, suppress)
        else:
            if warning == "fatal":
                raise ValueError(
                    f"ERROR: pos({input_data[1]},{index}) index out of bounds!"
                )
            else:
                print("Replaced by -1")
                return "-1"

    elif kind == "func" and input_data[0].text == "dec" and len(input_data) == 3:
        paras = [
            num_essence(child, context, para_maps2, warning) for child in input_data[1:]
        ]
        s = str(paras[1])
        p = "0" * (int(paras[0]) - len(s))
        return p + s

    elif kind == "func" and input_data[0].text == "hex" and len(input_data) == 3:
        paras = [
            num_essence(child, context, para_maps2, warning) for child in input_data[1:]
        ]
        s = decimal_to_hex(paras[1])
        p = "0" * (int(paras[0]) - len(s))
        return p + s

    elif kind == "func" and input_data[0].text == "bin" and len(input_data) == 3:
        paras = [
            num_essence(child, context, para_maps2, warning) for child in input_data[1:]
        ]
        s = decimal_to_bin(paras[1])
        p = "0" * (int(paras[0]) - len(s))
        return p + s

    elif kind == "func" and input_data[0].text == "eng" and len(input_data) == 2:
        val = num_essence(input_data[1], context, para_maps2, warning)

        if val >= 1073741824:
            return f"{math.floor(val / 10737418.24) / 100}GB"
        elif val >= 1048576:
            return f"{math.floor(val / 10485.76) / 100}MB"
        elif val >= 1024:
            return f"{math.floor(val / 10.24) / 100}KB"
        else:
            return f"{val}B"

    else:
        return str(num_essence(input_data, context, para_maps2, warning))


def decimal_to_hex(decimal_value):
    return format(int(decimal_value), "x")


def decimal_to_bin(decimal_value):
    return format(int(decimal_value), "b")


def prune_essence(
    paramaps2,
    in_list: list,
    context: str = None,
    varmap: list = None,
    pol: int = None,
    warning: str = "recover",
    suppress: str = "",
) -> list:
    if context is None:
        return prune_essence(in_list, "", [], 0)
    elif varmap is None:
        return prune_essence(in_list, context, [], 0)
    else:
        left = [prune_essence(in_list[0], context, varmap, pol)] if in_list else []
        right = (
            [prune_essence(in_list[1], context, varmap, pol)]
            if len(in_list) > 1
            else []
        )
        if in_list.get("kind") == "func":
            lastp = prune_essence(in_list[-1], context, varmap, pol)
            if len(in_list) != 3:
                op_element = ET.Element("op")
                for attr in in_list.attrib:
                    op_element.set(attr, in_list.attrib[attr])

                if len(in_list) > 0:
                    op_element.append(in_list[0])
                op_element.append(right)
                for child in in_list[2:]:
                    op_element.append(prune_essence(child, context, varmap, pol))
            elif (
                in_list[0].text in ("lshift", "rshift")
                and right.get("kind") == "const"
                and right.text == "0"
            ):
                return right
            elif (
                in_list[0].text in ("lshift", "rshift")
                and lastp.get("kind") == "const"
                and lastp.text == "0"
            ):
                return right
            elif (
                in_list[0].text in ("min", "max", "lshift", "rshift", "log")
                and right.get("kind") == "const"
                and lastp.get("kind") == "const"
            ):
                res = []
                op_element = ET.Element("op")
                for attr in in_list.attrib:
                    op_element.set(attr, in_list.attrib[attr])

                if len(in_list) > 0:
                    op_element.append(in_list[0])
                op_element.append(right)
                op_element.append(lastp)
                res.append(op_element)

                ET.Element(
                    "op", attrib={"kind": "const", "type": "int", "prio": "8"}
                ).text = num_essence(res, "0")
            elif in_list[0].text == "pos" and lastp.get("kind") == "const":
                index = num_essence(lastp, context)
                paras = []
                if right.get("kind") == "func" and right[0].text == "list":
                    for i, r in enumerate(right):
                        if i - 2 == index:
                            paras.append(r)
                # elif right.get("kind") == "var" and root.find( # not ready
                #     f".//{context}:{right.text}"
                # ):  # not ready
                #     parameter_node = root.find(f".//{context}:{right.text}")
                #     value_nodes = [
                #         child.text
                #         for child in parameter_node.findall("*")
                #         if child.tag.endswith("Value") and child.text is not None
                #     ]
                #     get_parameter = sorted(value_nodes, key=len)

                #     for pm2 in get_parameter: # not ready
                #         if root.find(".//DataType") is not None:
                #             if root.find(".//DataType").get("xsi:type") == "Array":
                #                 tree = parse_essence(
                #                     re.sub(r"^&quot;(list.*)&quot;$", r"1", pm2)
                #                 )

            else:
                op_element = ET.Element("op")
                for attr in in_list.attrib:
                    op_element.set(attr, in_list.attrib[attr])

                if len(in_list) > 0:
                    op_element.append(in_list[0])
                op_element.append(right)
                op_element.append(lastp)
        elif in_list.get("kind") == "not" and pol != 0:
            if left.get("kind") == "not":
                return prune_essence(left[0], context, varmap, pol)
            elif left.get("kind") == "const":
                op_element = ET.Element("op")
                for attr in left.attrib:
                    op_element.set(attr, left.attrib[attr])
                op_element.text = 1 if left.text == "0" else 0
            else:
                op_element = ET.Element("op")
                for attr in in_list.attrib:
                    op_element.set(attr, in_list.attrib[attr])
                op_element.append(prune_essence(in_list[0], context, varmap, pol))
        elif in_list.get("kind") == "not":
            if left.get("kind") == "not":
                return left[0]
            elif left.get("kind") == "const":
                op_element = ET.Element("op")
                for attr in left.attrib:
                    op_element.set(attr, left.attrib[attr])
                op_element.text = 1 if left.text == "0" else 0
            else:
                op_element = ET.Element("op")
                for attr in in_list.attrib:
                    op_element.set(attr, in_list.attrib[attr])
                op_element.append(left)
        elif (
            in_list.get("kind") == "var"
            and in_list.text == "suppress"
            and len(suppress)
        ):
            ET.Element(
                "op", attrib={"kind": "const", "type": "string", "prio": "8"}
            ).text = suppress
        elif in_list.get("kind") == "var":  # not ready
            if paramaps2:
                key = f"{context}:{in_list.text}"
                # for param in paramaps2.get_parameters(key):
                #     get_parameter.append(param.replace('"', ''))
                    
                # if paramaps2.has_filter(context):
                #     get_parameter.extend(get_filter(in_list.text, context))
    
        elif in_list.get("kind") == "var":  # not ready
            pass
        elif (
            in_list.get("kind") == "var"
            and len(varmap) > 0
            and varmap.get("Name") == in_list.text
        ):  # not ready
            pass
        elif in_list.get("kind") == "var":  # not ready
            pass

        elif in_list.get("kind") == "const" or in_list.get("kind") == "var":
            return in_list
        elif (
            in_list.get("kind") == "and"
            and left.get("kind") == "const"
            and left.text == "0"
        ):
            return left
        elif (
            in_list.get("kind") == "and"
            and right.get("kind") == "const"
            and right.text == "0"
        ):
            return right
        elif in_list.get("kind") == "and" and left.get("kind") == "const":
            return right
        elif in_list.get("kind") == "and" and right.get("kind") == "const":
            return left
        elif (
            in_list.get("kind") == "or"
            and left.get("kind") == "const"
            and left.text == "1"
        ):
            return left
        elif (
            in_list.get("kind") == "or"
            and right.get("kind") == "const"
            and right.text == "1"
        ):
            return right
        elif in_list.get("kind") == "or" and left.get("kind") == "const":
            return right
        elif in_list.get("kind") == "or" and right.get("kind") == "const":
            return left
        elif (
            in_list.get("kind") == "xor"
            and left.get("kind") == "const"
            and right.get("kind") == "const"
        ):
            ET.Element(
                "op", attrib={"kind": "const", "type": "bool", "prio": "8"}
            ).text = (0 if right.text == left.text else 1)
        elif (
            in_list.get("kind") == "xor"
            and left.get("kind") == "const"
            and left.text == "1"
        ):
            ET.Element(
                "op", attrib={"kind": "not", "type": "bool", "prio": "6"}
            ).text = right
        elif (
            in_list.get("kind") == "xor"
            and right.get("kind") == "const"
            and right.text == "1"
        ):
            op_element = ET.Element(
                "op", attrib={"kind": "not", "type": "bool", "prio": "6"}
            )
            op_element.append(right)  # ???
            op_element.append(left)
        elif in_list.get("kind") == "xor" and left.get("kind") == "const":
            return right
        elif in_list.get("kind") == "xor" and right.get("kind") == "const":
            return left
        elif (
            in_list.get("kind") == "add"
            and left.get("kind") == "const"
            and left.text == "0"
            and right.get("type") == "int"
        ):
            return right
        elif (
            in_list.get("kind") == "add"
            and right.get("kind") == "const"
            and right.text == "0"
            and left.get("type") == "int"
        ):
            return left
        elif (
            in_list.get("kind") == "add"
            and left.get("kind") == "const"
            and left.get("type") == "int"
            and right.get("kind") == "const"
            and right.get("type") == "int"
        ):
            op_element = ET.Element("op")
            for attr in left.attrib:
                op_element.set(attr, left.attrib[attr])
            op_element.text = left.text + right.text
        elif (
            in_list.get("kind") == "cat"
            and left.get("kind") == "const"
            and len(left.text) == 0
        ):
            return right
        elif (
            in_list.get("kind") == "cat"
            and right.get("kind") == "const"
            and len(right.text) == 0
        ):
            return left
        elif (
            in_list.get("kind") == "cat"
            and left.get("kind") == "const"
            and right.get("kind") == "const"
        ):
            op_element = ET.Element("op")
            for attr in left.attrib:
                op_element.set(attr, left.attrib[attr])
            op_element.set("type", "string")
            if (
                in_list[0].get("kind") == "var"
                and len(varmap) != 0
                and varmap.get("Name") == in_list[0].text
                and varmap.get("fmt")
            ):  # not ready
                varmap_el = [el for el in varmap if el.get("Name") == in_list[0].text]

        elif (
            in_list.get("kind") == "sub"
            and right.get("kind") == "const"
            and right.text == "0"
        ):
            return left
        elif (
            in_list.get("kind") == "sub"
            and left.get("kind") == "const"
            and left.get("type") == "int"
            and right.get("kind") == "const"
            and right.get("type") == "int"
        ):
            op_element = ET.Element("op")
            for attr in left.attrib:
                op_element.set(attr, left.attrib[attr])
            op_element.text = left.text - right.text
        elif (
            in_list.get("kind") == "mul"
            and left.get("kind") == "const"
            and left.text == "0"
        ):
            return left
        elif (
            in_list.get("kind") == "mul"
            and right.get("kind") == "const"
            and right.text == "0"
        ):
            return right
        elif (
            in_list.get("kind") == "mul"
            and left.get("kind") == "const"
            and left.text == "1"
        ):
            return right
        elif (
            in_list.get("kind") == "mul"
            and right.get("kind") == "const"
            and right.text == "1"
        ):
            return left
        elif (
            in_list.get("kind") == "div"
            and right.get("kind") == "const"
            and right.text == "1"
        ):
            return left
        elif (
            in_list.get("kind") == "mod"
            and right.get("kind") == "const"
            and right.text < 2
        ):  # ???
            ET.Element(
                "op", attrib={"kind": "const", "type": "int", "prio": "8"}
            ).text = 0
        elif (
            in_list.get("kind") == "exp"
            and right.get("kind") == "const"
            and right.text < 1
        ):  # ???
            ET.Element(
                "op", attrib={"kind": "const", "type": "int", "prio": "8"}
            ).text = 1
        elif (
            in_list.get("kind") == "exp"
            and right.get("kind") == "const"
            and right.text < 2
        ):  # ???
            return left
        elif in_list.get("kind") == "nm" and left.get("pol") != 0:
            op_element = ET.Element("op")
            op_element.set("pol", pol)
            for attr in in_list.attrib:
                op_element.set(attr, in_list.attrib[attr])
            op = ET.SubElement(op_element, "op")
            op.set("pol", str(-int(left.get("pol"))))
            for attr in left.attrib:
                if attr != "pol":
                    op.set(attr, left.attrib[attr])
            if left.text:
                op.text = left.text
            op_element.append(right)
        elif in_list.get("kind") == "ma" and left.get("pol") != 0:
            op_element = ET.Element("op")
            op_element.set("pol", pol)
            for attr in in_list.attrib:
                op_element.set(attr, in_list.attrib[attr])
            op_element.append(left)
            op_element.append(right)
        elif (
            in_list.get("kind") in ("ma", "eq")
            and not (left.get("kind"))
            and not (right.get("kind"))
        ):
            ET.Element(
                "op", attrib={"kind": "const", "type": "bool", "prio": "8"}
            ).text = 1
        elif (
            in_list.get("kind") in ("nm", "ne")
            and not (left.get("kind"))
            and not (right.get("kind"))
        ):
            ET.Element(
                "op", attrib={"kind": "const", "type": "bool", "prio": "8"}
            ).text = 0
        elif in_list.get("kind") in ("ma", "eq") and not (left.get("kind")):
            ET.Element(
                "op", attrib={"kind": "const", "type": "bool", "prio": "8"}
            ).text = 0
        elif in_list.get("kind") in ("nm", "ne") and not (left.get("kind")):
            ET.Element(
                "op", attrib={"kind": "const", "type": "bool", "prio": "8"}
            ).text = 1
        elif in_list.get("kind") in ("ma", "ne") and not (right.get("kind")):
            ET.Element(
                "op", attrib={"kind": "const", "type": "bool", "prio": "8"}
            ).text = 1
        elif in_list.get("kind") in ("nm", "eq") and not (right.get("kind")):
            ET.Element(
                "op", attrib={"kind": "const", "type": "bool", "prio": "8"}
            ).text = 0
        else:
            res = []
            op_element = ET.Element("op")
            for attr in in_list.attrib:
                op_element.set(attr, in_list.attrib[attr])
            op_element.append(left)
            op_element.append(right)
            res.append(op_element)

            if (left.get("kind") == "const" and left.text == "#") or (
                right.get("kind") == "const" and right.text == "#"
            ):
                return res
            elif (
                left.get("kind") == "const"
                and right.get("kind") == "const"
                and in_list.get("type") == "int"
            ):
                ET.Element(
                    "op", attrib={"kind": "const", "type": "int", "prio": "8"}
                ).text = num_essence(res, "0")
            elif (
                left.get("kind") == "const"
                and right.get("kind") == "const"
                and in_list.get("type") == "bool"
            ):
                ET.Element(
                    "op", attrib={"kind": "const", "type": "bool", "prio": "8"}
                ).text = num_essence(res, "0")
            elif (
                left.get("kind") == "const"
                and right.get("kind") == "const"
                and in_list.get("type") == "string"
            ):
                ET.Element(
                    "op", attrib={"kind": "const", "type": "string", "prio": "8"}
                ).text = text_essence(res, "0")
            else:
                return res


def get_filter(parameter_name: str, context: str, para_maps: ET.Element) -> List:

    if parameter_name.startswith("{"):
        m = re.match(r"^\{(.)\}.$", parameter_name)
        key = m.group(1) if m else parameter_name
    else:
        key = parameter_name

    filter_root = para_maps.find(f".//filter[@Int_Class_ID='{context}']")
    if filter_root is None:
        print(f"ERROR: Undefined filter context '{context}'")
        return []

    values = []
    for child in filter_root:
        if child.tag.endswith("Value"):
            values.append(child.text or "")
    values.sort(key=len)
    return [values[0]] if values else []


def log(number, base):
    return logh(number, base, base * base, 0)


def logh(number, base, base2, n):
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


def power2(exp: int):
    if exp < 0:
        return 1.0 / power2(-exp)
    elif exp == 0:
        return 1
    elif exp == 1:
        return 2
    elif exp == 2:
        return 4
    elif exp == 3:
        return 8
    else:
        h = power2(exp // 2)
        return h * h if exp % 2 == 0 else 2 * h * h


def compare(left, right):
    if left == right:
        return 0
    return -1 if left < right else 1
