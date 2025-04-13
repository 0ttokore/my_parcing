import os
import xml.etree.ElementTree as ET
import logging
import re
import pandas as pd
from itertools import groupby
import copy
from collections import defaultdict
from xml.dom.minidom import parseString


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
                #vector = []
                for vec in signal.findall(".//DataType//Vector"):
                    #vector.append(vec.text)
                    vector_element = ET.SubElement(member, "Vector")
                    vector_element.text = vec.text
            
            port_direction = port.find(".//Direction")
            if reverse == 1 and port_direction is not None and port_direction.text == "in":
                direction = 'out'
            elif reverse == 1 and port_direction is not None and port_direction.text == "out":
                direction = 'in'
            else:
                if port_direction is not None:
                    #direction = []
                    for direct in port.findall(".//Direction"):
                        #direction.append(direct.text)
                        direction_element = ET.SubElement(member, "Direction")
                        direction_element.text = direct.text      
            

def add_comment(text_comment, signal_keys, signal_values, port_keys, port_values, signal, port):
    if ("owner" in port_keys and "concept" in port_values) or (
        "owner" in signal_keys and "concept" in signal_values
    ):
        signal_id = signal.find("./ID").text
        port.insert(0, ET.Comment(f"{text_comment} {signal_id}"))


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

        pretty_xml = parseString(xml_str).toprettyxml(indent="  ")

        with open("output.xml", "w", encoding="utf-8") as f:
            f.write(pretty_xml)

    except Exception as e:
        logger.error(f"Conversion failed: {e}")
        raise


if __name__ == "__main__":
    main()
