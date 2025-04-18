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
        return f"varmap"
        return num_essence(
            prune_essence(prune_essence(input_str), context, varmap, 0), context
        )


def parse_essence(input_str: str) -> list:
    root = ET.Element("consts")
    consts = []
    for position, const in enumerate(
        extract_quoted(input_str, []), start=1
    ):  # we start from 1, bc we need position, not index
        op = ET.SubElement(
            root,
            "op",
            {"kind": "const", "type": "string", "prio": "8", "pos": str(position)},
        )
        op.text = const
    consts.append(root)
    patched_str = patch_quoted(input_str, consts)
    return to_tree_essence(patched_str, consts)


def num_essence():
    pass


def prune_essence():
    pass


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
        sub_str = input_str.split(quot, 1)[1] if quot in input_str else ""
        sub_s = sub_str.split(quot, 1)[1] if quot in sub_str else ""
        if double_length == 0 and len(sub_str) == 0:  # just a single ": string = '"'
            first_quote = next((c for c in consts if c.text == quot), None)
            if first_quote is not None:
                return f"$${first_quote.get('pos')}"
            else:
                return None
        elif sub_str.startswith(quot):
            return f"{input_str[:double_length]}'$$1'{patch_quoted(sub_s, consts)}"
        else:
            before_s = sub_str.split(quot, 1)[0] if quot in sub_str else ""
            first_quote = next((c for c in consts if c.text == before_s), None)
            if first_quote is not None:
                return f"{input_str[:double_length]}'$$'{first_quote.get('pos')}{patch_quoted(sub_s, consts)}"
            else:
                return None
    elif double_length > single_length:
        sub_str = input_str.split(apos, 1)[1] if apos in input_str else ""
        sub_s = sub_str.split(apos, 1)[1] if apos in sub_str else ""
        if double_length == 0 and len(sub_str) == 0:  # just a single ': string = "'"
            first_quote = next((c for c in consts if c.text == apos), None)
            if first_quote is not None:
                return f"$${first_quote.get('pos')}"
            else:
                return None
        elif sub_str.startswith(apos):
            return f"{input_str[:double_length]}'$$1'{patch_quoted(sub_s, consts)}"
        else:
            before_s = sub_str.split(apos, 1)[0] if apos in sub_str else ""
            first_quote = next((c for c in consts if c.text == before_s), None)
            if first_quote is not None:
                return f"{input_str[:double_length]}'$$'{first_quote.get('pos')}{patch_quoted(sub_s, consts)}"
    else:
        return input_str


def decimal_to_hex(decimal_number: int) -> str:
    hex_digits = "0123456789ABCDEF"
    upper_digits = decimal_to_hex(decimal_number // 16) if decimal_number >= 16 else ""
    current_digit = hex_digits[decimal_number % 16]
    return upper_digits + current_digit


def to_tree_essence(input_str: str, consts: list) -> list:
    root = ET.Element("Essence")
    if re.match(r"^\s*\$curlyLeft\s*$", input_str):
        ET.SubElement(
            root, "op", attrib={"kind": "const", "type": "string", "prio": "8"}
        ).text = "'{'"
    elif re.match(r"^\s*\$curlyRight\s*$", input_str):
        ET.SubElement(
            root, "op", attrib={"kind": "const", "type": "string", "prio": "8"}
        ).text = "'}'"
    elif re.match(r"^\s*true\s*$", input_str, re.IGNORECASE):
        ET.SubElement(
            root, "op", attrib={"kind": "const", "type": "bool", "prio": "8"}
        ).text = 1
    elif re.match(r"^\s*false\s*$", input_str, re.IGNORECASE):
        ET.SubElement(
            root, "op", attrib={"kind": "const", "type": "bool", "prio": "8"}
        ).text = 0
    # prio 1
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
            subtree = []
            op = ET.SubElement(
                root, "op", attrib={"kind": "func", "type": "int", "prio": "8"}
            )
            ET.SubElement(
                op, "op", attrib={"kind": "const", "type": "string", "prio": "8"}
            ).text = "min"

            for token in bracket.split(","):
                ET.SubElement(op, "token").text = to_tree_essence(token, consts)
            subtree.append(root)
            return to_tree_essence(
                f"{lbrack.replace("min$", "")}$${len(consts) + 1}{rbrack}",
                consts + [subtree],
            )
        elif lbrack.endswith("max"):
            subtree = []
            op = ET.SubElement(
                root, "op", attrib={"kind": "func", "type": "int", "prio": "8"}
            )
            ET.SubElement(
                op, "op", attrib={"kind": "const", "type": "string", "prio": "8"}
            ).text = "max"

            for token in bracket.split(","):
                ET.SubElement(op, "token").text = to_tree_essence(token, consts)
            subtree.append(root)
            return to_tree_essence(
                f"{lbrack.replace("max$", "")}$${len(consts) + 1}{rbrack}",
                consts + [subtree],
            )
        elif lbrack.endswith("rshift"):
            subtree = []
            op = ET.SubElement(
                root, "op", attrib={"kind": "func", "type": "int", "prio": "8"}
            )
            ET.SubElement(
                op, "op", attrib={"kind": "const", "type": "string", "prio": "8"}
            ).text = "rshift"

            for token in bracket.split(","):
                ET.SubElement(op, "token").text = to_tree_essence(token, consts)
            subtree.append(root)
            return to_tree_essence(
                f"{lbrack.replace("rshift$", "")}$${len(consts) + 1}{rbrack}",
                consts + [subtree],
            )
        elif lbrack.endswith("lshift"):
            subtree = []
            op = ET.SubElement(
                root, "op", attrib={"kind": "func", "type": "int", "prio": "8"}
            )
            ET.SubElement(
                op, "op", attrib={"kind": "const", "type": "string", "prio": "8"}
            ).text = "lshift"

            for token in bracket.split(","):
                ET.SubElement(op, "token").text = to_tree_essence(token, consts)
            subtree.append(root)
            return to_tree_essence(
                f"{lbrack.replace("lshift$", "")}$${len(consts) + 1}{rbrack}",
                consts + [subtree],
            )
        elif lbrack.endswith("log"):
            subtree = []
            op = ET.SubElement(
                root, "op", attrib={"kind": "func", "type": "int", "prio": "8"}
            )
            ET.SubElement(
                op, "op", attrib={"kind": "const", "type": "string", "prio": "8"}
            ).text = "log"

            for token in bracket.split(","):
                ET.SubElement(op, "token").text = to_tree_essence(token, consts)
            subtree.append(root)
            return to_tree_essence(
                f"{lbrack.replace("log$", "")}$${len(consts) + 1}{rbrack}",
                consts + [subtree],
            )
        elif re.match(r"dec\d*$", lbrack):
            subtree = []
            op = ET.SubElement(
                root, "op", attrib={"kind": "func", "type": "string", "prio": "8"}
            )
            ET.SubElement(
                op, "op", attrib={"kind": "const", "type": "string", "prio": "8"}
            ).text = "'dec'"
            ET.SubElement(
                op, "op", attrib={"kind": "const", "type": "int", "prio": "8"}
            ).text = (1 if lbrack.endswith("dec") else lbrack.split("dec", 1)[-1])
            ET.SubElement(op, "token").text = to_tree_essence(bracket, consts)
            subtree.append(root)
            return to_tree_essence(
                f"{lbrack.replace("dec\d*$", "")}$${len(consts) + 1}{rbrack}",
                consts + [subtree],
            )
        elif re.match(r"hex\d*$", lbrack):
            subtree = []
            op = ET.SubElement(
                root, "op", attrib={"kind": "func", "type": "string", "prio": "8"}
            )
            ET.SubElement(
                op, "op", attrib={"kind": "const", "type": "string", "prio": "8"}
            ).text = "'hex'"
            ET.SubElement(
                op, "op", attrib={"kind": "const", "type": "int", "prio": "8"}
            ).text = (1 if lbrack.endswith("hex") else lbrack.split("hex", 1)[-1])
            ET.SubElement(op, "token").text = to_tree_essence(bracket, consts)
            subtree.append(root)
            return to_tree_essence(
                f"{lbrack.replace("hex\d*$", "")}$${len(consts) + 1}{rbrack}",
                consts + [subtree],
            )
        elif re.match(r"bin\d*$", lbrack):
            subtree = []
            op = ET.SubElement(
                root, "op", attrib={"kind": "func", "type": "string", "prio": "8"}
            )
            ET.SubElement(
                op, "op", attrib={"kind": "const", "type": "string", "prio": "8"}
            ).text = "'bin'"
            ET.SubElement(
                op, "op", attrib={"kind": "const", "type": "int", "prio": "8"}
            ).text = (1 if lbrack.endswith("bin") else lbrack.split("bin", 1)[-1])
            ET.SubElement(op, "token").text = to_tree_essence(bracket, consts)
            subtree.append(root)
            return to_tree_essence(
                f"{lbrack.replace("bin\d*$", "")}$${len(consts) + 1}{rbrack}",
                consts + [subtree],
            )
        elif re.match(r"eng$", lbrack):
            subtree = []
            op = ET.SubElement(
                root, "op", attrib={"kind": "func", "type": "string", "prio": "8"}
            )
            ET.SubElement(
                op, "op", attrib={"kind": "const", "type": "string", "prio": "8"}
            ).text = "'eng'"
            ET.SubElement(op, "token").text = to_tree_essence(bracket, consts)
            subtree.append(root)
            return to_tree_essence(
                f"{lbrack.replace("eng$", "")}$${len(consts) + 1}{rbrack}",
                consts + [subtree],
            )

        elif lbrack.endswith("list"):
            subtree = []
            op = ET.SubElement(
                root, "op", attrib={"kind": "func", "type": "int", "prio": "8"}
            )
            ET.SubElement(
                op, "op", attrib={"kind": "const", "type": "string", "prio": "8"}
            ).text = "list"

            for token in bracket.split(","):
                ET.SubElement(op, "token").text = to_tree_essence(token, consts)
            subtree.append(root)
            return to_tree_essence(
                f"{lbrack.replace("list$", "")}$${len(consts) + 1}{rbrack}",
                consts + [subtree],
            )
        elif lbrack.endswith("pos"):
            subtree = []
            op = ET.SubElement(
                root, "op", attrib={"kind": "func", "type": "int", "prio": "8"}
            )
            ET.SubElement(
                op, "op", attrib={"kind": "const", "type": "string", "prio": "8"}
            ).text = "pos"

            for token in bracket.split(","):
                ET.SubElement(op, "token").text = to_tree_essence(token, consts)
            subtree.append(root)
            return to_tree_essence(
                f"{lbrack.replace("pos$", "")}$${len(consts) + 1}{rbrack}",
                consts + [subtree],
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
            op = ET.SubElement(
                root, "op", attrib={"kind": "and", "type": "bool", "prio": "1"}
            )
            op.append(to_tree_essence(andl, consts))
            op.append(to_tree_essence(andr, consts))
        elif or_length < and_length and or_length < xor_length:
            orl = re.sub(r"&+$", "", input_str[: len(input_str) - or_length])
            op = ET.SubElement(
                root, "op", attrib={"kind": "or", "type": "bool", "prio": "1"}
            )
            op.append(to_tree_essence(orl, consts))
            op.append(to_tree_essence(orr, consts))
        elif xor_length < and_length and xor_length < or_length:
            xorl = input_str[: len(input_str) - xor_length - 1]
            right = to_tree_essence(xorr, consts)
            left = to_tree_essence(xorl, consts)
            if right.attrib["type"] != "bool" or left.attrib["type"] != "bool":
                return to_tree_essence(f"{xorl}%%{xorr}", consts)
            else:
                op = ET.SubElement(
                    root, "op", attrib={"kind": "xor", "type": "bool", "prio": "1"}
                )
                op.append(left)
                op.append(right)
                return op
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
            op = ET.SubElement(
                root, "op", attrib={"kind": "ne", "type": "bool", "prio": "2"}
            )
            op.append(to_tree_essence(nel, consts))
            op.append(to_tree_essence(ner, consts))
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
            op = ET.SubElement(
                root, "op", attrib={"kind": "ge", "type": "bool", "prio": "2"}
            )
            op.append(to_tree_essence(gel, consts))
            op.append(to_tree_essence(ger, consts))
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
            op = ET.SubElement(
                root, "op", attrib={"kind": "le", "type": "bool", "prio": "2"}
            )
            op.append(to_tree_essence(lel, consts))
            op.append(to_tree_essence(ler, consts))
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
            op = ET.SubElement(
                root, "op", attrib={"kind": "eq", "type": "bool", "prio": "2"}
            )
            op.append(to_tree_essence(eql, consts))
            op.append(to_tree_essence(eqr, consts))
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
            op = ET.SubElement(
                root, "op", attrib={"kind": "gt", "type": "bool", "prio": "2"}
            )
            op.append(to_tree_essence(gtl, consts))
            op.append(to_tree_essence(gtr, consts))
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
            op = ET.SubElement(
                root, "op", attrib={"kind": "lt", "type": "bool", "prio": "2"}
            )
            op.append(to_tree_essence(ltl, consts))
            op.append(to_tree_essence(ltr, consts))
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
            op = ET.SubElement(
                root, "op", attrib={"kind": "nm", "type": "bool", "prio": "2"}
            )
            op.append(to_tree_essence(nml, consts))
            op.append(to_tree_essence(nmr, consts))
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
            op = ET.SubElement(
                root, "op", attrib={"kind": "ma", "type": "bool", "prio": "2"}
            )
            op.append(to_tree_essence(mal, consts))
            op.append(to_tree_essence(mar, consts))
        else:
            raise ValueError(f'ERROR: Parsing error in "{input_str}"!')

    elif "+" in input_str or "-" in input_str:  # add/sub: + -
        addr = re.sub(r"^.*+", "", input_str)
        subr = re.sub(r"^.*-", "", input_str)
        add = len(addr)
        sub = len(subr)
        addl = input_str[: len(input_str) - add - 1]
        subl = input_str[: len(input_str) - sub - 1]

        if input_str.strip().startswith("+"):
            return to_tree_essence(input_str.split("+", 1)[1], consts)
        elif input_str.strip().startswith("-"):
            return to_tree_essence(f"§{input_str.split('-', 1)[1]}{consts}")
        elif add < sub and addl.endswith("-"):
            left = to_tree_essence(subl, consts)
            right = to_tree_essence(addr, consts)
            op = ET.SubElement(root, "op", attrib={"kind": "sub", "prio": "3"})
            if left[0].get("type") == "int" and right[1].get("type") == "int":
                op.set("type", "int")
            op.append(left)
            op.append(right)
        elif add < sub:
            left = to_tree_essence(re.sub(r"\+\s*$", "", addl), consts)
            right = to_tree_essence(addr, consts)
            if left[0].get("kind") == "cat" or right[0].get("kind") == "cat":
                op = ET.SubElement(root, "op", attrib={"kind": "cat", "prio": "3"})
                op.append(left)
                op.append(right)
            elif (left[0].get("type") == "string" and left[0].text != "#") or (
                right[0].get("type") == "string" or right[0].text != "#"
            ):
                op = ET.SubElement(
                    root, "op", attrib={"kind": "cat", "type": "string", "prio": "3"}
                )
                op.append(left)
                op.append(right)
            elif left[0].get("kind") == "const" and len(left[0].text) == 0:
                root.append(right)
            elif right[0].get("kind") == "const" and len(right[0].text) == 0:
                root.append(left)
            else:
                op = ET.SubElement(root, "op", attrib={"kind": "add", "prio": "3"})
                if left[0].get("type") == "int" and right[0].get("type") == "int":
                    op.set("type", "int")
                op.append(left)
                op.append(right)
        elif sub < add and subl.strip().endswith("+"):
            op = ET.SubElement(
                root, "op", attrib={"kind": "sub", "type": "int", "prio": "3"}
            )
            op.append(to_tree_essence(addl, consts))
            op.append(to_tree_essence(subr, consts))
        elif sub < add and subl.strip().endswith("-"):
            op = ET.SubElement(
                root, "op", attrib={"kind": "add", "type": "int", "prio": "3"}
            )
            op.append(to_tree_essence(re.sub("-\s*$"), "", subl), consts)
            op.append(to_tree_essence(subr, consts))
        elif sub < add and re.match(r"(\*|\||%)\s*$", subl):
            root.append(to_tree_essence(f"{subl}§{subr}", consts))
        elif sub < add:
            op = ET.SubElement(
                root, "op", attrib={"kind": "sub", "type": "int", "prio": "3"}
            )
            op.append(to_tree_essence(subl, consts))
            op.append(to_tree_essence(subr, consts))
        else:
            raise ValueError(f'ERROR: Parsing error in "{input_str}"!')
    elif "*" in input_str or "/" in input_str:  # mul/div: * /
        mulr = re.sub("^.*\*", "", input_str)
        divr = re.sub("^.*/", "", input_str)
        mul = len(mulr)
        div = len(divr)

        if mul < div:
            mull = input_str[: len(input_str) - mul - 1]
            op = ET.SubElement(
                root, "op", attrib={"kind": "mul", "type": "int", "prio": "4"}
            )
            op.append(to_tree_essence(mull, consts))
            op.append(to_tree_essence(mulr, consts))
        elif div < mul:
            divl = input_str[: len(input_str) - div - 1]
            op = ET.SubElement(
                root, "op", attrib={"kind": "div", "type": "int", "prio": "4"}
            )
            op.append(to_tree_essence(divl, consts))
            op.append(to_tree_essence(divr, consts))
        else:
            raise ValueError(f'ERROR: Parsing error in "{input_str}"!')
    elif "%" in input_str:  # mod: % %% (was ^)
        modr = re.sub("^.*%", "", input_str)
        expr = re.sub("^.*%%", "", input_str)
        mod = len(modr)  # after last %
        exp = len(expr)  # after last %%

        if mod < exp:
            modl = input_str[: len(input_str) - mod - 1]  # before last %
            op = ET.SubElement(
                root, "op", attrib={"kind": "mod", "type": "int", "prio": "5"}
            )
            op.append(to_tree_essence(modl, consts))
            op.append(to_tree_essence(modr, consts))
        elif exp < mod:
            expl = input_str[: len(input_str) - exp - 2]
            op = ET.SubElement(
                root, "op", attrib={"kind": "exp", "type": "int", "prio": "5"}
            )
            op.append(to_tree_essence(expl, consts))
            op.append(to_tree_essence(expr, consts))
        else:
            raise ValueError(f'ERROR: Parsing error in "{input_str}"!')
    elif "!" in input_str:  # monadic operators
        op = ET.SubElement(
            root, "op", attrib={"kind": "not", "type": "bool", "prio": "6"}
        )
        op.append(to_tree_essence(input_str.split("!", 1)[1]), consts)
    elif input_str.strip().startswith("§"):
        op = ET.SubElement(
            root, "op", attrib={"kind": "sub", "type": "int", "prio": "3"}
        )
        ET.SubElement(
            op, "op", attrib={"kind": "const", "type": "int", "prio": "8"}
        ).text = 0
        op.append(to_tree_essence(input_str.split("§", 1)[1]), consts)
    elif input_str.strip().startswith("$$"):  # constants $$
        root.append(consts[int(input_str.split("$$", 1)[1])])
    elif input_str.strip().startswith("$"):  # variables $
        op = ET.SubElement(root, "op", attrib={"kind": "var", "prio": "7"})
        if re.match(r"^\s*\$[a-z]\s*$", input_str):
            op.set("type", "int")
        op.text = input_str.split("$", 1)[1].strip()

    elif input_str.strip().upper().startswith("0B"):  # numeric litarals
        ET.SubElement(
            root, "op", attrib={"kind": "const", "type": "int", "prio": "8"}
        ).text = str2base(input_str.strip()[2:], 2)
    elif input_str.strip().upper().startswith("0X"):
        ET.SubElement(
            root, "op", attrib={"kind": "const", "type": "int", "prio": "8"}
        ).text = str2base(input_str.strip()[2:], 16)
    elif input_str.strip().upper().startswith("0O"):
        ET.SubElement(
            root, "op", attrib={"kind": "const", "type": "int", "prio": "8"}
        ).text = str2base(input_str.strip()[2:], 8)
    elif re.match(r"^\d+$", input_str.strip()):
        ET.SubElement(
            root, "op", attrib={"kind": "const", "type": "int", "prio": "8"}
        ).text = str2base(input_str.strip(), 10)
    else:
        ET.SubElement(
            root, "op", attrib={"kind": "const", "type": "string", "prio": "8"}
        ).text = input_str
        

def str2base(input_str:str, base:int): # дописать
    symbols = '_0123456789ABCDEF'
    
    last_char = input_str.strip()[-1].upper() if input_str.strip() else ''
    h = symbols.index(last_char) if last_char in symbols else -1
    if len(input_str) < 2 or re.match(r'^0+?.$', input_str):
        return float(h)
    
    cleaned_input = re.sub(r'^0+', '', input_str)
    cleaned_input = re.sub(r'.$', '', cleaned_input)
    
    return h + base * str2base(cleaned_input, base)


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

        input_str = "head(mid)tail"
        sub_str = input_str.split(")", 1)[0]
        bracket = re.sub(r"^.*\(", "", sub_str)
        brack = len(sub_str) + 1
        lbrack = re.sub(r"\s*\([^\(]*$", "", sub_str)
        rbrack = input_str[brack:]

        tree = ET.parse("./instance_sheet_TC49x.xml")
        root = tree.getroot()
        address = [
            add
            for add in root.findall(".//BusInstanceReference/BusInterfaceMap")
            if add.get("type") == "BusSlaveInterfaceMap"
        ]
        start_address = [
            add.find(".//StartAddress").text
            for add in address
            if add.find(".//StartAddress").text is not None
        ]
        end_address = [
            add.find(".//EndAddress").text
            for add in address
            if add.find(".//EndAddress").text is not None
        ]
        input_add = start_address[0]
        input_add = 'ex_1"head"ex_2\'mid\'ex_3"tail'
        # result = integer_essence(input_add)
        # print(parse_essence(input_add))
        # consts = (extract_quoted(input_add, []))
        # print(consts)
        # print(patch_quoted(input_add, consts))

        result = extract_quoted(input_add, [])
        print(result)

        root = ET.Element("consts")
        consts = []
        for position, const in enumerate(
            extract_quoted(input_add, []), start=1
        ):  # we start from 1, bc we need position, not index
            op = ET.SubElement(
                root,
                "op",
                {"kind": "const", "type": "string", "prio": "8", "pos": str(position)},
            )
            op.text = const
        consts.append(root)

        # for i in consts:
        #     ET.dump(i)

        patched_str = patch_quoted(input_add, consts)
        print(patched_str)

    except Exception as e:
        logger.error(f"Conversion failed: {e}")
        raise


if __name__ == "__main__":
    main()
