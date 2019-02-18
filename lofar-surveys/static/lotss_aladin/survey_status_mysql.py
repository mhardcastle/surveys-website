#!/usr/bin/env python


"""Retrieve LoTSS status from the Survey database and produce a JSON
file summarising the status of the pointings."""


from mysql.connector import MySQLConnection
import json


DEFAULT_OUTFILE = "pointings_db.json"

db = {
        "database": "surveys",
        "user": "survey_user",
        "password": "150megahertz"
     }


class LoTSS_Status(object):

    def __init__(self, db_info):
        self.db_info = db_info
        self.pointings = None


    def get_status(self):
        """Determines the survey status from the DB

        Connects to the database and creates a 'pointings'
        dict representing the status of the survey. The
        pointings dict is returned and also stored as the
        'pointings' attribute of the object.

        Returns:
            A dict of the following form:

            {
                "P23Hetdex20": {
                    "RA": 185.29, 
                    "DEC": 47.49, 
                    "status": "Archived", 
                    "obs": [
                        {
                            "id": 232875,
                            "status": "DI_processed",
                            "date": datetime(2014, 06, 28, 13, 00, 00"),
                            ...
                        }
                    ]
                }
            }
        """

        db_connection = MySQLConnection(**self.db_info)
        cursor = db_connection.cursor()
        pointings = {}

        cursor.execute("SELECT id, status, ra, decl FROM fields;")
        fields_query = cursor.fetchall()
        for field, status, ra, dec in fields_query:
            pointings[field] = {"RA": ra, "DEC": dec, "status": status, "obs": []}
    
        cursor.execute("SELECT * FROM observations;")
        cols = cursor.column_names
        obs_query = cursor.fetchall()
        for obs_row in obs_query:
            obs = dict(zip(cols, obs_row))
            if obs["field"] in pointings:
                pointings[obs["field"]]["obs"].append(obs)
    
        self.pointings = pointings
        return pointings


    def save(self, filename=DEFAULT_OUTFILE, float_precision=2):
        """Write out a condensed version of the pointings information in JSON format.

        Example:
        [["P8Hetdex28", 191.65, 45.33, "Done", [{"id": 239680, "status": "DI_processed", "date": "2014-07-28"}]]]

        Args:
            filename: name of the output JSON file.
            float_precision: how many digits after the decimal point the 'ra' and 'dec' values will have.

        Returns: None
        """

        if self.pointings == None:
            self.get_status()
        out_data = []
        for key, value in self.pointings.items():
            pstatus = self._pointing_status(value)
            obs = [self._trim_obs(o) for o in value["obs"]]
            pointing_info = [key, round(value["RA"], float_precision), round(value["DEC"], float_precision), pstatus, obs]
            out_data.append(pointing_info)
        json.dump(out_data, open(filename, "w"))
    

    @staticmethod
    def _trim_obs(obs):
        """Return dict with only 'id', 'status', 'date' present."""
        obs_out = obs.copy()
        for key in obs:
            if key not in ['id', 'status', 'date']:
                del obs_out[key]
        try:
            obs_out['date'] = obs['date'].strftime("%Y-%m-%d")
        except AttributeError:
            # Datetime 0000-00-00 .... gets returned as None
            obs_out['date'] = "unknown"
    
        return obs_out
    
    
    @staticmethod
    def _pointing_status(pointing):
        """Determine the status of a pointing according to critera provided by Tim Shimwell."""
        if pointing["status"] == "Archived":
            return "Done"
        elif pointing["status"] == "Failed":
            return "Failed"
        # elif pointing["status"] in ["Downloading", "Downloaded", "List failed", "Complete", "Running", "Not started", "Stopped", "Queued", "D/L failed"]:
        else:
            # The 'status' value is not constrained in the DB
            if len(pointing["obs"]) > 0:
                time_ready = sum([obs["integration"] for obs in pointing["obs"] if obs["status"] == "DI_processed"])
                if time_ready >= 7:
                    return "Ready"
                time_observed = sum([obs["integration"] for obs in pointing["obs"] if obs["status"] == "Observed"])
                if time_observed + time_ready >= 7:
                    return "Observed"
                if "Scheduled" in [obs["status"] for obs in pointing["obs"]]:
                    return "Scheduled"
                return "Other"
            else:
                # No observations present
                return "Not_Observed"
        #else:
        #    raise KeyError("Unexpected status {}".format(pointing["status"]))
    
    
if __name__ == "__main__":
    LoTSS_Status(db).save()
