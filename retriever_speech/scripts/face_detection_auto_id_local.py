#!/usr/bin/python3

import shlex
import time
import rospy
import face_recognition
import cv2
from retriever_speech.msg import user_info 

pub = rospy.Publisher("/last_see_people", user_info,queue_size=10)

def compute_face_sizes(face_locations, face_encodings):
  face_sizes = []
  max_face_size = 0
  closest_face_idx = None

  for i, face_encoding in enumerate(face_encodings):
    top, right, bottom, left = face_locations[i]
    size = (bottom-top) * (right-left)
    face_sizes.append(size)
    
    if size > max_face_size:
      max_face_size = size
      closest_face_idx = i

  return face_sizes, closest_face_idx


def match_face(known_faces, face_encoding, threshold):
  face_id = None
  min_dist = threshold

  distances = face_recognition.face_distance(known_faces, face_encoding)
  for known_face_id, dist in enumerate(distances):
    if dist <= min_dist:
      min_dist = dist
      face_id = known_face_id

  return face_id, min_dist


if __name__ == '__main__':
  rospy.init_node('face_recognition', anonymous=True)

  # Get a reference to webcam #0 (the default one)
  video_capture = cv2.VideoCapture(0)

  known_faces = []

  while not rospy.is_shutdown():
    # Grab a single frame of video
    ret, frame = video_capture.read()

    # BGR(OpenCV) to RGB(face_recognition)
    rgb_frame = frame[:, :, ::-1]

    # Find all the faces and face encodings in the current frame of video
    face_locations = face_recognition.face_locations(rgb_frame, model='hog')
    
    if len(face_locations) > 0:

      face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
      face_sizes, closest_face_idx = compute_face_sizes(face_locations, face_encodings)

      min_face_diff = 1e30
      best_match_uid = None
      best_match_idx = None
      closest_face_uid = None
      closest_face_diff = None

      for i, encoding in enumerate(face_encodings):
        matched_uid, face_diff = match_face(
          known_faces=known_faces, 
          face_encoding=encoding, 
          threshold=0.6
        )

        if i == closest_face_idx:
          closest_face_uid = matched_uid
          closest_face_diff = face_diff

        if face_diff < min_face_diff:
          min_face_diff = face_diff
          best_match_uid = matched_uid
          best_match_idx = i

      if best_match_uid is None:
        known_faces.append(face_encodings[closest_face_idx])
        user_id = len(known_faces)-1
        face_idx = closest_face_idx

      else:
        if closest_face_uid is None:
          user_id = best_match_uid
          face_idx = best_match_idx
        else:
          user_id = closest_face_uid
          face_idx = closest_face_idx
        
      
      user_face_size = face_sizes[face_idx]
      top, right, bottom, left = face_locations[face_idx]
      user = user_info()
      #cmd = f'source /opt/ros/melodic/setup.bash;source /home/benny/Documents/retriever_ws/devel/setup.bash;rostopic pub /last_see_people retriever_speech/user_info "face_area: {user_face_size} user_id: {user_id}"'


      tag = user_id
      #user.user_id = user_id
      user.user_id = 0
      user.face_area = user_face_size
      #print(f'{tag} ({user_face_size})')
      print(user_id, user_face_size)
      pub.publish(user)
      # Draw a bounding box around the face
      #cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
      #cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
      #cv2.putText(frame, tag, (left + 6, bottom - 6), cv2.FONT_HERSHEY_DUPLEX, 1.0, (255, 255, 255), 1)


    # Display the resulting image
 #   cv2.imshow('Video', frame)

    # Hit 'q' on the keyboard to quit!
 #   if cv2.waitKey(1) & 0xFF == ord('q'):
 #   	break
    #time.sleep(1)
    rospy.sleep(0.1)

  # Release handle to the webcam
  video_capture.release()
#  cv2.destroyAllWindows()

