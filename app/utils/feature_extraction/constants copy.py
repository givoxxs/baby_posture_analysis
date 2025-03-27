"""Constants for feature extraction."""

# MediaPipe Pose keypoint indices
# Face/Head
NOSE = 0
LEFT_EYE = 1
RIGHT_EYE = 2
LEFT_EAR = 3
RIGHT_EAR = 4

# Upper body
LEFT_SHOULDER = 5
RIGHT_SHOULDER = 6
LEFT_ELBOW = 7
RIGHT_ELBOW = 8
LEFT_WRIST = 9
RIGHT_WRIST = 10

# Lower body
LEFT_HIP = 11
RIGHT_HIP = 12
LEFT_KNEE = 13
RIGHT_KNEE = 14
LEFT_ANKLE = 15
RIGHT_ANKLE = 16

# Common bone pairs for vector extraction
BONE_PAIRS = [
    (LEFT_SHOULDER, LEFT_ELBOW),    # Left upper arm
    (RIGHT_SHOULDER, RIGHT_ELBOW),  # Right upper arm
    (LEFT_ELBOW, LEFT_WRIST),       # Left forearm
    (RIGHT_ELBOW, RIGHT_WRIST),     # Right forearm
    (LEFT_HIP, LEFT_KNEE),          # Left thigh
    (RIGHT_HIP, RIGHT_KNEE),        # Right thigh
    (LEFT_KNEE, LEFT_ANKLE),        # Left calf
    (RIGHT_KNEE, RIGHT_ANKLE),      # Right calf
    (LEFT_SHOULDER, RIGHT_SHOULDER), # Shoulders line
    (LEFT_HIP, RIGHT_HIP),          # Hips line
    (LEFT_SHOULDER, LEFT_HIP),      # Left torso
    (RIGHT_SHOULDER, RIGHT_HIP),    # Right torso
]

# Face keypoints for occlusion detection
FACE_KEYPOINTS = [NOSE, LEFT_EYE, RIGHT_EYE, LEFT_EAR, RIGHT_EAR]

# Hand keypoints that might occlude the face
HAND_KEYPOINTS = [LEFT_WRIST, RIGHT_WRIST]
