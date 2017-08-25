import re
import pkg_resources


DELIMITERS = [r'\{\{', r'\}\}']
regex = DELIMITERS[0] + '(.*?)' + DELIMITERS[1]


def render_template(source_string, dictionary):
    keywords = re.findall(regex, source_string)
    output = source_string

    for keyword in keywords:
        if keyword not in dictionary:
            raise Exception("Variable " + keyword + " undefined")

    for keyword in keywords:
        output=output.replace("{{" + keyword + "}}", str(dictionary[keyword]))

    return output

def query_gen(sql_name):
    pass

