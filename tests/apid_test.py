import os
import re
import subprocess
import time

import htcondor
import pytest
import requests


URIBASE = "http://127.0.0.1:9680"


@pytest.fixture
def fixtures():
    # Check for already running condor and apid
    # Can't start them up myself b/c no root (for condor) and I can't kill
    # a flask process I start because it forks
    subprocess.check_call(["condor_ping", "DC_NOP"])
    subprocess.check_call(["curl", "-s", URIBASE])


def get(uri, params=None):
    return requests.get(URIBASE + "/" + uri, params=params)


def checked_get(uri, params=None):
    r = get(uri, params=params)
    assert 200 <= r.status_code < 400, "GET %s%s failed" % (
        uri, " with params %r" % params if params else ""
    )
    return r


def test_condor_version(fixtures):
    r = checked_get("v1/config/condor_version")
    assert re.search(r"\d+\.\d+\.\d+", r.text), "Unexpected condor_version"


def test_status(fixtures):
    for daemon in ["collector", "master", "negotiator", "schedd", "startd"]:
        r = checked_get("v1/status/" + daemon)
        j = r.json()
        for attr in ["name", "classad"]:
            assert j[0].get(attr), "%s: %s attr missing" % (daemon, attr)


def test_history(fixtures):
    r = checked_get("v1/history")
    j = r.json()
    for attr in ["classad", "jobid"]:
        assert j[0].get(attr), "%s attr missing" % (attr)
