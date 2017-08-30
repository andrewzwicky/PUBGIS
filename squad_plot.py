from pubgis import PUBGIS

players = ["breaK", "aimpr", "viss", "smak"]

videos = {"breaK": "E:\Movies\OBS\gamescom_squads_g1_tsm_break.mkv",
          "aimpr": "E:\Movies\OBS\gamescom_squads_g1_tsm_aimpr.mkv",
          "viss": "E:\Movies\OBS\gamescom_squads_g1_tsm_viss.mkv",
          "smak": "E:\Movies\OBS\gamescom_squads_g1_tsm_smak.mkv"}

plane_start_frames = {"breaK": 610,
                      "aimpr": 560,
                      "viss": 585,
                      "smak": 585}

jump_frames = {"breaK": 1850,
               "aimpr": 1790,
               "viss": 1790,
               "smak": 1790}

landing_frames = {"breaK": 5000,
                  "aimpr": 5270,
                  "viss": 4970,
                  "smak": 5270}

death_frames = {"breaK": 53000,
                "aimpr": 54400,
                "viss": 34000,
                "smak": 52500}

colors = {"breaK": (255, 255, 255),
          "aimpr": (255, 0, 0),
          "viss": (0, 255, 0),
          "smak": (0, 0, 255)}


def process_matches():
    matches_coords = []

    for player in players:
        match = PUBGIS(video_file=videos[player],
                       start_delay=landing_frames[player],
                       color=colors[player])

        matches_coords.append(match.process_match())

    return matches_coords


if __name__ == "__main__":
    process_matches()
