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


def checked_get_json(uri, params=None):
    return checked_get(uri, params=params).json()


def test_condor_version(fixtures):
    r = checked_get("v1/config/condor_version")
    assert re.search(r"\d+\.\d+\.\d+", r.text), "Unexpected condor_version"


def test_status(fixtures):
    for daemon in ["collector", "master", "negotiator", "schedd", "startd"]:
        r = checked_get("v1/status/" + daemon)
        j = r.json()
        for attr in ["name", "classad"]:
            assert j[0].get(attr), "%s: %s attr missing" % (daemon, attr)


def check_job_attrs(job):
    for attr in ["classad", "jobid"]:
        assert job.get(attr), "%s attr missing" % attr


def test_history(fixtures):
    j = checked_get_json("v1/history")
    check_job_attrs(j[0])


def submit_job():
    """Submit a sleep job and return the cluster ID"""
    sub = htcondor.Submit({
        "Executable": "/usr/bin/sleep",
        "Arguments": "300",
    })
    schedd = htcondor.Schedd()
    with schedd.transaction() as txn:
        cluster_id = sub.queue(txn)
    return cluster_id


def rm_cluster(cluster_id):
    schedd = htcondor.Schedd()
    schedd.act(htcondor.JobAction.Remove, "ClusterId == %d" % cluster_id)


def test_jobs(fixtures):
    cluster_id = submit_job()
    queries = ["v1/jobs", "v1/jobs/%d" % cluster_id, "v1/jobs/%d/0" % cluster_id]
    for q in queries:
        j = checked_get_json(q)
        check_job_attrs(j[0])
    rm_cluster(cluster_id)
