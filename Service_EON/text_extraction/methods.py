from utils.constants import *
from openai import OpenAI
import re
from pdfminer.high_level import extract_pages,extract_text
from pyexpat.errors import messages

searched_values = ["Cantitate facturată", "Perioadă facturată", "Mod stabilire index", "Sold de plată", "Total valoare factură\\ncurentă", "Sold anterior", "Dată scadență", "Dată emitere", "ValoareTVA"]
# de mutat in baza de date
found_values = dict()

response = ""
chat_message_content = ""

client = OpenAI(
    api_key=OPEN_AI_KEY,
)

def find_index(element):
    for index, val in enumerate(searched_values):
        if val in element:
            return index
    return -1

def openai_api_call(element, index):
    chat_message_content = CHAT_MESSAGE_EXPLANATION + searched_values[index] + "din textul : " + element
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": chat_message_content,
            }
        ],
        model=CHAT_VERSION,
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
    found_values.update({"Valoare kwh": round(value_khw, 3)})
    print(found_values)



if __name__ == '__main__':
    path = r'E:\\Licenta\\Facturi_EON\\Factura7.pdf'
    text_extractor(path)
