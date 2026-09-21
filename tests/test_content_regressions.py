"""Source-reviewed regression fixtures, independent of the generated booklets.

See docs/CONTENT_AUDIT.md for the underlying rules. These protect specific
corrections from reversal; passing tests is not independent rules certification.
"""

import pytest

from benchmark_outline import grade


@pytest.mark.parametrize(
    ("number", "key"),
    [
        (7, "B"),  # Magic Missile: five darts at third level.
        (9, "C"),  # Flying Sword monster: AC 17.
        (10, "A"),  # Reframed Extra Attack question: fighter.
        (13, "C"),  # Comfortable: 2 gp/day.
        (27, "D"),  # Plate plus shield: AC 20.
        (34, "C"),  # Reframed area question: total cover blocks propagation.
        (40, "B"),  # Wall of Stone: ten minutes.
        (42, "B"),  # Identify: one minute normally, eleven as a ritual.
        (44, "B"),  # Restrained: speed zero, not halved.
        (45, "D"),  # Flying Wild Shape: level eight encoded as choice D.
        (46, "D"),  # Alchemist's supplies: 50 gp.
    ],
)
def test_corrected_multiple_choice_keys(bank, number, key):
    assert bank.items[number - 1].answer == key
    assert grade(key, bank.items[number - 1])["score"] == 1


@pytest.mark.parametrize(
    ("number", "wrong"),
    [
        (52, "Strength 13 or Charisma 13"),
        (55, "3800 XP"),  # Question explicitly asks cumulative XP.
        (60, "DC 15"),
        (63, "10 gp"),  # New spell, not copying one's existing book.
        (73, "Cannot swim"),
        (74, "1d10 + 13"),  # Constitution does not enter Second Wind.
    ],
)
def test_old_incorrect_answers_cannot_receive_credit(bank, number, wrong):
    assert grade(wrong, bank.items[number - 1])["score"] is None


def test_candidate_answers_cannot_bypass_provisional_status(bank):
    for number, proposed in [(58, "1"), (67, "+10 feet"), (68, "4 days"), (69, "3rd level")]:
        result = grade(proposed, bank.items[number - 1])
        assert result == {"status": "needs_review", "score": None, "reason": "provisional"}
