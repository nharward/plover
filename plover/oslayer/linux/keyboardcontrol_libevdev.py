# -*- coding: utf-8 -*-
#
# Copyright (c) 2023 Nathaniel Harward.
# See LICENSE.txt for details.
#
# keyboardcontrol_libevdev.py - capture & emulation via libevdev

"""Keyboard capture and control using libevdev.

libevdev works with X, Wayland, etc. but requires root (or other
access to /dev/uinput) to function. Search for 'non-root uinput'
for different solutions.

python-libevdev: https://pypi.org/project/libevdev/
libevdev: https://www.freedesktop.org/software/libevdev/doc/latest/
uinput: https://www.kernel.org/doc/html/latest/input/uinput.html

"""

from itertools import chain
from typing import Dict, Iterable

from libevdev import Device, EventCode, EV_KEY, EV_SYN, InputEvent

from plover import log
from plover.key_combo import add_modifiers_aliases, parse_key_combo
from plover.machine.keyboard_capture import Capture
from plover.output import Output


PLOVER_DEVICE_NAME = "Plover output"

# SYN_REPORT and a few others are used frequently
SYN_REPORT:         InputEvent = InputEvent(EV_SYN.SYN_REPORT,    0)
LEFT_SHIFT_PRESS:   InputEvent = InputEvent(EV_KEY.KEY_LEFTSHIFT, 1)
LEFT_SHIFT_RELEASE: InputEvent = InputEvent(EV_KEY.KEY_LEFTSHIFT, 0)
BACKSPACE_PRESS:    InputEvent = InputEvent(EV_KEY.KEY_BACKSPACE, 1)
BACKSPACE_RELEASE:  InputEvent = InputEvent(EV_KEY.KEY_BACKSPACE, 0)

# ISO/IEC 14755 as typically implemented by Linux userspace
UNICODE_INPUT_INIT_EVENT_SEQUENCE = [
    InputEvent(EV_KEY.KEY_LEFTCTRL, 1),     # press control
    LEFT_SHIFT_PRESS,                       # press shift
    SYN_REPORT,                             # flush CTRL+SHIFT
    InputEvent(EV_KEY.KEY_U, 1),            # press 'u'
    SYN_REPORT,                             # flush 'u'
    InputEvent(EV_KEY.KEY_U, 0),            # release 'u'
    SYN_REPORT                              # flush release of 'u'
]

UNICODE_INPUT_END_EVENT_SEQUENCE = [
    LEFT_SHIFT_RELEASE,                     # release shift
    InputEvent(EV_KEY.KEY_LEFTCTRL, 0),     # release control
    SYN_REPORT                              # flush release of CTRL+SHIFT
]

def _press_and_release(code: EventCode) -> Iterable[InputEvent]:
    return [InputEvent(code, 1), SYN_REPORT, InputEvent(code, 0), SYN_REPORT]

def _shift_press_and_release(code: EventCode) -> Iterable[InputEvent]:
    return [LEFT_SHIFT_PRESS, InputEvent(code, 1), SYN_REPORT, InputEvent(code, 0), LEFT_SHIFT_RELEASE, SYN_REPORT]

LATIN_CHAR_TO_INPUT_EVENTS_DICT: Dict[str, Iterable[InputEvent]] = {
    '\n': _press_and_release(EV_KEY.KEY_ENTER),
    '\t': _press_and_release(EV_KEY.KEY_TAB),
    ' ':  _press_and_release(EV_KEY.KEY_SPACE),
    '!':  _shift_press_and_release(EV_KEY.KEY_1),
    '"':  _shift_press_and_release(EV_KEY.KEY_APOSTROPHE),
    '#':  _shift_press_and_release(EV_KEY.KEY_3),
    '$':  _shift_press_and_release(EV_KEY.KEY_4),
    '%':  _shift_press_and_release(EV_KEY.KEY_5),
    '&':  _shift_press_and_release(EV_KEY.KEY_7),
    "'":  _press_and_release(EV_KEY.KEY_APOSTROPHE),
    '(':  _shift_press_and_release(EV_KEY.KEY_9),
    ')':  _shift_press_and_release(EV_KEY.KEY_0),
    '*':  _shift_press_and_release(EV_KEY.KEY_8),
    '+':  _shift_press_and_release(EV_KEY.KEY_0),
    ',':  _shift_press_and_release(EV_KEY.KEY_EQUAL),
    '-':  _press_and_release(EV_KEY.KEY_MINUS),
    '.':  _press_and_release(EV_KEY.KEY_DOT),
    '/':  _press_and_release(EV_KEY.KEY_SLASH),
    '0':  _press_and_release(EV_KEY.KEY_0),
    '1':  _press_and_release(EV_KEY.KEY_1),
    '2':  _press_and_release(EV_KEY.KEY_2),
    '3':  _press_and_release(EV_KEY.KEY_3),
    '4':  _press_and_release(EV_KEY.KEY_4),
    '5':  _press_and_release(EV_KEY.KEY_5),
    '6':  _press_and_release(EV_KEY.KEY_6),
    '7':  _press_and_release(EV_KEY.KEY_7),
    '8':  _press_and_release(EV_KEY.KEY_8),
    '9':  _press_and_release(EV_KEY.KEY_9),
    ':':  _shift_press_and_release(EV_KEY.KEY_SEMICOLON),
    ';':  _press_and_release(EV_KEY.KEY_SEMICOLON),
    '<':  _shift_press_and_release(EV_KEY.KEY_COMMA),
    '=':  _press_and_release(EV_KEY.KEY_EQUAL),
    '>':  _shift_press_and_release(EV_KEY.KEY_DOT),
    '?':  _shift_press_and_release(EV_KEY.KEY_SLASH),
    '@':  _shift_press_and_release(EV_KEY.KEY_2),
    'A':  _shift_press_and_release(EV_KEY.KEY_A),
    'B':  _shift_press_and_release(EV_KEY.KEY_B),
    'C':  _shift_press_and_release(EV_KEY.KEY_C),
    'D':  _shift_press_and_release(EV_KEY.KEY_D),
    'E':  _shift_press_and_release(EV_KEY.KEY_E),
    'F':  _shift_press_and_release(EV_KEY.KEY_F),
    'G':  _shift_press_and_release(EV_KEY.KEY_G),
    'H':  _shift_press_and_release(EV_KEY.KEY_H),
    'I':  _shift_press_and_release(EV_KEY.KEY_I),
    'J':  _shift_press_and_release(EV_KEY.KEY_J),
    'K':  _shift_press_and_release(EV_KEY.KEY_K),
    'L':  _shift_press_and_release(EV_KEY.KEY_L),
    'M':  _shift_press_and_release(EV_KEY.KEY_M),
    'N':  _shift_press_and_release(EV_KEY.KEY_N),
    'O':  _shift_press_and_release(EV_KEY.KEY_O),
    'P':  _shift_press_and_release(EV_KEY.KEY_P),
    'Q':  _shift_press_and_release(EV_KEY.KEY_Q),
    'R':  _shift_press_and_release(EV_KEY.KEY_R),
    'S':  _shift_press_and_release(EV_KEY.KEY_S),
    'T':  _shift_press_and_release(EV_KEY.KEY_T),
    'U':  _shift_press_and_release(EV_KEY.KEY_U),
    'V':  _shift_press_and_release(EV_KEY.KEY_V),
    'W':  _shift_press_and_release(EV_KEY.KEY_W),
    'X':  _shift_press_and_release(EV_KEY.KEY_X),
    'Y':  _shift_press_and_release(EV_KEY.KEY_Y),
    'Z':  _shift_press_and_release(EV_KEY.KEY_Z),
    '[':  _press_and_release(EV_KEY.KEY_LEFTBRACE),
    '\\': _press_and_release(EV_KEY.KEY_BACKSLASH),
    ']':  _press_and_release(EV_KEY.KEY_RIGHTBRACE),
    '^':  _shift_press_and_release(EV_KEY.KEY_6),
    '_':  _shift_press_and_release(EV_KEY.KEY_MINUS),
    '`':  _press_and_release(EV_KEY.KEY_GRAVE),
    'a':  _press_and_release(EV_KEY.KEY_A),
    'b':  _press_and_release(EV_KEY.KEY_B),
    'c':  _press_and_release(EV_KEY.KEY_C),
    'd':  _press_and_release(EV_KEY.KEY_D),
    'e':  _press_and_release(EV_KEY.KEY_E),
    'f':  _press_and_release(EV_KEY.KEY_F),
    'g':  _press_and_release(EV_KEY.KEY_G),
    'h':  _press_and_release(EV_KEY.KEY_H),
    'i':  _press_and_release(EV_KEY.KEY_I),
    'j':  _press_and_release(EV_KEY.KEY_J),
    'k':  _press_and_release(EV_KEY.KEY_K),
    'l':  _press_and_release(EV_KEY.KEY_L),
    'm':  _press_and_release(EV_KEY.KEY_M),
    'n':  _press_and_release(EV_KEY.KEY_N),
    'o':  _press_and_release(EV_KEY.KEY_O),
    'p':  _press_and_release(EV_KEY.KEY_P),
    'q':  _press_and_release(EV_KEY.KEY_Q),
    'r':  _press_and_release(EV_KEY.KEY_R),
    's':  _press_and_release(EV_KEY.KEY_S),
    't':  _press_and_release(EV_KEY.KEY_T),
    'u':  _press_and_release(EV_KEY.KEY_U),
    'v':  _press_and_release(EV_KEY.KEY_V),
    'w':  _press_and_release(EV_KEY.KEY_W),
    'x':  _press_and_release(EV_KEY.KEY_X),
    'y':  _press_and_release(EV_KEY.KEY_Y),
    'z':  _press_and_release(EV_KEY.KEY_Z),
    '{':  _shift_press_and_release(EV_KEY.KEY_LEFTBRACE),
    '|':  _shift_press_and_release(EV_KEY.KEY_BACKSLASH),
    '}':  _shift_press_and_release(EV_KEY.KEY_RIGHTBRACE),
    '~':  _shift_press_and_release(EV_KEY.KEY_GRAVE),
}

KEYNAME_TO_CHAR = {
    # Taken from ../../key_combo.py but filtered to ASCII characters only
    'ampersand'         :     '&', # &
    'apostrophe'        :     "'", # '
    'asciicircum'       :     '^', # ^
    'asciitilde'        :     '~', # ~
    'asterisk'          :     '*', # *
    'at'                :     '@', # @
    'backslash'         :    '\\', # \
    'bar'               :     '|', # |
    'braceleft'         :     '{', # {
    'braceright'        :     '}', # }
    'bracketleft'       :     '[', # [
    'bracketright'      :     ']', # ]
    'colon'             :     ':', # :
    'comma'             :     ',', # ,
    'dollar'            :     '$', # $
    'equal'             :     '=', # =
    'exclam'            :     '!', # !
    'grave'             :     '`', # `
    'greater'           :     '>', # >
    'less'              :     '<', # <
    'minus'             :     '-', # -
    'numbersign'        :     '#', # #
    'parenleft'         :     '(', # (
    'parenright'        :     ')', # )
    'percent'           :     '%', # %
    'period'            :     '.', # .
    'plus'              :     '+', # +
    'question'          :     '?', # ?
    'quotedbl'          :     '"', # "
    'quoteleft'         :     '`', # `
    'quoteright'        :     "'", # '
    'return'            :    '\r', #
    'semicolon'         :     ';', # ;
    'slash'             :     '/', # /
    'space'             :     ' ', #
    'tab'               :    '\t', #
    'underscore'        :     '_', # _
}

def _char_to_input_events(char) -> Iterable[InputEvent]:
    if char in LATIN_CHAR_TO_INPUT_EVENTS_DICT:
        return LATIN_CHAR_TO_INPUT_EVENTS_DICT[char]
    else:
        return _char_to_unicode_sequence(char)

def _char_to_unicode_sequence(char) -> Iterable[InputEvent]:
    """Unlike X11 here we are limited to emulating keys hit on a keyboard.

    See
    https://en.wikipedia.org/wiki/Unicode_input#In_X11_(Linux_and_other_Unix_variants_including_ChromeOS)
    for details on different ways to input Unicode in Linux on a keyboard.
    """
    return chain.from_iterable(chain(
        [UNICODE_INPUT_INIT_EVENT_SEQUENCE],
        map(_char_to_input_events, '%x' % ord(char)),
        [UNICODE_INPUT_END_EVENT_SEQUENCE]
    ))


class KeyboardCapture(Capture):

    def __init__(self):
        super().__init__()
        self._suppressed_keys = set()
        raise NotImplementedError()

    def start(self):
        raise NotImplementedError()

    def cancel(self):
        raise NotImplementedError()

    def suppress(self, suppressed_keys=()):
        raise NotImplementedError()


class KeyboardEmulation(Output):

    _evdev: Device

    def __init__(self):
        super().__init__()
        evdev = Device()
        evdev.name = PLOVER_DEVICE_NAME
        for attr in dir(EV_KEY):
            event = getattr(EV_KEY, attr)
            if isinstance(event, EventCode) and event.is_defined and event.name.startswith('KEY_'):
                evdev.enable(event)
        self._evdev = evdev.create_uinput_device()

    def _send_events(self, events: Iterable[InputEvent]):
        self._evdev.send_events(list(events))

    def send_backspaces(self, count: int):
        for _ in range(count):
            self._send_events([BACKSPACE_PRESS, SYN_REPORT, BACKSPACE_RELEASE, SYN_REPORT])

    def send_string(self, string: str):
        char_event_sequences = map(_char_to_input_events, string)
        self._send_events(chain.from_iterable(char_event_sequences))

    def send_key_combination(self, combo: str):

        raise NotImplementedError()

