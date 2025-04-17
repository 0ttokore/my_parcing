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
            return to_tree_essence(f"{lbrack.replace("min$", "")}$${len(consts) + 1}{rbrack}", consts + [subtree])
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
            return to_tree_essence(f"{lbrack.replace("max$", "")}$${len(consts) + 1}{rbrack}", consts + [subtree])
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
            return to_tree_essence(f"{lbrack.replace("rshift$", "")}$${len(consts) + 1}{rbrack}", consts + [subtree])
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
            return to_tree_essence(f"{lbrack.replace("lshift$", "")}$${len(consts) + 1}{rbrack}", consts + [subtree])
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
            return to_tree_essence(f"{lbrack.replace("log$", "")}$${len(consts) + 1}{rbrack}", consts + [subtree])
        elif re.match(r'dec\d*$', lbrack):
            subtree = []
            op = ET.SubElement(
                root, "op", attrib={"kind": "func", "type": "string", "prio": "8"}
            )
            ET.SubElement(
                op, "op", attrib={"kind": "const", "type": "string", "prio": "8"}
            ).text = "'dec'"
            ET.SubElement(
                op, "op", attrib={"kind": "const", "type": "int", "prio": "8"}
            ).text = 1 if lbrack.endswith('dec') else lbrack.split('dec', 1)[-1]
            ET.SubElement(op, "token").text = to_tree_essence(bracket, consts)
            subtree.append(root)
            return to_tree_essence(f"{lbrack.replace("dec\d*$", "")}$${len(consts) + 1}{rbrack}", consts + [subtree])
        elif re.match(r'hex\d*$', lbrack):
            subtree = []
            op = ET.SubElement(
                root, "op", attrib={"kind": "func", "type": "string", "prio": "8"}
            )
            ET.SubElement(
                op, "op", attrib={"kind": "const", "type": "string", "prio": "8"}
            ).text = "'hex'"
            ET.SubElement(
                op, "op", attrib={"kind": "const", "type": "int", "prio": "8"}
            ).text = 1 if lbrack.endswith('hex') else lbrack.split('hex', 1)[-1]
            ET.SubElement(op, "token").text = to_tree_essence(bracket, consts)
            subtree.append(root)
            return to_tree_essence(f"{lbrack.replace("hex\d*$", "")}$${len(consts) + 1}{rbrack}", consts + [subtree])
        elif re.match(r'bin\d*$', lbrack):
            subtree = []
            op = ET.SubElement(
                root, "op", attrib={"kind": "func", "type": "string", "prio": "8"}
            )
            ET.SubElement(
                op, "op", attrib={"kind": "const", "type": "string", "prio": "8"}
            ).text = "'bin'"
            ET.SubElement(
                op, "op", attrib={"kind": "const", "type": "int", "prio": "8"}
            ).text = 1 if lbrack.endswith('bin') else lbrack.split('bin', 1)[-1]
            ET.SubElement(op, "token").text = to_tree_essence(bracket, consts)
            subtree.append(root)
            return to_tree_essence(f"{lbrack.replace("bin\d*$", "")}$${len(consts) + 1}{rbrack}", consts + [subtree])
        elif re.match(r'eng$', lbrack):
            subtree = []
            op = ET.SubElement(
                root, "op", attrib={"kind": "func", "type": "string", "prio": "8"}
            )
            ET.SubElement(
                op, "op", attrib={"kind": "const", "type": "string", "prio": "8"}
            ).text = "'eng'"
            ET.SubElement(op, "token").text = to_tree_essence(bracket, consts)
            subtree.append(root)
            return to_tree_essence(f"{lbrack.replace("eng$", "")}$${len(consts) + 1}{rbrack}", consts + [subtree])
        
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
            return to_tree_essence(f"{lbrack.replace("list$", "")}$${len(consts) + 1}{rbrack}", consts + [subtree])
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
            return to_tree_essence(f"{lbrack.replace("pos$", "")}$${len(consts) + 1}{rbrack}", consts + [subtree])
        else:
            subtree = to_tree_essence(bracket, consts)
            return to_tree_essence(f"{lbrack}$${len(consts) + 1}{rbrack}", consts + [subtree])
    
    elif '|' in input_str or '&' in input_str or '^' in input_str:
        orr = re.sub(r'^.*\|+', '', input_str)
        or_length = len(orr)
        andr = re.sub(r'^.*&+', '', input_str)
        and_length = len(andr)
        xorr = re.sub(r'^.*\^', '', input_str)
        xor_length = len(xorr)
        
        if and_length < or_length and and_length < xor_length:
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
        #result = integer_essence(input_add)
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
