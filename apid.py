import re
import subprocess
import json

from flask import Flask, Response, request
from flask_restful import Resource, Api, abort, reqparse

app = Flask(__name__)
api = Api(app)


class JobsBaseResource(Resource):
    executable = ""

    def query(self, clusterid, procid, constraint, projection):
        if not self.executable:
            abort(503, message="gotta override this")

        cmd = [self.executable, "-json"]
        if procid is not None:
            if clusterid is None:
                abort(400, message="clusterid not specified")
            cmd.append("%d.%d" % (clusterid, procid))
        elif clusterid is not None:
            cmd.append("%d" % clusterid)

        if constraint:
            cmd.extend(["-constraint", constraint])

        if projection:
            cmd.extend(["-attributes", projection + ",clusterid,procid"])

        completed = subprocess.run(cmd, capture_output=True, encoding="utf-8")
        if completed.returncode != 0:
            # lazy
            abort(400, message=completed.stderr)

        # super lazy here - the real deal would use the API anyway
        classads = json.loads(completed.stdout)
        if not classads:
            abort(404, message="No jobs found")
        data = []
        for ad in classads:
            job_data = {k.lower(): v for k, v in ad.items()}
            job_data["jobid"] = "%s.%s" % (job_data["clusterid"], job_data["procid"])
            data.append(job_data)
        return data

    def get(self, clusterid=None, procid=None):
        parser = reqparse.RequestParser(trim=True)
        parser.add_argument("projection", default="")
        parser.add_argument("constraint", default="")
        args = parser.parse_args()
        return self.query(clusterid, procid, projection=args.projection, constraint=args.constraint)


class JobsResource(JobsBaseResource):
    executable = "condor_q"


class HistoryResource(JobsBaseResource):
    executable = "condor_history"


class ConfigResource(Resource):
    def get(self, attribute=None):
        parser = reqparse.RequestParser(trim=True)
        parser.add_argument("daemon", choices=["master", "schedd", "startd", "collector", "negotiator"])
        args = parser.parse_args()

        cmd = ["condor_config_val", "-raw"]
        if args.daemon:
            cmd.append("-%s" % args.daemon)

        if attribute:
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

        data = {}
        if attribute:
            data[attribute.lower()] = completed.stdout.rstrip("\n")
        else:
            for line in completed.stdout.split("\n"):
                if line.startswith("#"): continue
                if " = " not in line: continue
                key, value = line.split(" = ", 1)
                data[key.lower()] = value

        return data


api.add_resource(JobsResource, "/v1/jobs", "/v1/jobs/<int:clusterid>", "/v1/jobs/<int:clusterid>/<int:procid>")
api.add_resource(HistoryResource, "/v1/history", "/v1/history/<int:clusterid>", "/v1/history/<int:clusterid>/<int:procid>")
api.add_resource(ConfigResource, "/v1/config", "/v1/config/<attribute>")
