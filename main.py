from openai import OpenAI
import re
from pdfminer.high_level import extract_pages,extract_text
from pyexpat.errors import messages

searched_values = ["Cantitate facturată", "Perioadă facturată", "Mod stabilire index", "Sold de plată", "Total valoare factură\\ncurentă", "Sold anterior", "Dată scadență", "Dată emitere", "ValoareTVA"]
found_values = dict()

open_ai_key = ""
chat_version = ""
chat_message_content = ""
chat_message_explanation = ""
response = ""


file = open("utils\\variables.txt","r")

for line in file:
    line.rstrip()
    last_dqoute = line.rfind('"')
    penultimate_dqoute = line.rfind('"', 0, last_dqoute)
    if "start_sequence" in line:
        start_sequence = line[penultimate_dqoute + 1 : last_dqoute]
    if "end_sequence" in line:
        end_sequence = line[penultimate_dqoute + 1 : last_dqoute]
    if "open_ai_key" in line:
        open_ai_key = line[penultimate_dqoute + 1: last_dqoute]
    if "chat_version" in line:
            chat_version = line[penultimate_dqoute + 1: last_dqoute]
    if "chat_message_explanation" in line:
        chat_message_explanation = line[penultimate_dqoute + 1: last_dqoute]

client = OpenAI(
    api_key=open_ai_key,
)

def find_index(element):
    for index, val in enumerate(searched_values):
        if val in element:
            return index
    return -1

def openai_api_call(element, index):
    chat_message_content = chat_message_explanation + searched_values[index] + "din textul : " + element
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": chat_message_content,
            }
        ],
        model=chat_version,
    )
    return chat_completion.choices[0].message.content

def text_extractor(path):
    for page_layout in extract_pages(path):
        for elem in page_layout:
            element = str(elem)
            index = find_index(element)
            if index != -1:
                response_message = openai_api_call(element, index)
                found_values.update({searched_values[index]: response_message if "," not in response_message else response_message.replace(',', '.')})
    cantitate_facturata = re.findall(r'\d+,\d+|\d+', found_values["Cantitate facturată"])
    value_khw = (float(found_values["Sold de plată"]) / float(cantitate_facturata[0])) / (1.0 + float(found_values["ValoareTVA"]) / 100)
    found_values.update({"Valoare kwh": value_khw})
    print(found_values)



if __name__ == '__main__':
    path = r'E:\\Licenta\\Facturi_EON\\Factura7.pdf'
    text_extractor(path)
