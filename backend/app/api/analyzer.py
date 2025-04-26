import cv2
import mediapipe as mp
import numpy as np

def analyze_video(video_path: str, side: str = "right") -> dict:

    # Depth thresholds
    GOOD_DEPTH_THRESHOLD = 0.002    # hip clearly below knee
    BORDERLINE_THRESHOLD = 0.0  # about parallel

    # Determine which side we are analyzing from
    if side == "left":
        hip_idx, knee_idx, ankle_idx = 23, 25, 27
    elif side == "right":
        hip_idx, knee_idx, ankle_idx = 24, 26, 28
    else:
        hip_idx, knee_idx, ankle_idx = 24, 26, 28
        print(f"[WARN] Unknown side '{side}' provided. Defaulting to right side.")
    
    # setup MediaPipe Pose and open the video file
    mp_pose = mp.solutions.pose
    pose = mp_pose.Pose()
    cap = cv2.VideoCapture(video_path)

    # read and analyze every 5th frame
    frame_count = 0
    frame_data = []

    while cap.isOpened():
        ret, frame = cap.read() # read video frame by frame
        if not ret: # stop when the video ends
            break

        # every 5th frame, convert BGR to RGB and run pose detection
        if frame_count % 5 == 0:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = pose.process(rgb)
        
            # grab x, y coordinates for hip, knee, and ankle
            if results.pose_landmarks:
                lm = results.pose_landmarks.landmark
                hip = [lm[hip_idx].x, lm[hip_idx].y]
                knee = [lm[knee_idx].x, lm[knee_idx].y]
                ankle = [lm[ankle_idx].x, lm[ankle_idx].y]

                # append hip_y, knee_y, angle triplets in an array
                angle = calculate_angle(hip, knee, ankle)
                frame_data.append((hip[1], knee[1], angle))

                print(f"Frame {frame_count} | hip_y={hip[1]:.4f} | knee_y={knee[1]:.4f}")


        frame_count += 1

    cap.release() # close the video

    # if no pose detected, return error message
    if not frame_data:
        return {"feedback": "No pose detected."}
    
    # sort the data by lowest hip_y, and take bottom 5 frames
    frame_data.sort(key=lambda x : x[0])
    bottom_frames = frame_data[:5]

    # calculate hip-knee difference for each bottom frame
    diffs = []
    for hip_y, knee_y, _ in bottom_frames:
        diff = hip_y - knee_y
        diffs.append(diff)
    
    # if less than 3 valid frames, too shallow
    if len(diffs) < 3:
        return {
            "depth_value": None,
            "side": side,
            "feedback": "Too shallow, not enough frames to analyze"
        }

    # average top 3 biggest diffs
    selected_diffs = sorted(diffs, reverse=True)[:3]
    depth_value = sum(selected_diffs) / len(selected_diffs) 
    
    # give feedback based on the average depth values
    if depth_value > GOOD_DEPTH_THRESHOLD:
        depth_feedback = "Good depth!"
    elif depth_value > BORDERLINE_THRESHOLD:
        depth_feedback = "Almost parallel, get a little lower."
    else:
        depth_feedback = "Too shallow, try to get hips lower."
    
    # return feedback as JSON
    return {
        "depth_value": round(depth_value, 4),
        "side": side,
        "feedback": depth_feedback,
    }


def calculate_angle(a, b, c):
    a, b, c = map(np.array, (a, b, c))
    ba = a - b  # vector from b to a
    bc = c - b  # vector from b to c
    cosine = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
    return np.degrees(np.arccos(np.clip(cosine, -1.0, 1.0)))