from whistlelock.doctor import run_doctor


def test_doctor_passes() -> None:
    assert run_doctor(as_json=True) == 0
