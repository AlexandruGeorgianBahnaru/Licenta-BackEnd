from datetime import datetime
import utils.constants as constants
from openai import OpenAI
import re
from pdfminer.high_level import extract_pages


searched_values = ["Cantitate facturată", "Mod stabilire index", "ValoareTVA", "Sold de plată", "Total valoare factură\\ncurentă", "Sold anterior", "Dată scadență", "Dată emitere", "Perioadă facturată"]
# de mutat in baza de date
found_values = dict()

response = ""
chat_message_content = ""
client = OpenAI(
    api_key=constants.OPEN_AI_KEY,
)

def find_index_searched_values(element):
    for index, val in enumerate(searched_values):
        if val in element:
            return index
    return -1

def openai_api_call(question_first, response_message, text_to_be_searched_in_first, index):
    if response_message == '':
        chat_message_content = question_first + searched_values[index] + " in textul : " + text_to_be_searched_in_first
    else:
        chat_message_content = question_first + "Raspunsul dat de tine: " + response_message + ", textul initital: " + text_to_be_searched_in_first + ", valoarea pentru care treuia sa cauti in text: " + searched_values[index]
    print(chat_message_content)
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": chat_message_content,
            }
        ],
        model=constants.CHAT_VERSION,
    )
    return chat_completion.choices[0].message.content

def extract_billing_month(period_string):
    start_str = period_string.split(' - ')[0]
    start_date = datetime.strptime(start_str, "%d.%m.%Y")
    return start_date.strftime("%B %Y")


async def text_extractor_file(file):
        for page_layout in extract_pages(file):
            for elem in page_layout:
                element = str(elem)
                index_searched_values = find_index_searched_values(element)
                if index_searched_values != -1:
                    message_response = openai_api_call(constants.CHAT_MESSAGE_REQUEST, '', element, index_searched_values)
                    verified_response = openai_api_call(constants.CHAT_MESSAGE_VERIFY_RESPONSE_FIRST, message_response,
                                                        element, index_searched_values)
                    found_value_numeric = re.findall(r'\d+,\d+|\d+', verified_response)
                    if found_value_numeric and index_searched_values < 6:
                        found_values.update({searched_values[index_searched_values]: found_value_numeric[0].replace(",", ".")})
                    else:
                        found_values.update({searched_values[index_searched_values]: verified_response})

        cantitate_facturata = re.findall(r'\d+,\d+|\d+', found_values["Cantitate facturată"])
        value_khw = (float(found_values["Sold de plată"]) / float(cantitate_facturata[0])) / (1.0 + float(found_values["ValoareTVA"]) / 100)
        found_values.update({"Valoare kwh": round(value_khw, 3)})
        print(found_values)
        return found_values

if __name__ == '__main__':
    path = r'E:\\Licenta\\Facturi_EON\\Factura7.pdf'
    # text_extractor_path(path)
