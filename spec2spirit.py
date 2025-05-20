import xml.etree.ElementTree as ET
import logging
import re
from mathlib2 import decimal_to_hex, decimal_to_bin, power, str2base, num_essence, parse_essence
import math
from datetime import datetime, timezone, timedelta


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# the solver function for () + - * / mod div ^
def evaluate(input_str: str, context: str = "0") -> str:
    if input_str == " ":
        return 0

    # prio 1: ( )
    if ")" in input_str:
        bracket = re.sub(r"^.*\(", "", input_str.split(")")[0])
        prebracket = input_str[: len(input_str.split(")")[0]) - 1 - len(bracket)]

        if re.match(r"dec\d*$", prebracket):
            try:
                s = str(int(evaluate(bracket, context)))
            except Exception as e:
                logger.error(f"Conversion failed: {e}")
            p = [
                "0"
                for _ in range(
                    len(s) + 1, int(re.sub(r".*dec(\d*)$", r"0\1", prebracket))
                )
            ]
            return (
                re.sub(r"dec\d*$", "", prebracket)
                + "".join(p)
                + s
                + input_str.split(")")[1]
            )
        elif re.match(r"hex\d*$", prebracket):
            try:
                s = decimal_to_hex(str_to_number(evaluate(bracket, context)))
            except Exception as e:
                logger.error(f"Conversion failed: {e}")
            p = [
                "0"
                for _ in range(
                    len(s) + 1, int(re.sub(r".*hex(\d*)$", r"0\1", prebracket))
                )
            ]
            return (
                re.sub(r"hex\d*$", "", prebracket)
                + "".join(p)
                + s
                + input_str.split(")")[1]
            )
        elif re.match(r"bin\d*$", prebracket):
            try:
                s = decimal_to_bin(str_to_number(evaluate(bracket, context)))
            except Exception as e:
                logger.error(f"Conversion failed: {e}")
            p = [
                "0"
                for _ in range(
                    len(s) + 1, int(re.sub(r".*bin(\d*)$", r"0\1", prebracket))
                )
            ]
            return (
                re.sub(r"bin\d*$", "", prebracket)
                + "".join(p)
                + s
                + input_str.split(")")[1]
            )
        elif re.match(r"eng$", prebracket):
            try:
                val = str_to_number(evaluate(bracket, context))
            except Exception as e:
                logger.error(f"Conversion failed: {e}")
                raise
            p = []
            if val >= 1073741824:
                value = math.floor(val / 10737418.24) / 100
                p.append(f"{value}GB")
            elif val >= 1048576:
                value = math.floor(val / 10485.76) / 100
                p.append(f"{value}MB")
            elif val >= 1024:
                value = math.floor(val / 10.24) / 100
                p.append(f"{value}KB")
            else:
                p.append(f"{val}B")
            return (
                re.sub(r"eng$", "", prebracket) + "".join(p) + input_str.split(")")[1]
            )
        elif re.match(r"pow\d+$", prebracket):
            try:
                e = int(evaluate(bracket, context))
                b = str_to_number(re.sub(r".*pow(\d+)$", r"\1", prebracket))
            except Exception as e:
                logger.error(f"Conversion failed: {e}")
            return str_to_number(
                evaluate(
                    re.sub(r"pow\d+$", "", prebracket)
                    + str(power(b, e))
                    + input_str.split(")")[1],
                    context,
                )
            )
        elif re.match(r"min$", prebracket):
            vals = bracket.split(",")
            min_val = min(vals)
            return evaluate(
                re.sub(r"min$", "", prebracket) + min_val + input_str.split(")")[1],
                context,
            )
        elif re.match(r"max$", prebracket):
            vals = bracket.split(",")
            max_val = max(vals)
            return evaluate(
                re.sub(r"max$", "", prebracket) + max_val + input_str.split(")")[1],
                context,
            )
        else:
            return str_to_number(
                evaluate(
                    prebracket + evaluate(bracket, context) + input_str.split(")")[1],
                    context,
                )
            )

    elif "+" in input_str or re.match(r"[\d\w]+\s*-", input_str):  # least binding: + -
        plus = len(input_str.split("+")[0])
        minus = len(before_last_minus(input_str, ""))
        if plus < minus:  # no + or no + after -
            return str_to_number(evaluate(input_str[:minus], context)) - str_to_number(
                evaluate(input_str[minus + 2 :], context)
            )
        else:
            return str_to_number(evaluate(input_str[:plus], context)) + str_to_number(
                evaluate(input_str[plus + 2 :], context)
            )

    elif any(
        op in input_str for op in {"*", "/", "div", "mod"}
    ):  # highest binding: * / mod div
        mul = len(input_str.split("*")[0])
        div = len(input_str.split("/")[0])
        idiv = len(input_str.split("div")[0])
        mod = len(input_str.split("mod")[0])
        if mul > div and mul > idiv and mul > mod:
            return str_to_number(
                evaluate(input_str.split("*")[0], context)
            ) * str_to_number(evaluate(input_str.split("*")[1], context))
        elif div > mul and div > idiv and div > mod:
            return str_to_number(
                evaluate(input_str.split("/")[0], context)
            ) / str_to_number(evaluate(input_str.split("/")[1], context))
        elif idiv > mul and idiv > div and idiv > mod:
            return math.floor(
                str_to_number(evaluate(input_str.split("div")[0], context))
                / str_to_number(evaluate(input_str.split("div")[1], context))
            )
        else:
            return str_to_number(
                evaluate(input_str.split("mod")[0], context)
            ) % str_to_number(evaluate(input_str.split("mod")[1], context))

    elif "^" in input_str:  # highest binding: ^
        b = str_to_number(evaluate(input_str.split("^")[0], context))
        e = str_to_number(evaluate(input_str.split("^")[1], context))
        if b == 1 or e == 0:
            return 1
        elif b == 0:
            return 0
        elif e == 1:
            return b
        elif castable(b, "float") and castable(e, "integer"):
            return power(b, int(e))
        else:
            raise ValueError(f"ERROR: Not a valid numeric expression {input_str}")

    elif input_str.strip().startswith("$"):  # variables $
        return evaluate(
            get_parameter(input_str.split("$")[1], context).strip(), context
        )

    elif input_str.strip().upper().startswith("0B"):  # literals
        return str2base(input_str.strip().split("0B")[1], 2)
    elif input_str.strip().upper().startswith("0X"):
        return str2base(input_str.strip().split("0X")[1], 16)
    elif castable(input_str, "float"):
        return float(input_str)
    elif context == "0":
        return str_to_number(input_str)
    else:
        raise ValueError(f"ERROR: Expression is not a valid number - {input_str}")


def str_to_number(input_str: str):
    input_str = input_str.strip()
    if re.match(r"^\d+[.,]\d+$", input_str):
        return float(input_str)
    elif re.match(r"^\d+$", input_str):
        return int(input_str)
    else:
        raise ValueError(f"Invalid input: {input_str}")


def before_last_minus(input_str: str, result: str) -> str:
    if not re.match(input_str, r"[\d\w]+\s*-"):
        return result
    elif len(result) == 0:
        return before_last_minus(
            re.sub(r"^.*[\d\w]+\s*-", "", input_str),
            re.sub(r"^(.*[\d\w]+\s*)-.*$", r"\1", input_str),
        )
    else:
        return before_last_minus(
            re.sub(r"^.*[\d\w]+\s*-", "", input_str),
            result + "-" + re.sub(r"^(.*[\d\w]+\s*)-.*$", r"\1", input_str),
        )


def castable(input_str: str, type: str) -> bool:
    try:
        if type == "float" or type == "double":
            float(input_str)
        elif type == "integer":
            int(input_str)
        return True
    except ValueError:
        return False


# TODO: check searching key in para_maps2, bc it looks like it doen't matches
def get_parameter(
    par_name: str,
    context: str,
    para_maps2: ET.Element,
    suppress: str = "",
    warning: str = "recover",
) -> str:
    # return the content of the brackets if it exists, else return the parameter name
    key = (
        re.sub(r"^\{(.*)\}.*$", r"\1", par_name)
        if par_name.startswith("{")
        else par_name
    )

    # Check if context exists in para_maps2
    if not any(str(param.get("Int_Class_ID")) == context for param in para_maps2):
        error_msg = f'ERROR: Undefined context {context} for parameter "{key}"'
        logger.error(error_msg)
        return "?"

    if key == "suppress" and len(suppress) > 0:
        return suppress
    elif len(para_maps2.findall(f".//{context}:{key}")) > 0:
        return get_parameter_from_list(para_maps2, context, key)
    elif key.startswith("$") and len(para_maps2.findall(f".//{context}:{key[1:]}")) > 0:
        return get_parameter_from_list(para_maps2, context, key[1:])
    else:
        # Find the context's instance name for the error message
        context_elem = next(
            (param for param in para_maps2 if param.get("Int_Class_ID") == context),
            None,
        )
        context_name = context_elem.get("InstanceName") if context_elem else ""
        error_msg = f"ERROR: Undefined parameter {par_name} in Context {context_name} [{context}]"

        if warning == "fatal":
            raise ValueError(error_msg)
        else:
            logger.warning(error_msg)
            logger.info(f'Keeping value as "{par_name}"')
            return par_name


def get_parameter_from_list(para_maps2: ET.Element, context: str, key: str) -> str:
    list_of_params = []
    for param in para_maps2.findall(f".//f'{context}:{key[1:]}'"):
        # Find all elements that end with 'Value' and sort by length of tag name
        value_elements = []
        for elem in param.iter():
            if elem.tag.endswith("Value"):
                text = elem.text or ""
                value_elements.append((len(elem.tag), text))
        # Sort by length of tag name
        value_elements.sort(key=lambda x: x[0])
        list_of_params.extend(text for _, text in value_elements)
    return list_of_params[0]


def Connects(Connections: str) -> list:
    try:
        with open(
            Connections, "r"
        ) as file:  # TODO: check if it's a file or a directory
            connex = ET.parse(file).getroot()
    except FileNotFoundError:
        logger.error(f"Connections file not found: {Connections}")
        raise
    except ET.ParseError as e:
        logger.error(f"Failed to parse XML file {Connections}: {e}")
        raise

    ports = []  # TODO: check what file it's used in, bc it doesn't contain elements InterfaceItem and Type, text == 'PORT'
    sockets = []  # TODO: check what file it's used in, bc it doesn't contain elements InterfaceItem and Type, text == 'INTERFACE'

    for item in connex.findall('.//*/*/*[local-name()="InterfaceItem"]'):
        type_elem = item.find('./*[local-name()="Type"]')
        if type_elem is None:
            continue

        id_elem = item.find('./*[local-name()="Int_Class_ID"]')
        if id_elem is None or not id_elem.text:
            continue

        if type_elem.text == "PORT":
            port = ET.Element("port", {"ID": id_elem.text})
            # Copy required elements
            for elem_name in ["IsDriver", "ConceptInstanceName", "ConceptName", "Name"]:
                if elem := item.find(f'./*[local-name()="{elem_name}"]'):
                    port.append(ET.fromstring(ET.tostring(elem)))
            ports.append(port)
        elif type_elem.text == "INTERFACE":
            socket = ET.Element("socket", {"ID": id_elem.text})
            # Copy required elements
            for elem_name in ["ConceptInstanceName", "ConceptName", "Name"]:
                if elem := item.find(f'./*[local-name()="{elem_name}"]'):
                    socket.append(ET.fromstring(ET.tostring(elem)))
            ET.SubElement(socket, "IsDriver").text = "False"
            sockets.append(socket)

    connects = []  # result list of net2 elements
    # Process ConnectivityItems
    for item in connex.findall('.//*/*[local-name()="ConnectivityItem"]'):
        nets = []
        for current_ref in item.findall('.//*[local-name()="InterfaceItemRef"]'):
            for port in ports:
                if port.get("ID") == current_ref.text:
                    nets.append(port)
            for socket in sockets:
                if socket.get("ID") == current_ref.text:
                    nets.append(socket)
        # Find driver ports
        driver_ports = [
            net
            for net in nets
            if net.tag == "port"
            and net.find('./*[local-name()="IsDriver"]') is not None
            and net.find('./*[local-name()="IsDriver"]').text == "True"
        ]
        driver_sockets = [net for net in nets if net.tag == "socket"]

        if len(driver_ports) > 0:
            # Process driver ports
            driver = ET.Element("out")
            for port in driver_ports:
                #  preparing function normalize_concept_names() arguments:
                ci_elem = port.find('./*[local-name()="ConceptInstanceName"]')
                cn_elem = port.find('./*[local-name()="ConceptName"]')
                name_elem = port.find('./*[local-name()="Name"]')

                if ci_elem is None or (cn_elem is None and name_elem is None):
                    continue

                ci = ci_elem.text.replace(".", "_")
                cn = cn_elem.text if cn_elem is not None else name_elem.text

                #  call normalize_concept_names() and make subelements out of it
                for pair in normalize_concept_names(ci, cn):
                    ET.SubElement(driver, "ConceptInstanceName").text = pair.get("ci")
                    ET.SubElement(driver, "ConceptName").text = pair.get("cn")

            # Handle LVDS RX case
            first_ci = driver.find('./*[local-name()="ConceptInstanceName"]')
            if first_ci is not None:
                lvds_rx = re.match(r"^P\d+_\d+_\d+", first_ci.text)
                lvdsP = re.sub(r"^(P\d+)_\d+_(\d+)$", r"\1_\2", first_ci.text)
                lvdsN = re.sub(r"^(P\d+)_(\d+)_\d+$", r"\1_\2", first_ci.text)

                # Process each concept name
                for cn_elem in driver.findall(
                    './*[local-name()="ConceptName"]'
                ):  # TODO: finish checking this block. check .text is not None!!!
                    outname = cn_elem.text
                    for port in nets:
                        if (
                            port.tag != "port"
                            or not port.find('./*[local-name()="IsDriver"]')
                            or port.find('./*[local-name()="IsDriver"]').text != "False"
                        ):
                            continue

                        sink = port
                        sink_ci = sink.find(
                            './*[local-name()="ConceptInstanceName"]'
                        ).text.replace(".", "_")
                        #  in xslt logic we comnbine results of both names and take the first one
                        #  it looks like one of them is always None, so we take the other one
                        sink_cn = (
                            sink.find('./*[local-name()="ConceptName"]')
                            or sink.find('./*[local-name()="Name"]')
                        ).text

                        allnames = normalize_concept_names(sink_ci, sink_cn)
                        allnames_cn = [n.get("cn") for n in allnames]
                        joined_string = "|".join(
                            ["." + name + "." for name in allnames_cn]
                        )

                        for name_pair in allnames:
                            cn = name_pair.get("cn")
                            if (
                                lvds_rx and not cn.endswith("P") or cn.endswith("N")
                            ) or (
                                not lvds_rx
                                and cn.endswith("P")
                                or cn.endswith("N")
                                and f"|{cn[:-1]}|" in f"|{joined_string}|"
                            ):
                                continue
                            else:
                                net2 = ET.Element("net2")

                                # Create in element
                                in_elem = ET.SubElement(net2, "in")
                                ET.SubElement(in_elem, "ConceptInstanceName").text = (
                                    name_pair.get("ci")
                                )
                                ET.SubElement(in_elem, "ConceptName").text = (
                                    name_pair.get("cn")
                                )

                                # Create out element
                                out_elem = ET.SubElement(net2, "out")
                                out_ci = ET.SubElement(out_elem, "ConceptInstanceName")
                                out_ci.text = (
                                    lvdsN if lvds_rx and cn.endswith("N") else lvdsP
                                )
                                ET.SubElement(out_elem, "ConceptName").text = re.sub(
                                    r"^OUT.*$", "OUT", outname
                                )

                                connects.append(net2)

        elif len(driver_sockets) >= 2:
            driver = []
            for socket in driver_sockets:
                # Get ConceptInstanceName and ConceptName/Name
                ci_elem = socket.find('./*[local-name()="ConceptInstanceName"]')
                cn_elem = socket.find('./*[local-name()="ConceptName"]')
                name_elem = socket.find('./*[local-name()="Name"]')

                if ci_elem is None or (cn_elem is None and name_elem is None):
                    continue

                ci = ci_elem.text.replace(".", "_")
                cn = cn_elem.text if cn_elem is not None else name_elem.text

                # Create socket element
                socket_elem = ET.Element("socket")
                for item in normalize_concept_names(ci, cn):
                    socket_elem.append(item)
                driver.append(socket_elem)

            for outer in driver[0]:
                for item in driver[0][1:]:

                    net2_1 = ET.Element("net2", {"socket": "1"})
                    # Create in element
                    in_elem = ET.SubElement(net2_1, "in")
                    ET.SubElement(in_elem, "ConceptInstanceName").text = item.get("ci")
                    ET.SubElement(in_elem, "ConceptName").text = item.get("cn") + "_in"
                    # Create out element
                    out_elem = ET.SubElement(net2_1, "out")
                    ET.SubElement(out_elem, "ConceptInstanceName").text = outer.get(
                        "ci"
                    )
                    ET.SubElement(out_elem, "ConceptName").text = outer.get("cn")
                    connects.append(net2_1)

                    net2_2 = ET.Element("net2", {"socket": "1"})
                    # Create in element
                    in_elem = ET.SubElement(net2_2, "in")
                    ET.SubElement(in_elem, "ConceptInstanceName").text = outer.get("ci")
                    ET.SubElement(in_elem, "ConceptName").text = outer.get("cn") + "_in"
                    # Create out element
                    out_elem = ET.SubElement(net2_2, "out")
                    ET.SubElement(out_elem, "ConceptInstanceName").text = item.get("ci")
                    ET.SubElement(out_elem, "ConceptName").text = item.get("cn")
                    connects.append(net2_2)

    return connects


def normalize_concept_names(
    con_i: str, con_name: str
) -> list:  # TODO: check return list, mb it's good idea to add res[] to recursive calls
    if "|" in con_i:  # legacy COX format
        res = []
        for token in con_i.split("|"):
            if ":" in token:
                res.append(
                    ET.Element(
                        "pair", {"ci": token.split(":")[0], "cn": token.split(":")[1]}
                    )
                )
            else:
                res.extend(normalize_concept_names(token, con_name))
        return res
    elif "=(" in con_name:  # socket member is array
        if ";" in con_name and len(con_name.split(";")[0]) < len(
            con_name.split("=(")[0]
        ):
            res = []
            res.extend(normalize_concept_names(con_i, con_name.split(";")[0]))
            res.extend(normalize_concept_names(con_i, con_name.split(";")[1]))
            return res
        elif ";" in con_name.split(")")[1]:
            res = []
            res.extend(normalize_concept_names(con_i, re.sub(r"\).*$", ")", con_name)))
            res.extend(
                normalize_concept_names(con_i, re.sub(r"^.*\)\s*;", "", con_name))
            )
            return res
        else:
            res = []
            member = con_name.split("=(")[0]
            for token in re.sub(r"^.+?=\((.*)\)$", r"\1", con_name).split(";"):
                for current_item in normalize_concept_names(con_i, token):
                    if "=" in current_item.get("cn"):
                        res.append(
                            ET.Element(
                                "pair",
                                {
                                    "ci": current_item.get("ci"),
                                    "cn": f"{member}[{re.sub(r'=', ']=', current_item.get('cn'))}",
                                },
                            )
                        )
                    else:
                        res.append(
                            ET.Element(
                                "pair",
                                {
                                    "ci": current_item.get("ci"),
                                    "cn": f"{member}={current_item.get('cn')}",
                                },
                            )
                        )
            return res
    elif ";" in con_name:  # members
        res = []
        res.extend(normalize_concept_names(con_i, con_name.split(";")[0]))
        res.extend(normalize_concept_names(con_i, con_name.split(";")[1]))
        return res
    elif "=" in con_name:  # array
        res = []
        range = con_name.split("=")[0]
        for current_item in normalize_concept_names(con_i, con_name.split("=")[1]):
            res.append(
                ET.Element(
                    "pair",
                    {
                        "ci": current_item.get("ci"),
                        "cn": f"{range}={current_item.get('cn')}",
                    },
                )
            )
        return res
    elif "|" in con_name:  # alias
        res = []
        for token in con_name.split("|"):
            if ":" in token:
                res.append(
                    ET.Element(
                        "pair", {"ci": token.split(":")[0], "cn": token.split(":")[1]}
                    )
                )
            else:
                res.append(ET.Element("pair", {"ci": con_i, "cn": token}))
        return res
    # return list bc in other blocks res-s are extended, so we need iterable elements
    if ":" in con_i:  # legacy COX format
        return [
            ET.Element("pair", {"ci": con_i.split(":")[0], "cn": con_i.split(":")[1]})
        ]
    elif ":" in con_name:  # ignore COX CI
        return [
            ET.Element(
                "pair", {"ci": con_name.split(":")[0], "cn": con_name.split(":")[1]}
            )
        ]
    else:
        return [ET.Element("pair", {"ci": con_i, "cn": con_name})]


def calc_formulas(input_str: str) -> str:
    # Split the input string into matching and non-matching parts
    parts = []
    current_pos = 0

    for match in re.finditer(r"\{{.*?\}}", input_str):
        # Add any text before the match
        if match.start() > current_pos:
            parts.append(input_str[current_pos : match.start()])

        # Process the matched part
        parts.append(evaluate(match.group(0)[2:-2].strip()))
        current_pos = match.end()

    # Add any remaining text after the last match
    if current_pos < len(input_str):
        parts.append(input_str[current_pos:])

    # Join all parts together
    return "".join(parts)


def enumerate_parameter(range_str: str, context: str) -> list:
    result = []
    for token in range_str.split(','):
        toks = token.split(':')

        if len(toks) > 2:
            raise ValueError(f"Illegal range spec {range_str} in {context}")
        elif len(toks) < 2:
            result.append(evaluate(toks[0]))
        else:
            end = int(evaluate(toks[0]))
            start = int(evaluate(toks[1]))
            
            if start < end:
                result.extend([str(i) for i in range(start, end + 1)])
            else:
                result.extend([str(i) for i in range(end, start + 1)])

    return result


def is_built(raw_inst: str, para_maps2: ET.Element) -> bool:
    return len(para_maps2.findall(f".//*[local-name()='{raw_inst}']")) != 0


def calc_hidden(par_name: str, context: str, para_maps2: ET.Element) -> bool:
    key = re.sub(r'^\$\{(.*)\}$', r'\1', par_name)
    if para_maps2.findall(f".//*[local-name()='{context}:{key}']"):  # parameter existence check: Return its Hidden attribute
        pars = para_maps2.findall(f".//*[local-name()='{context}:{key}']")
        par = str(any(par.get('Hidden') for par in pars if par.get('Hidden') is not None))
        return boolean_essence(par, context) != 0
    else:  # Return True if formula evaluates to non-zero
        par = re.sub(r'&amp;gt;', '>', re.sub(r'&amp;lt;', '<', par_name))
        return boolean_essence(par, context) != 0


def boolean_essence(input_str: str, context: str = '0') -> int:
    return int(num_essence(parse_essence(input_str), context))


def name2Driver(rawname: str, iomode: str) -> list:
    dummy = ET.Element('out')
    if rawname.match(r'^suppress_[^_]+_\d+_'):
        ET.SubElement(dummy, 'ConceptInstanceName').text = re.sub(r'^suppress_([^_]+_\d+)_.*$', r'\1', rawname)
        ET.SubElement(dummy, 'ConceptName').text = re.sub(r'^suppress_[^_]+_\d+_(.*)$', r'suppress_\1', rawname)
    elif rawname.match(r'^suppress_[^_]+_'):
        ET.SubElement(dummy, 'ConceptInstanceName').text = re.sub(r'^suppress_([^_]+)_.*$', r'\1', rawname)
        ET.SubElement(dummy, 'ConceptName').text = re.sub(r'^suppress_[^_]+_(.*)$', r'suppress_\1', rawname)
    elif rawname.match(r'^[^_]+_\d+_'):
        ET.SubElement(dummy, 'ConceptInstanceName').text = re.sub(r'^([^_]+_\d+)_.*$', r'\1', rawname)
        ET.SubElement(dummy, 'ConceptName').text = re.sub(r'^[^_]+_\d+_(.*)$', r'\1', rawname)
    elif rawname.match(r'^[^_]+_'):
        ET.SubElement(dummy, 'ConceptInstanceName').text = rawname.split('_')[0]
        ET.SubElement(dummy, 'ConceptName').text = rawname.split('_')[1]
    elif rawname.match(r'^TDO$'):
        ET.SubElement(dummy, 'ConceptInstanceName').text = 'TCU'
        ET.SubElement(dummy, 'ConceptName').text = rawname
    elif rawname.match(r'^DAP\d+$'):
        ET.SubElement(dummy, 'ConceptInstanceName').text = 'TCU'
        ET.SubElement(dummy, 'ConceptName').text = rawname.lower()
    elif rawname.match(r'^DAPE\d+$'):  # Patch for A2G: DAPE_ED output via dedicated pin only!
        prefix = 'suppress_' if iomode != 'DEDICATED' else ''
        ET.SubElement(dummy, 'ConceptInstanceName').text = prefix + 'DAPE_1'
        ET.SubElement(dummy, 'ConceptName').text = prefix + re.sub(r'DAPE(\d+)$', r'DAP\1', rawname)
    elif rawname.match(r'^XTAL\d+$', re.IGNORECASE):
        ET.SubElement(dummy, 'ConceptInstanceName').text = 'CCU'
        ET.SubElement(dummy, 'ConceptName').text = rawname.upper()
    else:
        ET.SubElement(dummy, 'ConceptInstanceName').text = 'OCDS'
        ET.SubElement(dummy, 'ConceptName').text = rawname

    outputname = resolve_names(dummy)
    result = []
    for i in range(0, len(outputname) - 1, 2):
        port_ref = ET.Element('internalPortReference')
        port_ref.set('spirit:componentRef', outputname[i])
        port_ref.set('spirit:portRef', outputname[i + 1])
        result.append(port_ref)
        
    return result


def resolve_names(net: list) -> list:  # net is list of Connects/in or Connects/out
    pass


def str2index(name: str) -> str:
    sub_str = re.sub(r'^.+(\D)$', r'\1', name).upper()
    alf = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'  # modified alfabet: add symbols from Q to Z
    ix = alf.index(sub_str) if sub_str in alf else -1
    return str(ix)


def str2dec(in_str: str) -> int:  # modified to prevent recursion
    result = 0
    for char in in_str:
        result = result * 10 + int(char)
    return result


def make_socket_nets(net: ET.Element, instance1: ET.Element, instance2: ET.Element) -> list:
    socket_nets = []  # return list of nets
    in_name = re.sub(r'(.*?)_in', r'\1', net.find('./*[local-name()="in"]/*[local-name()="ConceptName"]/text()'))
    for elem_1 in instance1.findall(f'./*[local-name()="Socket" and @Name={in_name}]'):
        for in_item in elem_1.findall('./*[local-name()="Member" and ./[local-name()="Direction"]/text()="in"]'):
            in_port = in_item
            in_bits = []
            if in_item.find('./*[local-name()="Vector"]'):
                nl = evaluate(in_item.find('./*[local-name()="Vector"]/*[local-name()="Left"]/text()'))
                nr = evaluate(in_item.find('./*[local-name()="Vector"]/*[local-name()="Right"]/text()'))
                if str_to_number(nl) < str_to_number(nr):
                    in_bits.extend([i for i in range(int(nl), int(nr) + 1)])
                else:
                    in_bits.extend([i for i in range(int(nr), int(nl) + 1)])
            wire = in_item.get('wire')
            for elem_2 in instance2.findall(f'./*[local-name()="Socket" and @Name={net.find("./*[local-name()='out']/*[local-name()='ConceptName']/text()")}]'):
                for out_item in elem_2.findall(f'./*[local-name()="Member" and @wire={wire}]'):
                    out_port = out_item
                    out_bits = []
                    if out_item.find('./*[local-name()="Vector"]'):
                        nl = evaluate(out_item.find('./*[local-name()="Vector"]/*[local-name()="Left"]/text()'))
                        nr = evaluate(out_item.find('./*[local-name()="Vector"]/*[local-name()="Right"]/text()'))
                        if str_to_number(nl) < str_to_number(nr):
                            out_bits.extend([i for i in range(int(nl), int(nr) + 1)])
                        else:
                            out_bits.extend([i for i in range(int(nr), int(nl) + 1)])
                    if len(in_bits):
                        for k in range(len(in_bits)):
                            subnet = ET.Element('Net')
                            in_elem = ET.SubElement(subnet, 'in')
                            ET.SubElement(in_elem, 'ConceptInstanceName').text = instance1.get('Int_Class_ID')
                            ET.SubElement(in_elem, 'ConceptName').text = f'{in_port.text.strip()}_{in_bits[k]}'

                            out_elem = ET.SubElement(subnet, 'out')
                            ET.SubElement(out_elem, 'ConceptInstanceName').text = instance2.get('Int_Class_ID')
                            str_join = f"_{out_bits[k]}" if len(out_bits) > k else ""
                            ET.SubElement(out_elem, 'ConceptName').text = f'{out_port.text.strip()}{str_join}'

                            socket_nets.extend(make_net(subnet, instance1))
                    else:
                        subnet = ET.Element('Net')
                        in_elem = ET.SubElement(subnet, 'in')
                        ET.SubElement(in_elem, 'ConceptInstanceName').text = instance1.get('Int_Class_ID')
                        ET.SubElement(in_elem, 'ConceptName').text = in_port.text.strip()

                        out_elem = ET.SubElement(subnet, 'out')
                        ET.SubElement(out_elem, 'ConceptInstanceName').text = instance2.get('Int_Class_ID')
                        str_join = f"_{out_bits[k]}" if len(out_bits) > 0 else ""
                        ET.SubElement(out_elem, 'ConceptName').text = f'{out_port.text.strip()}{str_join}'

                        socket_nets.extend(make_net(subnet, instance1))
    return socket_nets
                    
           
#  elaborate one global sideband interconnect
def make_net(net: ET.Element, instance: ET.Element) -> list:
    in_name = resolve_names(net.findall('./*[local-name()="in"]'), instance)  # list of broadcast receivers
    out_name = resolve_names(net.findall('./*[local-name()="out"]'))  # mutex controlled list of drivers
    result = []
    for i in range(0, len(in_name), 2):
        adHocConnection = ET.Element('spirit:adHocConnection')
        ET.SubElement(adHocConnection, 'spirit:name').text = f"{in_name[i]}_{in_name[i+1]}"
        ci_out = net.find('./*[local-name()="out"]/*[local-name()="ConceptInstanceName"]/text()')
        cn_out = net.find('./*[local-name()="out"]/*[local-name()="ConceptName"]/text()')
        ci_in = net.find('./*[local-name()="in"]/*[local-name()="ConceptInstanceName"]/text()')
        cn_in = net.find('./*[local-name()="in"]/*[local-name()="ConceptName"]/text()')
        ET.SubElement(adHocConnection, 'spirit:description').text = f"{ci_out}_{cn_out}__{ci_in}_{cn_in}"
        ET.SubElement(adHocConnection, 'spirit:internalPortReference', 
                      {'spirit:componentRef': in_name[i], 'spirit:portRef': in_name[i+1]})
        for j in range(0, len(out_name), 2):
            ET.SubElement(adHocConnection, 'spirit:internalPortReference', 
                          {'spirit:componentRef': out_name[j], 'spirit:portRef': out_name[j+1]})
        result.append(adHocConnection)

    return result


#  elaborate a potentially loop'ed local interconnect definition
def make_net_instance(template: ET.Element, instance: ET.Element) -> list:
    context = instance.get('Int_Class_ID')
    result = []
    
    non_hidden_attrs = [attr for attr in template.attrib if attr != 'Hidden']
    if non_hidden_attrs:
        first_attr = non_hidden_attrs[0]
        dims = enumerate_parameter(resolve_parameter(template.get(first_attr), [], context), context)
        
        for dim in dims:
            variant = ET.Element(template.tag)
            
            for attr in non_hidden_attrs[1:]:
                variant.set(attr, template.get(attr))
            
            #  TODO: finish this block (828-831 spec2spirit.xslt)
            
            result.extend(make_net_instance(variant, instance))
        return result
    
    # Check for Hidden attribute with ${...} pattern
    elif ('Hidden' in template.attrib and re.match(r'^\$\{(.*?)\}$', template.get('Hidden'))
          and calc_hidden(template.get('Hidden'), context)):
        return result
    
    # Check for Hidden attribute without ${...} pattern
    elif 'Hidden' in template.attrib and not re.match(r'^\$\{(.*?)\}$', template.get('Hidden')):
        resolved_hidden = resolve_parameter(template.get('Hidden'), [], context)
        if calc_hidden(resolved_hidden, context):
            return result
    
    else:
        # mutex controlled list of inputs and outputs
        input_names = resolve_names(template.findall('./*[local-name()="in"]'), instance)
        output_names = resolve_names(template.findall('./*[local-name()="out"]'), instance)
        
        if input_names and output_names:
            connection = ET.Element('spirit:adHocConnection')
            
            name_elem = ET.SubElement(connection, 'spirit:name')
            name_elem.text = f"{input_names[0]}_{input_names[1]}"
            
            desc_elem = ET.SubElement(connection, 'spirit:description')
            desc_elem.text = f"{output_names[0]}_{output_names[1]}__{input_names[0]}_{input_names[1]}"
            
            # Add internal port references for inputs
            for i in range(0, len(input_names), 2):
                port_ref = ET.SubElement(connection, 'spirit:internalPortReference')
                port_ref.set('spirit:componentRef', input_names[i])
                port_ref.set('spirit:portRef', input_names[i + 1])
            
            # Add internal port references for outputs
            for i in range(0, len(output_names), 2):
                port_ref = ET.SubElement(connection, 'spirit:internalPortReference')
                port_ref.set('spirit:componentRef', output_names[i])
                port_ref.set('spirit:portRef', output_names[i + 1])
            
            result.append(connection)
    
    return result


def resolve_parameter(in_str: str, keep: list, context: str = '0') -> str:
    if '${' not in in_str:
        return in_str
        
    key = in_str.split('${', 1)[1]
    t1 = key.split('}', 1)[0]
    t2 = key.split('"', 1)[0] if '"' in key else ''
    t3 = key.split('${', 1)[0] if '${' in key else ''
    para = []
    #  creating variable 'para'
    if key.startswith('"'):
        t30 = key[1:]
        t40 = t30.split('"', 1)[0]
        t50 = t30.split('"', 1)[1] if '"' in t30 else ''
        if '}' in t50:
            t60 = t50.split('}', 1)[0]
            para.append(f'"{t40}"{t60}')
            if len(t50.split('}', 1)[1]):
                para.append(resolve_parameter(t50.split('}', 1)[1], keep, context))
    elif t2 and len(t2) < len(t1):
        t30 = key.split('"', 1)[1]
        t40 = t30.split('"', 1)[0]
        t50 = t30.split('"', 1)[1] if '"' in t30 else ''
        t60 = t50.split('}', 1)[0] if '}' in t50 else ''
        para.append(f'"{t40}"{t60}')
        para.append(f'{t2}"{t40}"{t60}')
        if len(t50.split('}', 1)[1]):
            para.append(resolve_parameter(t50.split('}', 1)[1], keep, context))
    elif not key:
        para.append('${')
    elif ('${' in key and len(t3) < len(t1)) or '$' in t1:
        para.append('${')
        para.append(resolve_parameter(key, keep, context))
    else:
        para.append(t1)
        if len(key.split('}', 1)[1]):
            para.append(resolve_parameter(key.split('}', 1)[1], keep, context))
    
    #  choosing result parameters
    if not para[0]:  # left half of nested expression
        return in_str
    elif para[0] == keep or '$' in para[0] or '+' in para[0]:
        return in_str.split('${', 1)[0] + ''.join(para)
    elif para[0] in ('"{"', '"}"'):
        return in_str.split('${', 1)[0] + para[0][1] + para[1]
    else:
        p = get_parameter(para[0], context).replace('"', '')
        q = p.replace("'", '')
        r = q.replace('&amp;', '&')
        return in_str.split('${', 1)[0] + r + (para[1] if len(para) > 1 else '')
    

# elaborate a potentially loop'ed port mapping definition
# template - Map element
def looped_name(template: ET.Element, context: str, ci: str, cn: str) -> list:
    result = []
    
    # Check if template has attributes other than 'Name' and 'Hidden'
    other_attrs = [attr for attr in template.attrib.keys() 
                   if attr not in ['Name', 'Hidden']]
    
    if other_attrs:
        first_attr = other_attrs[0]
        # Get dimensions by resolving parameter and enumerating
        dims = enumerate_parameter(resolve_parameter(template.get(first_attr), [], context), context)
        
        for dim in dims:
            variant = ET.Element(template.tag)
            # Copy remaining attributes
            for attr in other_attrs[1:]:
                variant.set(attr, template.get(attr))
            # Copy Name attribute if exists
            if 'Name' in template.attrib:
                variant.set('Name', template.get('Name'))
            
            #  TODO: template call (609-612 spec2spirit.xslt)
            
            result.extend(looped_name(variant, context, ci, cn))
            
    elif 'Hidden' in template.attrib:
        hidden_value = template.get('Hidden')  # variable MapHidden
        
        #  Process special cases with #lastletter# and #prelastletter#
        if '#' in hidden_value:
            last_letter = ord(cn[-1].upper()) - ord('A')
            pre_last_letter = ord(cn[-2].upper()) - ord('A') if len(cn) > 1 else -1
            
            hidden_value = hidden_value.replace('#lastletter#', str(last_letter))
            hidden_value = hidden_value.replace('#prelastletter#', str(pre_last_letter))
        
        #  Hidden refers to a single parameter name
        #  Hidden refers to the port name
        if (re.match(r'^\$\{(.*?)\}$', hidden_value) and calc_hidden(hidden_value, context)) or \
           (not re.match(r'^\$\{(.*?)\}$', hidden_value) and 
            calc_hidden(cn.replace(template.get('Name'), resolve_parameter(hidden_value, [], context)), context)):
            pass  # using pass bc no loop
        else:
            #  Create variant without Hidden attribute
            variant = ET.Element(template.tag)
            for attr in template.attrib:
                if attr != 'Hidden':
                    variant.set(attr, template.get(attr))
            for child in template:
                variant.append(child)
            
            result.extend(looped_name(variant, context, ci, cn))
            
    # Handle ConceptInstanceName and ConceptName cases
    else:
        nci = None
        ncn = None
        
        # Process ConceptInstanceName
        concept_instance = template.find('ConceptInstanceName')
        if concept_instance is not None:
            text = concept_instance.text
            if '#lastdigit#' in text:
                last_digit = ci[-1]
                if castable(last_digit, 'integer'):
                    nci = calc_formulas(cn.replace(template.get('Name'), 
                        resolve_parameter(text.replace('#lastdigit#', last_digit), [], context)))
            else:
                nci = calc_formulas(cn.replace(template.get('Name'), 
                    resolve_parameter(text, [], context)))
        
        # Process ConceptName
        concept_name = template.find('ConceptName')
        if concept_name is not None:
            text = concept_name.text
            if '#lastletter#' in text:
                last_letter = ord(cn[-1].upper()) - ord('A')
                if last_letter >= 0:
                    ncn = calc_formulas(cn.replace(template.get('Name'), 
                        resolve_parameter(text.replace('#lastletter#', str(last_letter)), [], context)))
            elif '#prelastletter#' in text:
                pre_last_letter = ord(cn[-2].upper()) - ord('A') if len(cn) > 1 else -1
                if pre_last_letter >= 0:
                    ncn = calc_formulas(cn.replace(template.get('Name'), 
                        resolve_parameter(text.replace('#prelastletter#', str(pre_last_letter)), [], context)))
            else:
                ncn = calc_formulas(cn.replace(template.get('Name'), 
                    resolve_parameter(text, [], context)))
        
        # Add results if both nci and ncn are valid
        if nci and ncn:
            result.extend([nci, ncn])
    
    return result


#  elaborate a potentially loop'ed port constraint
#  template - Map element
def looped_constraint(template: ET.Element, context: str) -> list:
    result = []
    
    if template.attrib:
        # Get the first attribute's name and value
        first_attr = list(template.attrib.keys())[0]
        first_attr_value = template.get(first_attr)
        
        dims = enumerate_parameter(resolve_parameter(first_attr_value, [], context), context)
        for dim in dims:
            variant = ET.Element(template.tag)
            
            # Copy remaining attributes (excluding the first one)
            for attr in list(template.attrib.keys())[1:]:
                variant.set(attr, template.get(attr))
            
            #  TODO: template call (799-802 spec2spirit.xslt)
            
            result.extend(looped_constraint(variant, context))
            
    else:
        #  TODO: template call (809-812 spec2spirit.xslt)
        pass

    return result


#  elaborate a potentially loop'ed resource instance definition
def make_resource_instance(template: ET.Element, context: str) -> list:
    result = []
    
    # Check for non-Hidden attributes
    non_hidden_attrs = [attr for attr in template.attrib if attr != 'Hidden']
    if non_hidden_attrs:
        first_attr = non_hidden_attrs[0]
        dims = enumerate_parameter(resolve_parameter(template.get(first_attr), [], context), context)
        
        for dim in dims:
            variant = ET.Element(template.tag)
            # Copy remaining non-Hidden attributes
            for attr in non_hidden_attrs[1:]:
                variant.set(attr, template.get(attr))
            
            #  TODO: template call (750-753 spec2spirit.xslt)
            
            result.extend(make_resource_instance(variant, context))
            
    # Handle Hidden attribute cases
    elif 'Hidden' in template.attrib:
        hidden_value = template.get('Hidden')
        # Skip if Hidden is a parameter reference and evaluates to true
        if (re.match(r'^\$\{(.*?)\}$', hidden_value) and calc_hidden(hidden_value, context)) or \
           (not re.match(r'^\$\{(.*?)\}$', hidden_value) and 
            calc_hidden(resolve_parameter(hidden_value, [], context), context)):
            return result
            
    # Create component instance
    else:
        instance = ET.Element('spirit:componentInstance')
        
        # Set instance name
        name_elem = ET.SubElement(instance, 'spirit:instanceName')
        cin = template.find('ConceptInstanceName')
        if cin is not None and cin.text:
            name_elem.text = calc_formulas(resolve_parameter(cin.text, [], context))
        
        # Set component reference
        VLNV = template.find('VLNV')
        if VLNV is not None and VLNV.text:
            vendor, library, name, version = VLNV.text.split(':')
            comp_ref = ET.SubElement(instance, 'spirit:componentRef')
            comp_ref.set('spirit:vendor', vendor)
            comp_ref.set('spirit:library', library)
            comp_ref.set('spirit:name', name)
            comp_ref.set('spirit:version', version)
        
        param_decls = template.findall('ParamDecl')
        if param_decls:
            config_values = ET.SubElement(instance, 'spirit:configurableElementValues')
            for param in param_decls:
                value_elem = ET.SubElement(config_values, 'spirit:configurableElementValue')
                value_elem.set('spirit:referenceId', param.get('Name'))
                value = param.find('Value')
                if value is not None and value.text:
                    value_elem.text = calc_formulas(resolve_parameter(value.text, [], context))
        
        constraints = template.findall('Constraint')
        if constraints:
            vendor_ext = ET.SubElement(instance, 'spirit:vendorExtensions')
            for constraint in constraints:
                vendor_ext.extend(looped_constraint(constraint, context))
        
        result.append(instance)
    
    return result


#  Generate a complete XMP-wrapped set of metadata using the Dublin Core semanics
def template_MetaData(device: str, family: str, created: str, outputfile: str, silicon_name: str, label: str) -> ET.Element:
    # Define namespace mappings
    namespaces = {
        'x': 'adobe:ns:meta/',
        'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
        'dc': 'http://purl.org/dc/elements/1.1/',
        'xml': 'http://www.w3.org/XML/1998/namespace'
    }
    
    # Register namespaces for proper serialization
    for prefix, uri in namespaces.items():
        ET.register_namespace(prefix, uri)
    
    # Create root element with processing instructions
    root = ET.Element('{adobe:ns:meta/}xmpmeta')
    root.insert(0, ET.ProcessingInstruction('xpacket', 'begin="" id="W5M0MpCehiHzreSzNTczkc9d"'))
    
    # Create RDF element with namespaces
    rdf = ET.SubElement(root, '{http://www.w3.org/1999/02/22-rdf-syntax-ns#}RDF')
    rdf.set('xmlns:rdf', namespaces['rdf'])
    rdf.set('xmlns:dc', namespaces['dc'])
    
    # Create Description element
    desc = ET.SubElement(rdf, '{http://www.w3.org/1999/02/22-rdf-syntax-ns#}Description')
    desc.set('{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about', '')
    
    # Helper function to create elements with proper namespaces
    def create_element(parent, tag, text=None, lang=None):
        elem = ET.SubElement(parent, f'{{{namespaces[tag.split(":")[0]]}}}{tag.split(":")[1]}')
        if text:
            elem.text = text
        if lang:
            elem.set(f'{{{namespaces["xml"]}}}lang', lang)
        return elem
    
    # Title
    dc_title = create_element(desc, 'dc:title')
    rdf_Alt = create_element(dc_title, 'rdf:Alt')
    create_element(rdf_Alt, 'rdf:li', f"{device} On-chip Connectivity Definitions", 'en')
    
    # Creator
    dc_creator = create_element(desc, 'dc:creator')
    rdf_Seq = create_element(dc_creator, 'rdf:Seq')
    create_element(rdf_Seq, 'rdf:li', "CTDD@infineon.com")
    
    # Subject
    dc_subject = create_element(desc, 'dc:subject')
    rdf_Bag = create_element(dc_subject, 'rdf:Bag')
    for text in [device, family, "Resource modelling", "Resource mapping", "SPIRIT"]:
        create_element(rdf_Bag, 'rdf:li', text)
    
    # Description
    dc_description = create_element(desc, 'dc:description')
    rdf_Alt = create_element(dc_description, 'rdf:Alt')
    create_element(rdf_Alt, 'rdf:li', 
                  "SPIRIT (IEEE Std 1685-2009) compliant definition of connectivity.", 'en')
    
    # Publisher
    create_element(desc, 'dc:publisher', "http://www.infineon.com")
    
    # Contributor
    dc_contributor = create_element(desc, 'dc:contributor')
    rdf_Seq = create_element(dc_contributor, 'rdf:Seq')
    create_element(rdf_Seq, 'rdf:li', "IFX ATV MC ACE")
    
    # Date
    # don't use  xsi:type="dcterms:W3CDTF"
    create_element(desc, 'dc:date', created)
    
    # Type
    # don't use  xsi:type="dcterms:DCMIType"
    create_element(desc, 'dc:type', "Dataset")
    
    # Format
    create_element(desc, 'dc:format', "application/xml")
    
    # Identifier
    create_element(desc, 'dc:identifier', outputfile.replace('_raw', ''))
    
    # Source
    create_element(desc, 'dc:source', f"{silicon_name}.spinner@@{label}")
    
    # Language
    dc_language = create_element(desc, 'dc:language')
    rdf_Bag = create_element(dc_language, 'rdf:Bag')
    create_element(rdf_Bag, 'rdf:li', "en")
    
    # Relation
    dc_relation = create_element(desc, 'dc:relation')
    rdf_Bag = create_element(dc_relation, 'rdf:Bag')
    create_element(rdf_Bag, 'rdf:li', f"{device} Data Sheet")
    
    # Coverage
    dc_coverage = create_element(desc, 'dc:coverage')
    rdf_Alt = create_element(dc_coverage, 'rdf:Alt')
    create_element(rdf_Alt, 'rdf:li', 
                  """Legal Disclaimer: 
The information given in this document shall in no event be regarded as a guarantee of conditions or
characteristics. With respect to any examples or hints given herein, any typical values stated herein and/or any
information regarding the application of the device, Infineon Technologies hereby disclaims any and all warranties
and liabilities of any kind, including without limitation, warranties of non-infringement of intellectual property rights
of any third party.""", 'en')
    
    # Rights
    dc_rights = create_element(desc, 'dc:rights')
    rdf_Alt = create_element(dc_rights, 'rdf:Alt')
    create_element(rdf_Alt, 'rdf:li', 
                  "Copyright 2013 Infineon Technologies AG. All Rights Reserved", 'en')
    
    # Add end processing instruction
    root.append(ET.ProcessingInstruction('xpacket', 'end="w"'))
    
    return root


def format_dateTime(dt: datetime, format_str: str) -> str:
    """
    Format datetime according to XSLT-like format string.
    Matches XSLT format-dateTime functionality.
    """
    # Convert XSLT format to Python strftime format
    format_map = {
        '[Y0001]': '%Y',  # Year with century
        '[M01]': '%m',    # Month with leading zero
        '[D01]': '%d',    # Day with leading zero
        '[H01]': '%H',    # Hour (24h) with leading zero
        '[m01]': '%M',    # Minute with leading zero
        '[s01]': '%S',    # Second with leading zero
        'Z': 'Z'          # UTC timezone indicator
    }
    
    python_format = format_str
    for xslt, py in format_map.items():
        python_format = python_format.replace(xslt, py)
    
    return dt.strftime(python_format)


def adjust_dateTime_to_timezone(dt: datetime, duration: timedelta) -> datetime:
    """
    Adjust datetime to specified timezone.
    Matches XSLT adjust-dateTime-to-timezone functionality.
    """
    # For PT0H (UTC), we just return the datetime as is
    return dt


def current_dateTime() -> datetime:
    """
    Get current datetime in UTC.
    Matches XSLT current-dateTime functionality.
    """
    return datetime.now(timezone.utc)


def dayTimeDuration(duration_str: str) -> timedelta:
    """
    Convert XSLT duration string to Python timedelta.
    Matches XSLT xs:dayTimeDuration functionality.
    """
    # Parse PT0H format (Period Time 0 Hours)
    if duration_str.startswith('PT'):
        hours = int(duration_str[2:-1])
        return timedelta(hours=hours)
    return timedelta(0)


def get_silicon_name(root: ET.Element) -> str:
    """
    Get silicon name from XML structure.
    Matches XSLT path: //spinner5PBuilder/properties/property[@name='chip_top_name']
    """
    try:
        return root.find('.//spinner5PBuilder/properties/property[@name="chip_top_name"]').text
    except (AttributeError, TypeError):
        return ""


def get_outputfile(device: str) -> str:
    """
    Generate output filename.
    Matches XSLT concat($Device,'_Design_Spirit_raw.xml')
    """
    return f"{device}_Design_Spirit_raw.xml"


def main():
    try:
        # Get current datetime in UTC and format it
        created = format_dateTime(
            adjust_dateTime_to_timezone(
                current_dateTime(),
                dayTimeDuration('PT0H')
            ),
            '[Y0001]-[M01]-[D01]T[H01]:[m01]:[s01]Z'
        )
        
        # Parse input XML to get silicon name
        tree = ET.parse('input.xml')  # You'll need to specify the correct input file
        root = tree.getroot()
        silicon_name = get_silicon_name(root)
        
        # Get device name from somewhere (you'll need to specify how to get this)
        device = "DEVICE_NAME"  # Replace with actual device name source
        outputfile = get_outputfile(device)
        
        # Create metadata
        metadata = template_MetaData(
            device=device,
            family="FAMILY_NAME",  # Replace with actual family name
            created=created,
            outputfile=outputfile,
            silicon_name=silicon_name,
            label="LABEL"  # Replace with actual label
        )
        
        # Write output
        tree = ET.ElementTree(metadata)
        tree.write(outputfile, encoding='utf-8', xml_declaration=True)

    except Exception as e:
        logger.error(f"Conversion failed: {e}")
        raise


if __name__ == "__main__":
    main()
