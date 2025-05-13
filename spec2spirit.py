import xml.etree.ElementTree as ET
import logging
import re
from mathlib2 import decimal_to_hex, decimal_to_bin, power, str2base
import math


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# the solver function for () + - * / mod div ^
def evaluate(input_str: str, context: str = "0") -> str:
    if input_str == " ":
        return 0
    
    # prio 1: ( )
    if ")" in input_str:
        bracket = re.sub(r"^.*\(", '', input_str.split(")")[0])
        prebracket = input_str[: len(input_str.split(")")[0]) - 1 - len(bracket)]

        if re.match(r"dec\d*$", prebracket):
            try:
                s = str(int(evaluate(bracket, context)))
            except Exception as e:
                logger.error(f"Conversion failed: {e}")
            p = ["0" for _ in range(len(s) + 1, int(re.sub(r".*dec(\d*)$", '0$1', prebracket)))]
            return re.sub(r"dec\d*$", '', prebracket) + "".join(p) + s + input_str.split(")")[1]
        elif re.match(r"hex\d*$", prebracket):
            try:
                s = decimal_to_hex(str_to_number(evaluate(bracket, context)))
            except Exception as e:
                logger.error(f"Conversion failed: {e}")
            p = ["0" for _ in range(len(s) + 1, int(re.sub(r".*hex(\d*)$", '0$1', prebracket)))]
            return re.sub(r"hex\d*$", '', prebracket) + "".join(p) + s + input_str.split(")")[1]
        elif re.match(r"bin\d*$", prebracket):
            try:
                s = decimal_to_bin(str_to_number(evaluate(bracket, context)))
            except Exception as e:
                logger.error(f"Conversion failed: {e}")
            p = ["0" for _ in range(len(s) + 1, int(re.sub(r".*bin(\d*)$", '0$1', prebracket)))]
            return re.sub(r"bin\d*$", '', prebracket) + "".join(p) + s + input_str.split(")")[1]
        elif re.match(r"eng$", prebracket):
            try:
                val = str_to_number(evaluate(bracket, context))
            except Exception as e:
                logger.error(f"Conversion failed: {e}")
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
            return re.sub(r"eng$", '', prebracket) + "".join(p) + input_str.split(")")[1]
        elif re.match(r"pow\d+$", prebracket):
            try:
                e = int(evaluate(bracket, context))
                b = str_to_number(re.sub(r".*pow(\d+)$", '$1', prebracket))
            except Exception as e:
                logger.error(f"Conversion failed: {e}")
            return str_to_number(evaluate(re.sub(r"pow\d+$", '', prebracket) + str(power(b, e)) + input_str.split(")")[1], context))
        elif re.match(r"min$", prebracket):
            vals = bracket.split(",")
            min_val = min(vals)
            return evaluate(re.sub(r"min$", '', prebracket) + min_val + input_str.split(")")[1], context)
        elif re.match(r"max$", prebracket):
            vals = bracket.split(",")
            max_val = max(vals)
            return evaluate(re.sub(r"max$", '', prebracket) + max_val + input_str.split(")")[1], context)
        else:
            return str_to_number(evaluate(prebracket + evaluate(bracket, context) + input_str.split(")")[1], context))
    
    elif '+' in input_str or re.match(r"[\d\w]+\s*-", input_str): # least binding: + -
        plus = len(input_str.split("+")[0])
        minus = len(before_last_minus(input_str,''))
        if plus < minus: # no + or no + after -
            return str_to_number(evaluate(input_str[:minus], context)) - str_to_number(evaluate(input_str[minus+2:], context))
        else:
            return str_to_number(evaluate(input_str[:plus], context)) + str_to_number(evaluate(input_str[plus+2:], context))
 
    elif any(op in input_str for op in {'*', '/', 'div', 'mod'}): # highest binding: * / mod div
        mul = len(input_str.split("*")[0])
        div = len(input_str.split("/")[0])
        idiv = len(input_str.split("div")[0])
        mod = len(input_str.split("mod")[0])
        if mul > div and mul > idiv and mul > mod:
            return str_to_number(evaluate(input_str.split("*")[0], context)) * str_to_number(evaluate(input_str.split("*")[1], context))
        elif div > mul and div > idiv and div > mod:
            return str_to_number(evaluate(input_str.split("/")[0], context)) / str_to_number(evaluate(input_str.split("/")[1], context))
        elif idiv > mul and idiv > div and idiv > mod:
            return math.floor(str_to_number(evaluate(input_str.split("div")[0], context)) / str_to_number(evaluate(input_str.split("div")[1], context)))
        else:
            return str_to_number(evaluate(input_str.split("mod")[0], context)) % str_to_number(evaluate(input_str.split("mod")[1], context))

    elif '^' in input_str: # highest binding: ^
        b = str_to_number(evaluate(input_str.split("^")[0], context))
        e = str_to_number(evaluate(input_str.split("^")[1], context))
        if b == 1 or e == 0:
            return 1
        elif b == 0:
            return 0
        elif e == 1:
            return b
        elif castable(b, 'float') and castable(e, 'integer'):
            return power(b, int(e))
        else:
            raise ValueError(f"ERROR: Not a valid numeric expression {input_str}")

    elif input_str.strip().startswith('$'): # variables $
        return evaluate(get_parameter(input_str.split("$")[1], context).strip(), context)
    
    elif input_str.strip().upper().startswith('0B'): # literals
        return str2base(input_str.strip().split('0B')[1], 2)
    elif input_str.strip().upper().startswith('0X'): 
        return str2base(input_str.strip().split('0X')[1], 16)
    elif castable(input_str, 'float'):
        return float(input_str)
    elif context == '0':
        return str_to_number(input_str)
    else:
        raise ValueError(f"ERROR: Expression is not a valid number - {input_str}")
    

def str_to_number(input_str: str):
    input_str = input_str.strip()
    if re.match(r'^\d+[.,]\d+$', input_str):
        return float(input_str)
    elif re.match(r'^\d+$', input_str):
        return int(input_str)
    else:
        raise ValueError(f"Invalid input: {input_str}")
    

def before_last_minus(input_str: str, result: str) -> str:
    if not re.match(input_str, r'[\d\w]+\s*-'):
        return result
    elif len(result) == 0:
        return before_last_minus(re.sub(r'^.*[\d\w]+\s*-', '', input_str), re.sub(r'^(.*[\d\w]+\s*)-.*$', '$1', input_str))
    else:
        return before_last_minus(re.sub(r'^.*[\d\w]+\s*-', '', input_str), result + '-' + re.sub(r'^(.*[\d\w]+\s*)-.*$', '$1', input_str))


def castable(input_str: str, type: str) -> bool:
    try:
        if type == 'float' or type == 'double':
            float(input_str)
        elif type == 'integer':
            int(input_str)
        return True
    except ValueError:
        return False


def get_parameter(input_str: str, context: str) -> str: # TODO: implement
    return input_str


def main():
    try:
        strg = 'max(1,2,3,4,5)'
        res = evaluate(strg)
        print(res)
    
    
    except Exception as e:
        logger.error(f"Conversion failed: {e}")
        raise


if __name__ == "__main__":
    main()