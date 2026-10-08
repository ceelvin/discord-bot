import unittest

from bot import desired_nick, strip_markers

TANK = " 🛡️"
HEAL = " 🪽"
DPS = " ⚔️"
SUFFIXES = [TANK, HEAL, DPS]
SWORD = "\u2694"
SWORD_EMOJI = "\u2694\ufe0f"
SHIELD = "\U0001f6e1"
SHIELD_EMOJI = "\U0001f6e1\ufe0f"


class Member:
    def __init__(self, nick: str, name: str | None = None) -> None:
        self.nick = nick
        self.name = name or nick.split()[0]
        self.display_name = nick


class NicknameTests(unittest.TestCase):
    def test_strip_stacked_swords(self) -> None:
        stacked = f"Vocki {SWORD} {SWORD} {SWORD} {SWORD} {SWORD_EMOJI}"
        self.assertEqual(strip_markers(stacked, SUFFIXES), "Vocki")

    def test_strip_mixed_heal_markers(self) -> None:
        self.assertEqual(strip_markers("julio 🪽 💚", SUFFIXES), "julio")
        self.assertEqual(strip_markers("[HEAL] julio 💚", SUFFIXES), "julio")

    def test_dps_keeps_exact_sword_emoji(self) -> None:
        stacked = f"Vocki {SWORD} {SWORD} {SWORD} {SWORD} {SWORD_EMOJI}"
        desired = desired_nick(Member(stacked), DPS, SUFFIXES)
        self.assertEqual(desired, f"Vocki{DPS}")
        self.assertTrue(desired.endswith(SWORD_EMOJI))
        again = desired_nick(Member(desired), DPS, SUFFIXES)
        self.assertEqual(again, desired)

    def test_existing_dps_is_stable(self) -> None:
        nick = f"Susanne{DPS}"
        desired = desired_nick(Member(nick), DPS, SUFFIXES)
        self.assertEqual(desired, nick)
        self.assertEqual(desired_nick(Member(desired), DPS, SUFFIXES), nick)

    def test_heal_replaces_legacy_heart(self) -> None:
        self.assertEqual(desired_nick(Member("julio 💚"), HEAL, SUFFIXES), f"julio{HEAL}")
        mixed = desired_nick(Member("julio 🪽 💚"), HEAL, SUFFIXES)
        self.assertEqual(mixed, f"julio{HEAL}")
        self.assertNotIn("💚", mixed)
        self.assertEqual(desired_nick(Member(mixed), HEAL, SUFFIXES), mixed)

    def test_tank_keeps_emoji_presentation(self) -> None:
        nick = f"Tank{TANK}"
        desired = desired_nick(Member(nick), TANK, SUFFIXES)
        self.assertEqual(desired, nick)
        self.assertEqual(desired[-2:], SHIELD_EMOJI)

    def test_legacy_prefix_and_heart(self) -> None:
        desired = desired_nick(Member("[HEAL] julio 💚"), HEAL, SUFFIXES)
        self.assertEqual(desired, f"julio{HEAL}")
        self.assertEqual(desired_nick(Member(desired), HEAL, SUFFIXES), desired)


if __name__ == "__main__":
    unittest.main()
