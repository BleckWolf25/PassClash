#!/usr/bin/env python3
"""
File: generate_wordlist.py

Version: 1.0.0
Author: BleckWolf25
License: MIT

Summary:
    Generate bundled demo wordlist with common passwords and pattern expansions.

Description:
    This script generates the demonstration wordlist used by PassClash for password
    cracking simulations. It creates a deterministic, stable-ordered list containing
    well-known real-world passwords (based on SecLists/rockyou collections) and applies
    common transformations (years, suffixes, leet substitutions, keyboard patterns) that
    people typically use. The output is small enough to ship in the repository while
    providing realistic cracking scenarios.

Usage:  python scripts/generate_wordlist.py [output.txt]

Since: 05/08/2026
Updated: 05/08/2026
"""
# ---------- IMPORTS
from __future__ import annotations

import sys
from pathlib import Path

# ---------- CONSTANTS
BASE = [
    # top of the classic lists
    "123456", "password", "12345678", "qwerty", "123456789", "12345",
    "1234", "111111", "1234567", "dragon", "123123", "baseball",
    "abc123", "football", "monkey", "letmein", "696969", "shadow",
    "master", "666666", "qwertyuiop", "123321", "mustang", "1234567890",
    "michael", "654321", "pussy", "superman", "1qaz2wsx", "7777777",
    "fuckyou", "121212", "000000", "qazwsx", "123qwe", "killer",
    "trustno1", "jordan", "jennifer", "zxcvbnm", "asdfgh", "hunter",
    "buster", "soccer", "harley", "batman", "andrew", "tigger", "sunshine",
    "iloveyou", "fuckme", "2000", "charlie", "robert", "thomas", "hockey",
    "ranger", "daniel", "starwars", "klaster", "112233", "george",
    "asshole", "computer", "michelle", "jessica", "pepper", "1111",
    "zxcvbn", "555555", "11111111", "131313", "freedom", "777777",
    "pass", "fuck", "maggie", "159753", "aaaaaa", "ginger", "princess",
    "joshua", "cheese", "amanda", "summer", "love", "ashley", "6969",
    "nicole", "chelsea", "biteme", "matthew", "access", "yankees",
    "987654321", "dallas", "austin", "thunder", "taylor", "matrix",
    "william", "corvette", "hello", "martin", "heather", "secret",
    "fucker", "merlin", "diamond", "1234qwer", "gfhjkm", "hammer",
    "silver", "222222", "88888888", "anthony", "justin", "test",
    "bailey", "q1w2e3r4t5", "patrick", "internet", "scooter", "orange",
    "11111", "golfer", "cookie", "richard", "samantha", "bigdog",
    "guitar", "jackson", "whatever", "mickey", "chicken", "sparky",
    "snoopy", "maverick", "phoenix", "camaro", "sexy", "peanut",
    "morgan", "welcome", "falcon", "cowboy", "ferrari", "samsung",
    "andrea", "smokey", "steelers", "joseph", "mercedes", "dakota",
    "arsenal", "eagles", "melissa", "boomer", "booboo", "spider",
    "nascar", "monster", "tigers", "yellow", "xxxxxx", "123123123",
    "gateway", "marina", "diablo", "bulldog", "qwer1234", "compaq",
    "purple", "hardcore", "banana", "junior", "hannah", "123654",
    "porsche", "lakers", "iceman", "money", "cowboys", "987654",
    "london", "tennis", "999999", "ncc1701", "coffee", "scooby",
    "0000", "miller", "boston", "q1w2e3r4", "fuckoff", "brandon",
    "yamaha", "chester", "mother", "forever", "johnny", "edward",
    "333333", "oliver", "redsox", "player", "nikita", "knight",
    "fender", "barney", "midnight", "please", "brandy", "chicago",
    "badboy", "iwantu", "slayer", "rangers", "charles", "angel",
    "flower", "bigdaddy", "rabbit", " wizard", "bigdick", "jasper",
    "enter", "rachel", "chris", "steven", "winner", "adidas", "victoria",
    "natasha", "1q2w3e4r", "jasmine", "winter", "prince", "panties",
    "marine", "ghbdtn", "fishing", "cocacola", "casper", "james",
    "232323", "raiders", "888888", "marlboro", "gandalf", "asdfasdf",
    "crystal", "87654321", "12344321", "sexsex", "golden", "blowme",
    "bigtits", "8675309", "panther", "lauren", "angela", "bitch",
    "spanky", "thx1138", "angels", "madison", "winston", "shannon",
    "mike", "toyota", "blowjob", "jordan23", "canada", "sophie",
    "apples", "dick", "tiger", "razz", "123abc", "pokemon", "qazxsw",
    "55555", "qwaszx", "muffin", "johnson", "murphy", "cooper",
    "jonathan", "liverpoo", "david", "danielle", "159357", "jackie",
    "1990", "123456789a", "789456123", "wilson", "michael1", "pussycat",
    "godzilla", "passw0rd", "12345qwert", "sniper", "fuck_inside",
    "qwertz", "blazer", "gabriel", "suckit", "wonderful", "married",
    "loveyou", "buddy", "12345678910", "homer", "porsche9", "matrix1",
    "spitfire", "whiskey", "teens", "bulldogs", "servers", "zagreb",
    "star", "westside", "motorola", "something", "ravens", "raiders1",
    "dragon1", "powder", "smokey1", "princess1", "diamonds", "123qweasd",
    "trustme", "warrior", "11221122", "scorpio", "cameron", "wolverine",
    "gators", "friends", "carolina", "streets", "texas", "supra",
    "wizard", "hunter2", "warcraft", "fishing1", "green", "loveme",
    "garden", "swimming", "buster1", "google", "chevy", "yankee",
    "college", "russia", "purple1", "carpediem", "mustang1", "samsung1",
    "noname123", "sexy1", "hotdog", "ashley1", "passwords", "alexis",
    "summer1", "chelsea1", "babygirl1", "killer1", "blink182", "whatever1",
    "qwerty123", "abc1234", "dolphin", "garfield", "tootsie", "stargate",
    "google123", "password1", "corvette1", "wildcats", "slipknot",
    "harley1", "batman1", "superman1", "hellfire", "daredevil", "angels1",
    "superstar", "dragonball", "metallic", "snoopy1", "michael123",
    "pepper1", "melissa1", "soccer1", "football1", "monkey1", "matrix1x",
    "123456a", "1qazxsw2", "azerty", "azertyuiop", "qwerty1", "abc12345",
    "love123", "baby123", "admin123", "root123", "test123", "demo123",
    "welcome1", "letmein1", "hacker", "hacker1", "security", "pentest",
    "password123", "p@ssword", "p@ssw0rd", "passw0rd1", "admin", "root",
    "toor", "guest", "default", "changeme", "1234abcd", "abcd1234",
]

_MONTHS = ["january", "february", "march", "april", "may", "june", "july",
           "august", "september", "october", "november", "december"]
_DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday",
         "sunday"]
_SEASONS = ["spring", "summer", "autumn", "fall", "winter"]
_SPORTS = ["football", "soccer", "baseball", "basketball", "hockey", "tennis",
           "golf", "cricket", "rugby", "volleyball"]
_TEAMS = ["lakers", "cowboys", "yankees", "raiders", "packers", "patriots",
          "steelers", "niners", "bulls", "celtics"]
_NAMES = ["michael", "jessica", "ashley", "christopher", "jennifer", "amanda",
          "matthew", "sarah", "daniel", "laura", "joshua", "melissa", "andrew",
          "nicole", "brandon", "amber", "ryan", "stephanie", "justin",
          "heather", "jacob", "megan", "kyle", "jasmine", "tyler", "michelle",
          "brian", "samantha", "kevin", "rachel", "jason", "alexis", "eric",
          "tiffany", "adam", "victoria", "joaoc", "alice", "bob", "carol",
          "dave", "eve", "frank", "grace", "henry", "ivy", "jack", "kate",
          "leo", "mia", "nina", "oscar", "peter", "quinn", "rose", "sam"]
_OBJECTS = ["dragon", "monkey", "tiger", "eagle", "falcon", "phoenix",
            "wizard", "knight", "panther", "dolphin", "shadow", "ghost",
            "phantom", "viper", "cobra", "wolf", "titan", "storm", "blaze",
            "frost", "thunder", "lightning", "rocket", "comet", "meteor"]

_YEARS = list(range(1990, 2027))
_SUFFIXES = ["1", "12", "123", "1234", "12345", "!"]

# ---------- FUNCTIONS
def expand(base_words: list[str]) -> list[str]:
    """Return a stable, de-duplicated expansion of the supplied base words."""
    out = list(dict.fromkeys(w.strip() for w in base_words if w.strip()))
    out = [w for w in out if not w.startswith(" ")]

    def add(words: list[str]) -> None:
        for w in words:
            if w not in out:
                out.append(w)

    # calendar + years
    add([f"{m}{y}" for m in _MONTHS for y in _YEARS])
    add([f"{m}1" for m in _MONTHS] + [f"{m}2024" for m in _MONTHS])
    add([f"{d}1" for d in _DAYS] + [f"{d}123" for d in _DAYS])
    add([f"{s}1" for s in _SEASONS] + [f"{s}2024" for s in _SEASONS])

    # sports/teams/names/objects + suffixes
    add([f"{w}{s}" for w in _SPORTS + _TEAMS + _OBJECTS for s in _SUFFIXES])
    add([f"{w}{y}" for w in _SPORTS + _OBJECTS for y in (2024, 2025, 2026)])
    add([f"{w}1" for w in _NAMES] + [f"{w}123" for w in _NAMES[:40]])
    add([f"{w}!" for w in _OBJECTS[:12]])

    # leet flavours of common words
    leet = {
        "password": ["p@ssw0rd", "p@ssword", "passw0rd"],
        "admin": ["@dmin", "adm1n", "@dm1n"],
        "secret": ["s3cr3t", "s3cret"],
        "hacker": ["h4cker", "hack3r"],
        "love": ["l0ve", "l0v3"],
        "dragon": ["dr@g0n", "dr4g0n"],
    }
    for variants in leet.values():
        add(variants)

    # keyboard walks
    add(["1qaz2wsx", "1qazxsw2", "qweasdzxc", "qazwsxedc", "zaq12wsx",
         "1q2w3e4r5t", "qwertyuiop[]", "asdfghjkl;", "zxcvbnm,./", "poiuytrewq",
         "mnbvcxz", "lkjhgfdsa", "0987654321", "1122334455", "31415926",
         "271828", "1029384756", "918273645", "1a2b3c4d5e", "a1b2c3d4",
         "qaz123", "wsxedc123", "asd123", "qwe123", "zxc123", "qweasd",
         "asdzxc", "qweasdzxc123"])

    # numeric favourites
    add([str(y) for y in _YEARS])
    add(["123654789", "147258369", "159753456", "753951", "369258147",
         "112233", "445566", "778899", "101010", "102030", "135790",
         "246810", "01020304", "13131313", "202020", "303030", "404040",
         "505050", "606060", "707070", "808080", "909090"])

    # paired word+word
    add([f"{w1}{w2}" for w1 in ("ilove", "fuck", "baby", "super", "master",
                                "mega", "ultra", "power") for w2 in
         ("you", "me", "1", "123", "dragon", "love")])

    return out


def main() -> int:
    """Write the bundled demonstration wordlist and return a process status."""
    out_path = Path(sys.argv[1]) if len(sys.argv) > 1 else (
        Path(__file__).resolve().parent.parent / "wordlists" / "rockyou_top5k.txt"
    )
    words = expand(BASE)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(words) + "\n", encoding="utf-8")
    print(f"wrote {len(words)} words -> {out_path}")
    return 0

# ---------- MAIN
if __name__ == "__main__":
    raise SystemExit(main())
