from config import constants
from metermind.core.exceptions import MeterMindError

ALLOWED_TRANSITIONS = {
    "raised": ("assigned",),
    "assigned": ("inspected",),
    "inspected": ("regularised", "billed_back", "closed_no_fault", "assigned"),
    "regularised": (),
    "billed_back": (),
    "closed_no_fault": (),
}


def move_case_status(current_status, wanted_status):
    if current_status not in ALLOWED_TRANSITIONS:
        raise MeterMindError(current_status)
    if wanted_status not in ALLOWED_TRANSITIONS:
        raise MeterMindError(wanted_status)

    permitted = ALLOWED_TRANSITIONS[current_status]
    if wanted_status not in permitted:
        if not permitted:
            raise MeterMindError(f"a case at {current_status} is closed")
        destinations = ", ".join(permitted)
        raise MeterMindError(
            f"a case at {current_status} may move to {destinations}, "
            f"not to {wanted_status}"
        )
    return wanted_status


if __name__ == "__main__":
    for current, wanted in (
        ("raised", "assigned"),
        ("assigned", "inspected"),
        ("raised", "closed_no_fault"),
    ):
        try:
            moved = move_case_status(current, wanted)
            print(f"{current:20} -> {wanted:20} {moved}")
        except MeterMindError as error:
            print(f"{current:20} -> {wanted:20} refused: {error}")
