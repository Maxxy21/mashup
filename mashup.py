import requests
import json
from gtts import gTTS
import re
from pygame import mixer
from sense_emu import SenseHat
from time import sleep
from bs4 import BeautifulSoup
import os

sense = SenseHat()

red = (255, 0, 0)
green = (0, 255, 0)
black = (0, 0, 0)


def playAudioFile(filename):
    mixer.init()
    mixer.music.load(filename)
    mixer.music.play()
    while mixer.music.get_busy():
        pass

def text2speech(lang, text):
    filename = 'audio.mp3'
    tts = gTTS(text=text, lang=lang)
    tts.save(filename)
    playAudioFile(filename)
    os.remove(filename)

def get_astro_URL(url):
    response = requests.get(url)
    success = response.status_code
    if success < 400:
        sense.clear(green)
        sleep(1)
        sense.show_message("Success", text_colour=green, scroll_speed=0.04)
        sleep(1)
        sense.clear()
    else:
        sense.clear(red)
        sleep(1)
        sense.show_message("!Request Failure", text_colour=red, back_colour=black, scroll_speed=0.04)
        sleep(1)
        sense.clear()
        print('Request Failure')
    result = json.loads(response.text)
    return result

astros = get_astro_URL('http://api.open-notify.org/astros.json')
peoplelist = astros['people']
names = [element['name'] for element in peoplelist]
craft = peoplelist[0]['craft']

#function that gets the english wiki page
def get_wiki_urlFromGoogle(query):
    request = requests.get("https://www.google.com/search?q=" + str(query))
    soup = BeautifulSoup(request.content, 'html.parser')  # create a soup object by parsing html of request
    wiki_en_substring = 'https://en.wikipedia.org/wiki'  # wikipedia english site substring to check for
    links = soup.findAll("a")
    list_of_links = []
    # replace unwanted characters in links found in the tag
    for link in soup.find_all("a", href=re.compile("(?<=/url\?q=)(htt.*://.*)")):
        list_of_links.append(re.split(":(?=http)", link["href"].replace("/url?q=", "")))
    lst_of_link = []
    for i in list_of_links:
        # strips brackets and quotes and creates preferred links with the wiki_sub
        lst_of_link.append(str(i).strip("[]'"))
        list_of_prefd_links = [y for y in lst_of_link if wiki_en_substring in y]
    # transfrom the list of preferred links to string
    listToStr = ' '.join([str(e) for e in list_of_prefd_links])
    substring_site = listToStr.split('&')[0]
    url = substring_site.replace("'", "")
    return str(url)

def astros_on_board():
    new_name_lst = names[:]  # update list of names and add 'and' to the last but one element for grammar purposes
    new_name_lst[-1:-1] = ['and']
    text = 'In space there are currently ' + str(
        astros['number']) + ' astronauts on board the ' + craft + ' and their names are ' + ', '.join(
        new_name_lst) + '.\n'
    print(text)
    # text to speech
    text2speech('en', (text))

def astros_on_board_names():
    people_dict = {}
    v = 1
    for i in range(astros['number']):
        # creates a dictionary of the astronaut names as values and numbers as keys
        people_dict[v + i] = names[i]
    return people_dict

def ISS_position():
    result = get_astro_URL('http://api.open-notify.org/iss-now.json')
    iss_position = result["iss_position"]
    position = "The ISS is at lon: " + str(iss_position["longitude"]) + " and lat: " + str(iss_position["latitude"])
    print(position)
    for i in range(0, 2):
        # shows the ISS position on the sense_hat
        sense.show_message(position)

def speech_text(texts):
    for elements in texts:
        text = re.sub("[\[].*?[\]]", "", elements)  # removes the wiki_embedded links in []
        print(text)
        text2speech('en', text)

def wiki_bio(name):
    wiki_format = name.replace(" ", "_")
    # creates a url of wiki substring and the query
    url = 'https://en.wikipedia.org/wiki/' + str(wiki_format)
    request = requests.get(url)
    success = request.status_code
    if success < 400:
        soup = BeautifulSoup(request.content, 'html.parser')
        # creates a list of texts found in tag 'p'
        text1_lst = [i.text for i in soup.select('p')]
        # remove spaces and new lines
        text_strip = [y.strip() for y in text1_lst]
        # remove empty elements
        rem_empty_elements = [x for x in text_strip if x]
        speech_text(rem_empty_elements)
    else:
        # if name with the wikipedia is not found it gets the link on google
        # possibly different name or spelling
        wiki_link = get_wiki_urlFromGoogle(name)
        request = requests.get(wiki_link)
        soup = BeautifulSoup(request.content, 'html.parser')
        text2_lst = [i.text for i in soup.select('p')]
        text_strip = [y.strip() for y in text2_lst]
        rem_empty_elements = [x for x in text_strip if x]
        speech_text(rem_empty_elements)


print('This is a program that shows the astronauts currently on board the',craft,'in space.')
try:
    while True:
        selection = int(input('\nPlease choose the corresponding number for each info:\n1 for the astronauts currently in space and '
            'their biographies.\n2 for the spacecraft\'s current position.\nPress CTRL+C to quit.\t\n'))
        if selection == 1:
            astros_on_board()
            bio_select = input('Would you like to hear the biography of an astronaut on board the '+ craft +'? Answer y for YES '
                'and n for NO.\t\n')
            if bio_select.lower() == 'y':
                for key in astros_on_board_names():
                    print(key, 'for', astros_on_board_names()[key])
                astro_num = int(input('Please choose the corresponding number for the biography.\t\n'))
                astros_name_key = [key for key in astros_on_board_names()]
                if astro_num in astros_name_key:
                    sense.show_message(astros_on_board_names()[astro_num], scroll_speed=0.05)
                    sense.clear()
                    wiki_bio(astros_on_board_names()[astro_num])
                else:
                    print('Please choose a correct number in the options given.')
                    continue
            elif bio_select.lower() == 'n':
                print("Good bye.")
                sense.show_message("Good bye.")
                break
            else:
                print('Please choose a correct option in the options given.')
                continue
        elif selection == 2:
            ISS_position()
        else:
            print('Please choose a correct option in the options given.')
            continue
except ValueError:
    print("No valid integer in line. Please insert only a number.")
except KeyboardInterrupt:
    print("Good bye.")
    sense.show_message("Good bye.")
    sense.clear()