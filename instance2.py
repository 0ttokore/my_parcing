import os
import xml.etree.ElementTree as ET
import logging
import re
import pandas as pd
from itertools import groupby
import copy
from collections import defaultdict
from xml.dom.minidom import parseString
from typing import List
from decimal import Decimal


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def find_filter(input_file: str, filter: str) -> str:
    if filter:
        return filter

    tree = ET.parse(input_file)
    root = tree.getroot()
    default_silicon = root.find(".//DefaultSilicon")

    return default_silicon.text if default_silicon is not None else ""


def clean_filename(filename: str) -> str:
    cleaned = filename.replace("\\", "/")
    cleaned = re.sub(r"^file:/+(\D:)", r"\1", cleaned)
    cleaned = re.sub(r"^file:/+", "//", cleaned)

    return cleaned


def stuff_digits(version: str) -> str:
    version = re.sub(r"\.(\d)(\.|$)", r".0\1\2", version)
    version = re.sub(r"(\.|V)(\d)(\.|$)", r"\1 0\2\3", version)
    return version


def open_lookup_file(Iproot: str) -> str:
    if not os.path.exists(Iproot):
        print(f"Cannot open file: {Iproot}")
        return pd.DataFrame()
    try:
        tree = ET.parse(Iproot)
        root = tree.getroot()
        namespace = {"": "http://www.infineon.com/RelMgrLookup"}
        data = []
        for path in root.findall(".//path", namespace):
            version = path.get("Version", "")
            locked = path.get("Locked", "")
            release = path.get("Release", "")
            p_type = path.get("type", "")

            for file_elem in path.findall("file", namespace):
                file_path = file_elem.text.strip() if file_elem.text else ""
                key = file_elem.get("key", "")
                level = file_elem.get("level", "")

                data.append(
                    {
                        "path": file_path,
                        "release": release,
                        "locked": locked,
                        "version": version,
                        "level": level,
                        "key": key,
                        "type": p_type,
                    }
                )
        df = pd.DataFrame(
            data,
            columns=["path", "release", "locked", "version", "level", "key", "type"],
        )
        return df
    except ET.ParseError as e:
        print(f"Error parsing XML file {Iproot}: {e}")
        return pd.DataFrame()


def process_df(drive, disc, df):
    df["path"] = df["path"].str.replace("/", "\\")
    df["path"] = df["path"].str.replace(drive, disc)
    df_sorted = df.sort_values(by=["level", "version"], ascending=[True, False])
    df_grouped = df_sorted.groupby(["key", "level"]).head(1).reset_index(drop=True)
    df_grouped["version"] = df_grouped["version"].apply(stuff_digits)
    return df_grouped


def resolve_path(key, subdir, Iproot, filter) -> list:
    if not key.endswith(".xml"):
        key2 = key.replace(":", "_") + ".xml"
    key2 = key2.rstrip("/")
    files = Iproot[Iproot["path"].str.endswith(key)]["path"].tolist()
    files = [os.path.normpath(file) for file in files]
    for file in files:
        try:
            if os.access(file, os.R_OK):
                logger.info(f"File {file} exists and is readable.")
            else:
                logger.warning(f"File {file} exists, but is not readable.")
            with open(file, "r") as f:
                logger.info(f"File {file} opened for reading.")
        except Exception as e:
            logger.error(f"Failed to open file {file}: {e}")
    if subdir:
        subkeys = [i.upper() for i in filter.split("/")]
        matched_keys = []
        dirs = Iproot[Iproot["key"] == key]["path"].tolist()
        for dir in dirs:
            idx = dir.find("\\lnk\\")
            if idx == -1:
                continue
            after_lnk = dir[idx + len("/lnk/") :]
            next_slash = after_lnk.find("\\")
            mykey_str = after_lnk[:next_slash] if next_slash != -1 else after_lnk
            mykeys = mykey_str.upper().split("-") if mykey_str else []
            dir_level = compare_mykeys_subkeys(mykeys, subkeys)
            if dir_level >= 0:
                return dir
    else:
        return dirs


def compare_mykeys_subkeys(mykeys, subkeys):
    if not mykeys:
        return 0
    if len(subkeys) < len(mykeys):
        return -1
    for i in range(len(mykeys)):
        if subkeys[i] != mykeys[i]:
            return -1
    if len(mykeys) == 1:
        return 1
    elif len(mykeys) == 2:
        return 2
    else:
        return 3


def make_key(vlnv):
    try:
        vendor = vlnv.find("Vendor").text if vlnv.find("Vendor") is not None else None
        library = (
            vlnv.find("Library").text if vlnv.find("Library") is not None else None
        )
        name = vlnv.find("Name").text if vlnv.find("Name") is not None else None
        version = (
            vlnv.find("Version").text if vlnv.find("Version") is not None else None
        )

        if vendor is None or library is None or name is None or version is None:
            raise ValueError(
                "ERROR: Missing one or more components in VLNV (Vendor, Library, Name, Version)."
            )

        return f"{vendor}:{library}:{name}:{version}"

    except ValueError as e:
        print(f"Error: {e}")
        return None


def collect_parameters(filterparams, input_file, filter, data):
    tree = ET.parse(input_file)
    root = tree.getroot()

    parameter_maps = root.findall(".//ParameterMap")
    commons = [pm for pm in parameter_maps if pm.find("Name").text not in filterparams]
    default_filters = [
        pm for pm in parameter_maps if pm.find("Name").text in filterparams
    ]

    instances = [
        inst
        for inst in root.findall(".//Instance")
        if inst.find("Silicon") is None
        or any(filter in s.text for s in inst.findall("Silicon"))
    ]

    instance_keys = []
    for instance in instances:
        vlnv_element = instance.find(".//VLNV")
        if vlnv_element is not None:
            key = make_key(vlnv_element)
            instance_keys.append((instance, key))
    save_instance_keys_to_xml(instance_keys, "IPdefs.xml")
    sorted_instance_keys = sorted(instance_keys, key=lambda x: x[1])

    grouped_instances = {}
    for key, group in groupby(sorted_instance_keys, key=lambda x: x[1]):
        grouped_instances[key] = [copy.deepcopy(inst) for inst, _ in group]
    files = []
    for key, group in grouped_instances.items():
        file = resolve_path(key, True, data, filter)
        if file:
            print(transform_parameters(file))

    return files


def save_instance_keys_to_xml(instance_keys, output_file):
    root = ET.Element("Instances")

    for instance, key in instance_keys:
        instance_copy = ET.Element(instance.tag, instance.attrib)

        key_element = ET.SubElement(instance_copy, "Key")
        key_element.text = key

        for child in instance:
            instance_copy.append(child)

        root.append(instance_copy)

    tree = ET.ElementTree(root)
    tree.write(output_file, encoding="utf-8", xml_declaration=True)


# parammaps
def transform_parameters(xml_root):
    tree = ET.parse(xml_root)
    xml_root = tree.getroot()

    parameter_element = ET.Element("parameter", Int_Class_ID="0")

    param_nodes = []

    for param_block in xml_root.findall(".//Component/ParamDeclBlock/ParamDecl"):
        param_nodes.append(param_block)

    for const_block in xml_root.findall(".//Component/ConstDefBlock/ConstDef"):
        param_nodes.append(const_block)

    for generic_block in xml_root.findall(".//Component/GenericDeclBlock/GenericDecl"):
        param_nodes.append(generic_block)

    for param in param_nodes:
        name_element = param.find("Name")
        param_name = name_element.text if name_element is not None else "Unknown"

        new_param = ET.Element(param.tag, Name=param_name)

        for attr_name, attr_value in param.attrib.items():
            new_param.set(attr_name, attr_value)

        for child in param:
            new_param.append(child)

        parameter_element.append(new_param)

    return parameter_element


def parammaps(file_path, grouping_key):
    if not os.path.exists(file_path):
        print(f"Missing component definition: {file_path}")
        return None

    tree = ET.parse(file_path)
    root = tree.getroot()

    root_output = ET.Element("Root")

    parameters = ET.Element("Parameters", key=grouping_key)
    parameters.extend(root.findall(".//ParamDeclBlock/ParamDecl"))
    parameters.extend(root.findall(".//GenericDeclBlock/GenericDecl"))
    root_output.append(parameters)

    interfaces = ET.Element("Interfaces", key=grouping_key)
    interfaces.extend(root.findall(".//Interface"))
    root_output.append(interfaces)

    reg_mem_sets = ET.Element("RegMemSets", key=grouping_key)
    reg_mem_sets.extend(root.findall(".//RegMemSet"))
    root_output.append(reg_mem_sets)

    modes = ET.Element("Modes", key=grouping_key)
    modes.extend(root.findall(".//BitFieldElement/AccessLevel"))
    modes.extend(root.findall(".//BitFieldSequenceElement/AccessLevel"))
    modes.extend(root.findall(".//Interface/AccessCondition"))
    root_output.append(modes)

    return ET.tostring(root_output, encoding="unicode")


def group_instances(xml_path):
    tree = ET.parse(xml_path)
    root = tree.getroot()

    grouped_instances = defaultdict(list)

    for instance in root.findall("Instance"):
        name_element = instance.find("VLNV/Name")
        if name_element is not None:
            name = name_element.text
            grouped_instances[name].append(instance)

    return grouped_instances


def process_document():
    pass


def create_metadata(toolversion, IProot, df, Ipdefs, effectiveFilter, Doc_Author):
    db = ET.Element("DB")
    meta_data = ET.SubElement(db, "MetaData", audience="Internal")
    table = ET.SubElement(
        meta_data,
        "S_Table",
        frame="topbot",
        cols="3",
        colsep="1",
        rowsep="1",
        Type="Normal",
    )
    table.set("cwidths", "1.263in 1.407in 4.230in")

    table_title = ET.SubElement(table, "TableTitle")
    caption = ET.SubElement(table_title, "TCaption")
    caption.text = "Document Level Metadata"

    s_head = ET.SubElement(table, "S_Head")
    s_hrow = ET.SubElement(s_head, "S_HRow", rowsep="1")

    for colname, text in [("1", "Namespace"), ("2", "Property"), ("3", "Value")]:
        s_hcell = ET.SubElement(s_hrow, "S_HCell", colname=colname, hAlign="Normal")
        s_hcell_body = ET.SubElement(s_hcell, "S_HCellBody")
        s_hcell_body.text = text

    s_body = ET.SubElement(table, "S_Body")

    metadata_rows = [
        ("dc", "Creator", Doc_Author),
        ("dc", "Title", "Instance Sheet"),
        ("dc", "Description", f"Instance specifications for silicon {effectiveFilter}"),
        ("xapBJ", "JobRef", clean_filename(IProot)),
    ]

    for ns, prop, value in metadata_rows:
        s_row = ET.SubElement(s_body, "S_Row", rowsep="1")
        for colname, text in [("1", ns), ("2", prop), ("3", value)]:
            s_cell = ET.SubElement(s_row, "S_Cell", colname=colname)
            s_cell_body = ET.SubElement(s_cell, "S_CellBody")
            s_cell_body.text = text

    if not df.empty:
        for item in df["path"]:
            s_row = ET.SubElement(s_body, "S_Row", rowsep="1")
            s_cell1 = ET.SubElement(s_row, "S_Cell", colname="1")
            s_cell1_body = ET.SubElement(s_cell1, "S_CellBody")
            s_cell1_body.text = "ifx"
            s_cell2 = ET.SubElement(s_row, "S_Cell", colname="2")
            s_cell2_body = ET.SubElement(s_cell2, "S_CellBody")
            s_cell2_body.text = "Library"
            s_cell3 = ET.SubElement(s_row, "S_Cell", colname="3")
            s_cell3_body = ET.SubElement(s_cell3, "S_CellBody")
            s_cell3_body.text = clean_filename(item)

    return db


def create_xml(toolversion, IProot, df, Ipdefs, effectiveFilter, Doc_Author):
    root = ET.Element("root")

    comments = [
        "====",
        "© Copyright Infineon Technologies AG 2016. All rights reserved",
        "====",
    ]

    for comment in comments:
        root.append(ET.Comment(comment))
    db = create_metadata(toolversion, IProot, df, Ipdefs, effectiveFilter, Doc_Author)
    root.append(db)
    return ET.tostring(root, encoding="utf-8")


def instance_initialization(input_file, effective_filter, output_file="./instance.xml"):
    tree = ET.parse(input_file)
    root = tree.getroot()

    instances = [
        inst
        for inst in root.findall(".//Instance")
        if (
            inst.find("Silicon") is None
            or any(effective_filter in s.text for s in inst.findall("Silicon"))
        )
        and (
            inst.attrib.get("type") == "VirtualInstance"
            or inst.attrib.get("xsi:type") == "VirtualInstance"
            or inst.attrib.get("type") == "ComponentInstance"
            or inst.attrib.get("xsi:type") == "ComponentInstance"
        )
    ]

    sorted_instances = sorted(
        instances,
        key=lambda inst: (
            (inst.attrib.get("type"), inst.attrib.get("xsi:type")),
            (
                inst.find("ConceptName").text
                if inst.find("ConceptName") is not None
                else ""
            ),
            (
                inst.find("DesignName").text
                if inst.find("DesignName") is not None
                else ""
            ),
        ),
    )

    output_root = ET.Element("Instances")
    for inst in sorted_instances:
        output_root.append(inst)

    tree = ET.ElementTree(output_root)
    tree.write(output_file, encoding="utf-8", xml_declaration=True)
    root = tree.getroot()

    return sorted_instances, root


def get_class_id(root):
    self_values = [
        self_id.text
        for self_id in root.findall(".//Int_Class_ID")
        if self_id.text is not None
    ]
    return self_values


def get_shell(root, effective_filter):
    ref = [
        ciref.find("ComponentInstanceRef").text
        for ciref in root.findall(".//ComponentInstanceReference")
        if (
            ciref.find("Silicon") is None
            or any(effective_filter in s.text for s in ciref.findall("Silicon"))
        )
        and (ciref.find("ComponentInstanceRef") is not None)
    ]

    shell = [
        inst.find("ParameterMap")
        for inst in root.findall(".//Instance")
        if (
            inst.find("Int_Class_ID") is not None
            and inst.find("Int_Class_ID").text in ref
        )
        and inst.find("ParameterMap") is not None
    ]
    return shell


def spec_name(inst):
    if inst.find("ConceptName") is not None:
        return inst.find("ConceptName").text
    if inst.find("DesignName") is None and inst.find("VLNV/Name") is not None:
        return inst.find("VLNV/Name").text
    if inst.find("DesignName") is not None:
        return inst.find("DesignName").text
    else:
        return ""


def get_fileref(inst):
    return make_key(inst.find(".//VLNV")) if inst.find(".//VLNV") is not None else ""


def instance(instances, extracolumns):
    root = ET.Element("Instances")

    for inst in instances:
        new_instance = ET.Element("Instance")

        for attr in ["type", "xsi:type"]:
            if attr in inst.attrib:
                new_instance.set(attr, inst.attrib[attr])

        new_instance.set("InstanceName", spec_name(inst))
        new_instance.set("Essence", get_fileref(inst))

        for ip in inst.findall("InstanceProperty"):
            name_elem = ip.find("Name")
            value_elem = ip.find("Value")

            if name_elem is not None and value_elem is not None:
                name = name_elem.text
                value = value_elem.text

                if f"|{name}|" in extracolumns:
                    new_instance.set(name, value)

        root.append(new_instance)

    xml_bytes = ET.tostring(root, encoding="utf-8")
    dom = parseString(xml_bytes)
    xml_as_string = dom.toprettyxml(indent="  ")

    with open("new_instances.xml", "w", encoding="utf-8") as f:
        f.write(xml_as_string)
    return root


def get_myname_from_root(root):
    short_name = root.find(".//ShortName")
    name = root.find(".//Name")
    ext_vlnv_name = root.find(".//ExtVLNV/Name")
    result = []
    if (
        short_name is not None
        and short_name.text
        and len(re.sub(r"^.?:(.?)\"?$", r"\1", short_name.text)) > 0
    ):
        clean_name = re.sub(r"^.*?:", "", short_name.text).replace('"', "")
        result.append(clean_name)
        result.append(clean_name + "_")
    elif name is None or (
        name is not None and (not name.text or not name.text.strip())
    ):
        if ext_vlnv_name is not None and ext_vlnv_name.text:
            result.append(ext_vlnv_name.text.lower())
    elif (
        name is not None
        and ext_vlnv_name is not None
        and name.text.strip() == ext_vlnv_name.text.lower()
    ):
        result.append(ext_vlnv_name.text.lower())
    else:
        if name is not None and name.text:
            result.append(name.text.strip())
            result.append(name.text.strip() + "_")
    return result


def create_socket(path):
    try:
        tree = ET.parse(path)
        root = tree.getroot()
    except Exception as e:
        print(f"Error processing {path}: {str(e)}")
        return
    myname = get_myname_from_root(root)
    role_element = root.find(".//Role")
    role = role_element.text if role_element is not None and role_element.text else None
    
    
def interface_def_role(interface_path, interface, excludes, includes, reverse=0):
    tree = ET.parse(interface_path)
    root = tree.getroot()

    if not isinstance(interface, list):
        interface = []
    if not isinstance(excludes, list):
        excludes = []
    if not isinstance(includes, list):
        includes = []

    socket_element = ET.Element("Socket", Name=interface[0]) if len(interface) > 0 else ""
    socket_prefix = interface[1] if len(interface) > 1 else ""

    signals = root.findall(".//Signal")

    for port in root.findall("./InterfaceDefPort"):
        port_id = port.find("ID").text
        signal = next((sign for sign in signals if port.find("./XRefSignal/XRefTargetID").text in sign.find("ID").text), None)

        signal_keys = [k.text for k in signal.findall("./Property/Key")]
        signal_values = [v.text for v in signal.findall("./Property/Value")]

        port_keys = [k.text for k in port.findall("./Property/Key")]
        port_values = [v.text for v in port.findall("./Property/Value")]

        if port_id in excludes:
            add_comment("excluding ", signal_keys, signal_values, port_keys, port_values, signal, port)

        elif len(includes) > 0 and port_id not in includes:
            add_comment("not including ", signal_keys, signal_values, port_keys, port_values, signal, port)
            
        elif "owner" in port_keys and port_values is not None and port_values != 'concept':
            pass

        elif not("owner" in signal_keys and signal_values is not None) or "owner" in signal_keys and signal_values != 'concept':
            pass
        
        else:
            member = ET.Element('Member')
            member.set('wire', signal.find("./ID").text)
            my_name = []
            
            port_short_name = root.find(".//ShortName")
            signal_short_name = root.find(".//Signal//ShortName")
            port_name = port.find(".//Name")
            
            if port_short_name is not None and port_short_name.text and len(port_short_name.text) > 0:
                my_name.append(port_short_name.text.replace('"', ""))
            elif signal_short_name is not None and signal_short_name.text and len(signal_short_name.text) > 0:
                my_name.append(signal_short_name.text.replace('"', ""))
            else:
                if port_name is not None and port_name.text:
                    modified_name = re.sub(r'^(.*?)_a?[io]s*$', r'\1', port_name.text)
                    my_name.append(' '.join(modified_name.split()))
            
            name = socket_prefix + my_name[0]
            if signal.find(".//DataType//Vector") is not None:
                for vec in signal.findall(".//DataType//Vector"):
                    vector_element = ET.SubElement(member, "Vector")
                    vector_element.text = vec.text
            
            port_direction = port.find(".//Direction")
            if reverse == 1 and port_direction is not None and port_direction.text == "in":
                add_direction(member, 'out')
            elif reverse == 1 and port_direction is not None and port_direction.text == "out":
                add_direction(member, 'in')
            else:
                if port_direction is not None:
                    for direct in port.findall(".//Direction"):
                        add_direction(member, direct.text)
            

def add_comment(text_comment, signal_keys, signal_values, port_keys, port_values, signal, port):
    if ("owner" in port_keys and "concept" in port_values) or (
        "owner" in signal_keys and "concept" in signal_values
    ):
        signal_id = signal.find("./ID").text
        port.insert(0, ET.Comment(f"{text_comment} {signal_id}"))


def add_direction(member, text):
    direction_element = ET.SubElement(member, "Direction")
    direction_element.text = text


def process_filters_grouped(filters):
    try:
        tree = ET.parse(filters)
        root = tree.getroot()
    except Exception as e:
        print(e)
    
    result = []
    
    name_groups = defaultdict(list)
    for filter_elem in root:
        name = filter_elem.get('Name')
        if name:
            name_groups[name].append(filter_elem)
    
    for name in sorted(name_groups.keys()):
        group = name_groups[name]
        
        default_values = [elem for elem in group if elem.tag == 'DefaultValue']
        if not default_values:
            continue
        
        parameter = ET.Element('Parameter')
        parameter.set('Name', name)
        parameter.set('Type', 'FILTER')
        
        initial_values = [elem for elem in group if elem.tag == 'InitialValue']
        have_init = len(initial_values)
        
        have_spec = []
        text_groups = defaultdict(list)
        for elem in group:
            text = elem.text or ""
            text_groups[text].append(elem)
        
        for text, elems in text_groups.items():
            default_values_in_text_group = [e for e in elems if e.tag == 'DefaultValue']
            if default_values_in_text_group:
                non_designation_count = sum(1 for e in elems if e.get('Style') != 'Designation')
                have_spec.append(non_designation_count)
        
        for text in sorted(text_groups.keys()):
            elems = text_groups[text]
            
            default_values_in_text_group = [e for e in elems if e.tag == 'DefaultValue']
            if not default_values_in_text_group:
                continue
                
            value_elems = [e for e in elems if e.tag == 'Value']
            if value_elems:
                ph = ET.Element('ph')
                ph.set('Style', value_elems[0].get('Style', ''))
                ph.text = text
                parameter.append(ph)
                continue
                
            initial_value_elems = [e for e in elems if e.tag == 'InitialValue']
            if initial_value_elems:
                ph = ET.Element('ph')
                ph.set('Style', initial_value_elems[0].get('Style', ''))
                ph.text = text
                parameter.append(ph)
                continue
                
            if have_init > 0:
                continue
                
            if any(spec > 0 for spec in have_spec):
                continue
                
            non_value_elems = [e for e in elems if e.tag != 'Value']
            if non_value_elems:
                ph = ET.Element('ph')
                ph.set('Style', non_value_elems[0].get('Style', ''))
                ph.text = text
                parameter.append(ph)
        
        if len(parameter) > 0:
            result.append(parameter)
    
    return result


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


def main():
    try:
        Iproot = "C:/python_projects/work/my_parcing/parsed_context_spirit.xml"
        filter = None
        toolversion = 1.4
        Doc_Author = "Abc Abc"
        drive = "file:"
        disc = ""
        filter_params = [
            "audience",
            "platform",
            "product",
            "package",
            "props",
            "otherprops",
        ]
        input = "C:/python_projects/work/my_parcing/instance_sheet_TC49x.xml"
        filter = find_filter(
            input_file="C:/python_projects/work/my_parcing/instance_sheet_TC49x.xml",
            filter=filter,
        )
        data = open_lookup_file(Iproot)
        # data = process_df(drive,disc,data)
        """data.to_csv('lookup_file.csv')
        IPdefs = collect_parameters(filter_params,input, filter,data)"""
        xml_str = create_xml(
            toolversion, Iproot, data, "IPdefs.xml", filter, Doc_Author
        )

        # pretty_xml = parseString(xml_str).toprettyxml(indent="  ")

        # with open("output.xml", "w", encoding="utf-8") as f:
        #     f.write(pretty_xml)
        
        result = process_filters_grouped('./FILTERS.xml')
        
        root = ET.Element('root')
        for element in result:
            root.append(element)

        tree = ET.ElementTree(root)

        from xml.dom import minidom
        xml_str = ET.tostring(root, encoding='utf-8', method='xml')
        pretty_xml = minidom.parseString(xml_str).toprettyxml(indent="  ")
        with open("output.xml", 'w', encoding='utf-8') as file:
            file.write(pretty_xml)
        

    except Exception as e:
        logger.error(f"Conversion failed: {e}")
        raise


if __name__ == "__main__":
    main()
