
import math

def text_essence(input_data, context, para_maps2=None, warning="fatal", suppress=""):
    if not input_data.get('kind'):
        return ""
        
    kind = input_data.get('kind')
    
    if kind == 'cat':
        return text_essence(input_data['children'][0], context, para_maps2, warning, suppress) + \
               text_essence(input_data['children'][1], context, para_maps2, warning, suppress)
               
    elif kind == 'const' and input_data.get('text') == '#':
        return input_data.get('text')
        
    elif kind == 'const':
        return input_data.get('text', '').replace('&amp;', '&')
        
    elif kind == 'var' and input_data.get('text') == 'suppress' and len(suppress) > 0:
        return suppress
        
    elif kind == 'var':
        get_parameter = []
        
        if para_maps2:
            key = f"{context}:{input_data.get('text')}"
            for param in para_maps2.get_parameters(key):
                get_parameter.append(param.replace('"', ''))
                
            if para_maps2.has_filter(context):
                get_parameter.extend(get_filter(input_data.get('text'), context))
                
        if not get_parameter:
            get_parameter.append(input_data.get('text'))
            
        if len(get_parameter) < 2:
            error_msg = f'ERROR: Unresolved parameter "{input_data.get("text")}"!'
            if warning == 'fatal':
                raise ValueError(error_msg)
            else:
                print(error_msg)
                print(f'Replaced by "{get_parameter[0]}"')
                
        return get_parameter[0]
        
    elif kind == 'func' and input_data['children'][0].get('text') == 'pos' and len(input_data['children']) == 3:
        index = num_essence(input_data['children'][2], context, para_maps2, warning)
        
        second_child = input_data['children'][1]
        paras = []
        
        if second_child.get('kind') == 'func' and second_child['children'][0].get('text') == 'list':
            for pos, child in enumerate(second_child['children'][1:], 0):
                if pos == index:
                    paras.append(child)
        elif second_child.get('kind') == 'var':
            get_parameter = []
            if para_maps2:
                key = f"{context}:{second_child.get('text')}"
                for param in para_maps2.get_parameters(key):
                    get_parameter.append(param)
                    
            if get_parameter and len(get_parameter[0]) > 0:
                tree = parse_essence(get_parameter[0])
                if tree.get('kind') == 'func' and tree['children'][0].get('text') == 'list':
                    for pos, child in enumerate(tree['children'][1:], 0):
                        if pos == index:
                            paras.append(child)
                else:
                    error_msg = f'ERROR: Invalid first parameter in "pos({second_child.get("text")},...)"!'
                    raise ValueError(error_msg)
            else:
                error_msg = f'ERROR: Unresolved parameter "{input_data.get("text")}"'
                if warning == 'fatal':
                    raise ValueError(error_msg)
                else:
                    print(error_msg)
                    print("Replaced by -1")
                    return "-1"
        else:
            raise ValueError("ERROR: Invalid first parameter in 'pos()'!")
            
        if paras:
            return text_essence(paras[0], context, para_maps2, warning, suppress)
        else:
            error_msg = f'ERROR: pos({input_data["children"][1]},{index}) index out of bounds!'
            if warning == 'fatal':
                raise ValueError(error_msg)
            else:
                print(error_msg)
                print("Replaced by -1")
                return "-1"
                
    elif kind == 'func' and input_data['children'][0].get('text') == 'dec' and len(input_data['children']) == 3:
        paras = [num_essence(child, context, para_maps2, warning) for child in input_data['children'][1:]]
        s = str(paras[1])
        padding = '0' * (int(paras[0]) - len(s))
        return padding + s
        
    elif kind == 'func' and input_data['children'][0].get('text') == 'hex' and len(input_data['children']) == 3:
        paras = [num_essence(child, context, para_maps2, warning) for child in input_data['children'][1:]]
        s = decimal_to_hex(paras[1])
        padding = '0' * (int(paras[0]) - len(s))
        return padding + s
        
    elif kind == 'func' and input_data['children'][0].get('text') == 'bin' and len(input_data['children']) == 3:
        paras = [num_essence(child, context, para_maps2, warning) for child in input_data['children'][1:]]
        s = decimal_to_bin(paras[1])
        padding = '0' * (int(paras[0]) - len(s))
        return padding + s
        
    elif kind == 'func' and input_data['children'][0].get('text') == 'eng' and len(input_data['children']) == 2:
        val = num_essence(input_data['children'][1], context, para_maps2, warning)
        
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

def num_essence(input_data, context, para_maps2=None, warning="fatal"):
    pass

def parse_essence(text):
    pass

def get_filter(param_name, context):
    return []


def decimal_to_hex(decimal_value):
    return format(int(decimal_value), 'x')

def decimal_to_bin(decimal_value):
    return format(int(decimal_value), 'b')

def get_filter(param_name, context):
    pass

input_data = {
    "kind": "func",
    "children": [
        {"text": "hex"},
        {"kind": "const", "text": "4"},
        {"kind": "const", "text": "255"}
    ]
}

context = "default"
result = text_essence(input_data, context)
print(result)  
