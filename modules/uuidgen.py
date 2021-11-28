import string
import random

__all__ = {'uuid', 'LOWER', 'UPPER', 'ANY'}

LOWER = 1
UPPER = 2
ANY   = 3

__modes = {
    LOWER: string.ascii_lowercase,
    UPPER: string.ascii_uppercase,
    ANY  : string.ascii_letters
}

def uuid(__length: int, mode: int = 3):
    return ''.join(random.SystemRandom().choices([*__modes[mode], *string.digits], k=__length))