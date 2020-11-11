'''
A Naïve approach to assigning a GPS value to every frame of each video by 
subtracting the time estimates for each frame and finding the 
GPS reading with the minimum absolute difference 

Associating GPS readings with a frame of a video
'''
import xml.etree.ElementTree as ET
import csv

def time2secs(time):  # Convert a string representation of a H:M:S into the number of seconds
    Hours, Min, Sec = [int(i) for i in time.split(":")]
    return 360 * Hours + 60 * Min + Sec


tree = ET.parse(
    'raw_data/main_boat_position/onboard_gps_source1/AI Tracks at Sea High Frequency GPS_train.txt')
root = tree.getroot()
readings = list()
for entry in root.iter("trkpt"):
    readings.append((entry.find("time").text.split("T")[1][:-1],\
                  float(entry.attrib["lat"]), float(entry.attrib["lon"]))) # (Time in seconds, latitude, longitude)

frame_times = dict()
def dist(p1,p2):
    return (((p1[0]-p2[0])**2)+((p1[1]-p2[1])**2)) ** .5
    
for i in range(6, 23):
    frame_times[i] = dict()
    with open(f"raw_data/camera_gps_logs/SOURCE_GPS_LOG_{i}_cleaned.csv","r") as f:
       content = f.readlines()
       content = content[1:] # Skip Header
    for entry in content:  
        frame_id, utc_time, _, _, est_time = entry.split(",")
        frame_times[i][frame_id] = utc_time.strip()
try:
    files = dict()
    [files.update({i : open(f"generated_data/frame2gps/frame2gps.{i}.csv", "w+")}) for i in frame_times]
    writers = dict()
    for _file in files:
        fields = ['Frame No.','Frame Time','GPS Time', 'Latitude', 'Longitude']  
        csvwriter = csv.writer(files[_file])  
        csvwriter.writerow(fields)  
        writers[_file] = csvwriter
    results = dict()
    # * Could I optimize this... definitely. Is it worth the mental effort probably not
    for video in frame_times:
        last_best = None
        results[video] = []
        for frame in frame_times[video]:
            best_reading = None
            best_score = 999999999
            for reading in readings:
                score = abs(time2secs(frame_times[video][frame]) - time2secs(reading[0]))
                if (score < best_score) and (score <= 5):
                    best_reading = reading 
                    best_score = score
            if last_best != best_reading and best_reading != None:
                # Store to Filter Later 
                results[video].append([frame, frame_times[video][frame], best_reading[0], best_reading[1], best_reading[2]])

    # Filter # ? I havent evalutated the helpulness of this fully 
    for res in results:
        writers[res].writerow(results[res][0])
        for i in range(1, len(results[res]) - 1):
            prev_pnt = [results[res][i-1][3],results[res][i-1][4]]
            this_pnt = [results[res][i][3],    results[res][i][4]]
            next_pnt = [results[res][i+1][3],results[res][i+1][4]]
            if dist(prev_pnt, next_pnt) >= dist(prev_pnt, this_pnt):
                writers[res].writerow(results[res][i])
        writers[res].writerow(results[res][-1])
finally:  
    for _file in files:
        files[_file].close()