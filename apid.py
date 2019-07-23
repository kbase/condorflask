import re
import subprocess
import json

from flask import Flask
from flask_restful import Resource, Api, abort, reqparse

app = Flask(__name__)
api = Api(app)


def validate_attribute(attribute):
    """Return True if the given attribute is a valid classad attribute name"""
    return bool(re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", attribute))


def validate_projection(projection):
    """Return True if the given projection has a valid format, i.e.
    is a comma-separated list of valid attribute names.
    """
    return all(validate_attribute(x) for x in projection.split(","))


class JobsBaseResource(Resource):
    """Base class for endpoints for accessing current and historical job
    information. This class must be overridden to specify `executable`.

    """
    executable = ""

    def query(self, clusterid, procid, constraint, projection, attribute):
        if not self.executable:
            raise ValueError("Need to override executable")

        cmd = [self.executable, "-json"]
        if clusterid is not None:
            x = "%d" % clusterid
            if procid is not None:
                x += ".%d" % procid
            cmd.append(x)

        if constraint:
            cmd.extend(["-constraint", constraint])

        if attribute:
            if not validate_attribute(attribute):
                abort(400, message="Invalid attribute")
            cmd.extend(["-attributes", attribute])
        elif projection:
            if not validate_projection(projection):
                abort(400, message="Invalid projection: must be a comma-separated list of classad attributes")
            cmd.extend(["-attributes", projection + ",clusterid,procid"])

        classads = self._run_cmd(cmd)

        if attribute:
            data = classads[0][attribute]
            return data
        data = []
        for ad in classads:
            job_data = dict()
            job_data["classad"] = {k.lower(): v for k, v in ad.items()}
            job_data["jobid"] = "%s.%s" % (job_data["classad"]["clusterid"], job_data["classad"]["procid"])
            data.append(job_data)
        return data

    def get(self, clusterid=None, procid=None, attribute=None):
        parser = reqparse.RequestParser(trim=True)
        parser.add_argument("projection", default="")
        parser.add_argument("constraint", default="")
        args = parser.parse_args()
        return self.query(clusterid, procid, projection=args.projection, constraint=args.constraint,
                          attribute=attribute)

    def _run_cmd(self, cmd):
        completed = subprocess.run(cmd, capture_output=True, encoding="utf-8")
        if completed.returncode != 0:
            # lazy
            abort(400, message=completed.stderr)

        # super lazy here - the real deal would use the API anyway
        classads = json.loads(completed.stdout)
        if not classads:
            abort(404, message="No job(s) found")

        return classads


class JobsResource(JobsBaseResource):
    """Endpoints for accessing information about jobs in the queue
    """
    executable = "condor_q"


class HistoryResource(JobsBaseResource):
    """Endpoints for accessing historical job information
    """
    executable = "condor_history"


class StatusResource(Resource):
    """Endpoints for accessing condor_status information
    """
    def get(self, name=None):
        parser = reqparse.RequestParser(trim=True)
        parser.add_argument("projection", default="")
        parser.add_argument("constraint", default="")
        parser.add_argument("query", choices=[
            "absent", "avail", "ckptsrvr", "claimed", "cod", "collector",
            "data", "defrag", "java", "vm", "license", "master", "grid",
            "run", "schedd", "server", "startd", "generic", "negotiator",
            "storage", "any", "state", "submitters"
        ])
        args = parser.parse_args()

        cmd = ["condor_status", "-json"]

        if name:
            cmd.append(name)

        if args.query:
            cmd.append("-%s" % args.query)

        if args.constraint:
            cmd.extend(["-constraint", args.constraint])
        if args.projection:
            if not validate_projection(args.projection):
                abort(400, message="Invalid projection: must be a comma-separated list of classad attributes")
            cmd.extend(["-attributes", args.projection + ",name"])

        completed = subprocess.run(cmd, capture_output=True, encoding="utf-8")
        if completed.returncode != 0:
            # lazy
            if re.search(r"^condor_status: unknown host", completed.stderr, re.MULTILINE):
                abort(404, message=completed.stderr)
            else:
                abort(400, message=completed.stderr)

        # super lazy here - the real deal would use the API anyway
        classads = json.loads(completed.stdout)
        if not classads:
            abort(404, message="No ad(s) found")

        # lowercase all the keys
        classads_lower = [{k.lower(): v for k, v in ad.items()} for ad in classads]

        data = [
            {"name": ad["name"],
             "classad": ad} for ad in classads_lower
        ]

        return data


class ConfigResource(Resource):
    """Endpoints for accessing condor config
    """
    def get(self, attribute=None):
        parser = reqparse.RequestParser(trim=True)
        parser.add_argument("daemon", choices=["master", "schedd", "startd", "collector", "negotiator"])
        args = parser.parse_args()

        cmd = ["condor_config_val", "-raw"]
        if args.daemon:
            cmd.append("-%s" % args.daemon)

        if attribute:
            if not validate_attribute(attribute):
                abort(400, message="Invalid attribute")
            cmd.append(attribute)
        else:
            cmd.append("-dump")

        completed = subprocess.run(cmd, capture_output=True, encoding="utf-8")
        if completed.returncode != 0:
            # lazy
            if re.search(r"^Not defined:", completed.stderr, re.MULTILINE):
                abort(404, message=completed.stderr)
            else:
                abort(400, message=completed.stderr)

        if attribute:
            return completed.stdout.rstrip("\n")
        else:
            data = {}
            for line in completed.stdout.split("\n"):
                if line.startswith("#"): continue
                if " = " not in line: continue
                key, value = line.split(" = ", 1)
                data[key.lower()] = value
            return data


api.add_resource(JobsResource,
                 "/v1/jobs",
                 "/v1/jobs/<int:clusterid>",
                 "/v1/jobs/<int:clusterid>/<int:procid>",
                 "/v1/jobs/<int:clusterid>/<int:procid>/<attribute>")
api.add_resource(HistoryResource,
                 "/v1/history",
                 "/v1/history/<int:clusterid>",
                 "/v1/history/<int:clusterid>/<int:procid>",
                 "/v1/history/<int:clusterid>/<int:procid>/<attribute>")
api.add_resource(StatusResource,
                 "/v1/status",
                 "/v1/status/<name>")
api.add_resource(ConfigResource,
                 "/v1/config",
                 "/v1/config/<attribute>")
