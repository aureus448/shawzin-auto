# Warframe Shawzin Test (c) Nate Ruppert 2021
r"""Converts Warframe shawzin encoding to (hopefully) AHK acceptable code
LIMITATIONS - Does not account for or deal with multi-string (multi-fret) encodings (yet)

Encoding reference: https://warframe.fandom.com/wiki/Shawzin
Input string created by me via: https://vinchenzo.gitlab.io/warframe-shawzin-composer/
Relies on tesseract for OCR (For finding "Record" or "Recording"): https://github.com/UB-Mannheim/tesseract/wiki
Expects 64-bit tesseract placed here: (Default install location) C:\Program Files\Tesseract-OCR\tesseract

Example test string: Saria's Song from Legend of Zelda Ocarina of Time

5JAAMAERAIJAQMAURAYJAgMAkRAohAsUAwRA4SA8RBAKBEEBICBcEBgKBkEBoJCAMCERCIJCQMC
URCYJCgMCkRCohCsUCwRC4SC8hDASDEKDIRDcKDgCDkEDoCEAEEEJEIKEQMEUREYSEgREkEEoCF
AJFBEFEKFFJFIMFJKFQRFRMFUSFVRFYUFZSFghFhUFkiFlhFokFpCGAEGEJGIKGQMGURGYSGgRG
kEGoCHABHEJHIEHMKHQJHUMHYKHcRHgMHkSHoRHsUHwSH0hH4iH6UH+hIA

TODO:
    * Add support for multi-fret encoding
    * Add better function(s) for each individual task (ex: shawzin_auto.record() etc)
    * Un-list comprehension everything for actual code readability for others (and yourself when you forget in 3 days)
"""

import time
from typing import List

import pytesseract
from ahk import AHK
from PIL import ImageGrab


def imToString():
    # Path of tesseract executable
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract"
    # ImageGrab-To capture the screen image in a loop.
    # Bbox used to capture a specific area.
    cap = ImageGrab.grab()

    # Converted the image to monochrome for it to be easily
    # read by the OCR and obtained the output String.
    tesstr = pytesseract.image_to_data(cap)
    return tesstr


def play_song(input_data):
    start = time.perf_counter()
    i = 0  # Used to determine which position in array
    while i < len(input_data):
        note_time, fret, key = input_data[i]
        if (timer := time.perf_counter() - start) >= note_time:
            print(f"Activated at: {timer} for [{note_time}, {fret}, {key}]")
            if fret:
                ahk.send(f"{{{fret} down}}{key}{{{fret} up}}", delay=0)
            else:
                ahk.send(f"{key}", delay=0)
            i += 1


def screen_search(text_match, text_non_match=""):
    screen_data = imToString()
    # Result of tesseract: grab the "Record" line - if not in shawzin the program intentionally crashes
    # This works 100% because Warframe text is nice and easy for OCR
    if text_non_match:
        line = [
            _
            for _ in screen_data.split("\n")
            if text_match in _ and text_non_match not in _
        ]
    else:
        line = [_ for _ in screen_data.split("\n") if text_match in _]
    if len(line) > 1 or not line:
        raise ValueError(
            "No 'Record' found in Screenshot - are you sure you're on the Shawzin page?"
        )
    else:
        width, height = line[0].split("\t")[
            6:8
        ]  # Position 6 and 7 of string split contain required width, height
    return width, height


if __name__ == "__main__":
    shawzin_input = (
        "5JAAMAERAIJAQMAURAYJAgMAkRAohAsUAwRA4SA8RBAKBEEBICBcEBgKBkEBoJCAMCERC"
        "IJCQMCURCYJCgMCkRCohCsUCwRC4SC8hDASDEKDIRDcKDgCDkEDoCEAEEEJEIKEQMEURE"
        "YSEgREkEEoCFAJFBEFEKFFJFIMFJKFQRFRMFUSFVRFYUFZSFghFhUFkiFlhFokFpCGAEG"
        "EJGIKGQMGURGYSGgRGkEGoCHABHEJHIEHMKHQJHUMHYKHcRHgMHkSHoRHsUHwSH0hH4iH"
        "6UH+hIA"
    )
    print(f"Input provided of: {shawzin_input}")
    clean = shawzin_input.replace(" ", "")[0]
    notes = [
        clean[1:][i : i + 3] for i in range(0, len(clean), 3)
    ]  # Each note is 3 characters
    result: List[List[int]] = [
        ordinal for x in notes if (ordinal := list(map(ord, [_ for _ in x])))
    ]  # Converts each character to their int variant

    # Rewrites based on ASCII character set the Shawzin value for each character
    # Follows the order: A-Z (26), then a-z (26), then 0-9 (10), then +, / (2) for 64 total
    final: List[List[int]] = [
        [
            res - 64
            if 64 < res < 91  # A-Z
            else res - 70
            if 96 < res < 123  # a-Z
            else res + 5
            if 47 < res < 58  # 0-9
            else 63
            if res == 43  # +
            else 64
            if res == 47  # /
            else -1
            for res in x
        ]
        for x in result
    ]

    # Converts part 1 and 2 of each note [0, 1, 2] from measure # and position # to time in seconds before press
    # This is the exact time from start to press key
    note_timing = [
        _
        for note_step in final
        if (_ := (note_step[1] - 1) * 4 + note_step[2] * 4 / 64)
    ]

    note_to_press = [ord(note_step[0]) for note_step in notes if note_step]

    i = 0  # Used for indexing which note its on
    ahk_input = []  # List containing keys to press
    for x, y in zip(note_timing, note_to_press):
        # print('Raw:', x, y)

        # LIMITATION: Only implements: None, Sky, Earth, Water (no combination, yet)
        # No Fret A-H [A, I, Q (::8) are all n/a for shawzin encoding]
        if 64 < y < 91 or 103 < y < 111:  # A-Z or h-n (remaining of Water)
            # print(f'Debug: {y}')
            if 64 < y < 72:  # None
                pos = 65
                fret = "None"
            elif 72 < y < 80:  # Sky
                pos = 73
                fret = "Sky"
            elif 80 < y < 88:  # Earth
                pos = 81
                fret = "Earth"
            elif 102 < y < 112:  # Water
                pos = 103
                fret = "Water"
            else:
                print(f"Unknown for {y}! Quitting")
                break

            # Does not count any other positions than 1, 2, 3 (for now)
            key = res if (res := y - pos) < 3 else 3 if res == 4 else -1
            # print(f'{fret} for {y} Key: {key}')
            # convert fret to a position (0 for none, 1 for left, 2 for down, 3 for right)
            fret_display = (
                ""
                if fret == "None"
                else "Left"
                if fret == "Sky"
                else "Down"
                if fret == "Earth"
                else "Right"
                if fret == "Water"
                else "BAD DATA"
            )
        else:
            print(
                f"Provided (currently) unsupported values: {y} "
                f"- Please note Any Fret combinations are not supported yet"
            )
            break

        print(
            f"[Note #{i:>3}] At exactly {x:>7}s: Will press Note Key [{key}] and Fret Key [{fret_display}]"
        )
        ahk_input.append([x, fret_display, key])
        i += 1  # Increment where we are

    # Collect warframe window:
    ahk = AHK()

    win = list(ahk.windows())  # list of all windows
    warframe_window = [_ for _ in win if "Warframe" in str(_.title)]  # Should return 1

    print("Must be in shawzin already for this to work")
    input("Press enter to confirm just playing it")
    warframe_window[0].activate()
    time.sleep(1)
    play_song(ahk_input)

    print("Must be in shawzin already for this to work")
    input("Press enter to confirm recording")
    warframe_window[0].activate()
    ahk.key_press("W")
    time.sleep(1)
    width, height = screen_search("Record", "Recorded")
    ahk.mouse_position = width, height
    print(f"Moving mouse to position X: {width}, Y: {height}")
    print("Beginning in 5 seconds...")
    time.sleep(5)
    ahk.click()  # Click Record
    time.sleep(0.25)  # Estimated delay
    play_song(ahk_input)

    # Now that recording is finished (must be done manually - waits a bit)
    input("Press enter to confirm continue to playback")
    print("Reactivating")
    warframe_window[0].activate()
    ahk.key_press("W")
    time.sleep(1)
    # Searches for Recorded Song button and gets ready to Validate recording
    width, height = screen_search("Recorded")
    ahk.mouse_position = width, height
    print(f"Moving mouse to position X: {width}, Y: {height}")
    print("Beginning in 5 seconds...")
    time.sleep(5)
    ahk.click()  # Click Record
    time.sleep(2.75)  # Estimated delay
    play_song(ahk_input)

    print("Done! Thanks for using my tool and hope it worked for you :)")
