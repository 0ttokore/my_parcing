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


def prune_essence(
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
                index = Decimal(num_essence(lastp, context))
                paras = []
                if right.get("kind") == "func" and right[0].text == "list":
                    for i, r in enumerate(right):
                        if i - 2 == index:
                            paras.append(r)
                elif right.get("kind") == "var":  # дописать
                    pass

                if len(paras) > 0:
                    return prune_essence(paras[0], context, varmap, pol)
                else:
                    if warning == "fatal":
                        raise ValueError(
                            f"ERROR: pos({right}, {index}) index out of bounds!"
                        )
                    else:
                        print("pos(...) replaced by -1")
                        return -1
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
        elif in_list.get("kind") == "var":  # дописать
            pass
        elif in_list.get("kind") == "var":  # дописать
            pass
        elif in_list.get("kind") == "var" and len(varmap) > 0:  # дописать
            pass
        elif in_list.get("kind") == "var":  # дописать
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
            op_element.text = Decimal(left.text) + Decimal(right.text)
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
            if in_list[0].get("kind") == "var" and len(varmap) != 0:  # дописать
                pass
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
            op_element.text = Decimal(left.text) - Decimal(right.text)
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
            and Decimal(right.text) < 2
        ):  # ???
            ET.Element(
                "op", attrib={"kind": "const", "type": "int", "prio": "8"}
            ).text = 0
        elif (
            in_list.get("kind") == "exp"
            and right.get("kind") == "const"
            and Decimal(right.text) < 1
        ):  # ???
            ET.Element(
                "op", attrib={"kind": "const", "type": "int", "prio": "8"}
            ).text = 1
        elif (
            in_list.get("kind") == "exp"
            and right.get("kind") == "const"
            and Decimal(right.text) < 2
        ):  # ???
            return left
        elif in_list.get("kind") == "nm" and left.get("pol") != 0:
            op_element = ET.Element("op")
            op_element.set("pol", pol)
            for attr in in_list.attrib:
                op_element.set(attr, in_list.attrib[attr])
            op = ET.SubElement(op_element, "op")
            op.set("pol", -left.get("pol"))
            for attr in left.attrib:
                op.set(attr, left.attrib[attr])
            # дописать фильтр


def num_essence():
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

        # ET.dump(root[0])

        # ch = root.findall("./*")
        # ET.dump(ch[0])

        print(op.attrib)

    except Exception as e:
        logger.error(f"Conversion failed: {e}")
        raise


if __name__ == "__main__":
    main()
