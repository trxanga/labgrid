import os
import pexpect
import pytest

@pytest.fixture
def power_env(tmpdir):
    p = tmpdir.join("config.yaml")
    p.write(
"""
targets:
  main:
    drivers:
      ManualPowerDriver: {}
"""
    )
    return p

@pytest.fixture
def pw_cycle_test(tmpdir):
    t = tmpdir.join("pw_cycle_test.py")
    t.write(
"""
def test(target):
    pw = target.get_driver("ManualPowerDriver")
    pw.cycle()
"""
    )
    return t


@pytest.mark.parametrize(
    "color_scheme,pytest_extra_param,",
    (
        ("", ""),
        ("", "--lg-colored-steps"),
        ("dark", "--lg-colored-steps"),
        ("light", "--lg-colored-steps"),
    )
)
def test_step_reporter(power_env, pw_cycle_test, color_scheme, pytest_extra_param):
    from colors import strip_color

    env = os.environ.copy()
    if color_scheme:
        env["LG_COLOR_SCHEME"] = color_scheme

    # step reporter is called when -vv is given
    # -s is necessary for manual power driver confirmation
    with pexpect.spawn('pytest -vvs {param} --lg-env {env} {test}'
        .format(param=pytest_extra_param, env=power_env, test=pw_cycle_test), env=env) as spawn:

        # rough match
        spawn.expect("cycle.*?state.*?=.*?start.*?\r\n")
        step_line = strip_color(spawn.after.decode("utf-8")).rstrip()
        # exact match
        assert step_line.endswith("cycle state='start'")

        spawn.expect("main: CYCLE the target None and press enter")
        spawn.sendline()

        # rough match
        spawn.expect("cycle.*?state.*?=.*?stop.*?\r\n")
        step_line = strip_color(spawn.after.decode("utf-8")).rstrip()
        # exact match
        assert step_line.endswith("cycle state='stop'")

        spawn.expect(pexpect.EOF)
        spawn.close()
        assert spawn.exitstatus == 0
