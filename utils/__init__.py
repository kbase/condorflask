import htcondor


def get_schedd(pool=None, schedd_name=None):
    if schedd_name:
        collector = htcondor.Collector(pool)
        return htcondor.Schedd(collector.locate(
            htcondor.DaemonTypes.Schedd,
            schedd_name
        ))
    else:
        return htcondor.Schedd()
