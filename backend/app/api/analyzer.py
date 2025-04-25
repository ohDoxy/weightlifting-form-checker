import cv2
import mediapipe as mp
import numpy as np

def analyze_video(video_path: str, side: str = "right") -> dict:

    # Depth thresholds
    GOOD_DEPTH_THRESHOLD = 0.015    # hip clearly below knee
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
        
            # grab x, y coordinates for hip (24), knee (26), and ankle (28)
            # and calcuate the knee angle from the right side
            if results.pose_landmarks:
                lm = results.pose_landmarks.landmark
                hip = [lm[hip_idx].x, lm[hip_idx].y]
                knee = [lm[knee_idx].x, lm[knee_idx].y]
                ankle = [lm[ankle_idx].x, lm[ankle_idx].y]

                # position based depth check
                angle = calculate_angle(hip, knee, ankle)
                diff = hip[1] - knee[1] # hip and knee y coords
                frame_data.append((angle, diff))

                print(f"Frame {frame_count} | hip_y={hip[1]:.4f} | knee_y={knee[1]:.4f} | diff={diff:.4f}")


        frame_count += 1

    cap.release() # close the video

    # if no pose detected, return error message
    if not frame_data:
        return {"feedback": "No pose detected."}
    
    # Analyze bottom 5 frames (smallest knee angle)
    frame_data.sort(key=lambda x: x[0])
    bottom_frames = frame_data[:5]
    depth_value = sum(diff for _, diff in bottom_frames) / len(bottom_frames)
    
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