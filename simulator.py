"""
BioPulse-Z Telemetry Simulator
Continuous bedside vitals streaming with real-time pathology injection.
"""
import random
from typing import Dict, List

class BedMonitorSimulator:
    def __init__(self, bed_ids: List[str]):
        self.bed_ids = bed_ids
        self.states: Dict[str, dict] = {}
        self.anomalous_beds = set()
        
        for b in bed_ids:
            self.states[b] = {
                "hr": random.randint(68, 78),
                "sbp": random.randint(118, 126),
                "dbp": random.randint(74, 82),
                "rr": random.randint(14, 17),
                "spo2": random.randint(97, 99),
                "trend": [random.randint(70, 75) for _ in range(6)]
            }
        
        # Bed-04 and Bed-08 default to pathological drift for demonstration
        self.inject_pathology("BED-04")
        self.inject_pathology("BED-08")

    def inject_pathology(self, bed_id: str):
        self.anomalous_beds.add(bed_id)

    def resolve_pathology(self, bed_id: str):
        if bed_id in self.anomalous_beds:
            self.anomalous_beds.remove(bed_id)
            self.states[bed_id]["hr"] = 74
            self.states[bed_id]["sbp"] = 120
            self.states[bed_id]["dbp"] = 78
            self.states[bed_id]["rr"] = 15
            self.states[bed_id]["spo2"] = 98

    def tick(self) -> List[dict]:
        payloads = []
        for bed_id in self.bed_ids:
            st = self.states[bed_id]
            is_anomaly = bed_id in self.anomalous_beds
            
            if is_anomaly:
                st["hr"] = int(min(145, max(100, st["hr"] + random.choice([-1, 0, 1, 2]))))
                st["sbp"] = int(max(75, min(95, st["sbp"] + random.choice([-2, -1, 0, 1]))))
                st["dbp"] = int(max(45, min(62, st["dbp"] + random.choice([-1, 0, 1]))))
                st["rr"] = int(min(32, max(22, st["rr"] + random.choice([-1, 0, 1]))))
                st["spo2"] = int(max(88, min(93, st["spo2"] + random.choice([-1, 0, 0, 1]))))
            else:
                st["hr"] = int(min(90, max(60, st["hr"] + random.choice([-1, 0, 1]))))
                st["sbp"] = int(min(135, max(110, st["sbp"] + random.choice([-1, 0, 1]))))
                st["dbp"] = int(min(85, max(68, st["dbp"] + random.choice([-1, 0, 1]))))
                st["rr"] = int(min(19, max(12, st["rr"] + random.choice([-1, 0, 1]))))
                st["spo2"] = int(min(100, max(95, st["spo2"] + random.choice([0, 0, 0, 1, -1]))))

            st["trend"].append(st["hr"])
            if len(st["trend"]) > 6:
                st["trend"].pop(0)

            payloads.append({
                "bed_id": bed_id,
                "hr": st["hr"],
                "sbp": st["sbp"],
                "dbp": st["dbp"],
                "rr": st["rr"],
                "spo2": st["spo2"],
                "trend": list(st["trend"])
            })
        return payloads