import cv2

# Open USB camera (camera 0)
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Cannot open camera")
    exit()

print("Camera opened successfully!")

try:
    while True:
        # Capture frame-by-frame
        ret, frame = cap.read()

        if not ret:
            print("Can't receive frame (stream end?). Exiting...")
            break

        # Display the resulting frame
        cv2.imshow('USB Camera Feed', frame)

        # Wait for keypress
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            # Press 'q' to quit
            break
        elif key == ord('s'):
            # Press 's' to save an image
            cv2.imwrite('snapshot.jpg', frame)
            print("Saved snapshot!")

finally:
    # Release everything when done
    cap.release()
    cv2.destroyAllWindows()