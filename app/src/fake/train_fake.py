import os
import glob
import librosa
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
#log reg
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix
import joblib

def extract_mfcc_features(audio_path, n_mfcc=200, n_fft=2048, hop_length=512):
	try:
		audio_data, sr = librosa.load(audio_path, sr=None)
	except Exception as e:
		print(f"Error loading audio file {audio_path}: {e}")
		return None

	mfccs = librosa.feature.mfcc(y=audio_data, sr=sr, n_mfcc=n_mfcc, n_fft=n_fft, hop_length=hop_length)
	return np.mean(mfccs.T, axis=0)

def create_dataset(directory, label):
	X, y = [], []
	audio_files = glob.glob(os.path.join(directory, "*.wav"))
	for audio_path in audio_files:
		mfcc_features = extract_mfcc_features(audio_path)
		if mfcc_features is not None:
			X.append(mfcc_features)
			y.append(label)
		else:
			print(f"Skipping audio file {audio_path}")

	print("Number of samples in", directory, ":", len(X))
	print("Filenames in", directory, ":", [os.path.basename(path) for path in audio_files])
	return X, y


def train_model(X, y):
	unique_classes = np.unique(y)
	print("Unique classes in y_train:", unique_classes)

	if len(unique_classes) < 2:
		raise ValueError("Atleast 2 set is required to train")

	print("Size of X:", X.shape)
	print("Size of y:", y.shape)
	
	mean_accuracy = 0
	for i in range(20):
		X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.1, random_state=i, stratify=y)

		print("Size of X_train:", X_train.shape)
		print("Size of X_test:", X_test.shape)
		print("Size of y_train:", y_train.shape)
		print("Size of y_test:", y_test.shape)

		scaler = StandardScaler()
		X_train_scaled = scaler.fit_transform(X_train)

		if X_test is not None:
			X_test_scaled = scaler.transform(X_test)

			svm_classifier = SVC(kernel='rbf', random_state=50, probability=True)
			# svm_classifier = LogisticRegression(random_state=42, max_iter=1000)
			for _ in range(100):
				svm_classifier.fit(X_train_scaled, y_train)

			y_pred = svm_classifier.predict(X_test_scaled)

			accuracy = accuracy_score(y_test, y_pred)
			confusion_mtx = confusion_matrix(y_test, y_pred)
			mean_accuracy += accuracy

			print("Accuracy:", accuracy)
			print("Confusion Matrix:")
			print(confusion_mtx)
		else:
			print("Insufficient samples for stratified splitting. Combine both classes into one for training.")
			print("Train on all available data.")

			svm_classifier = SVC(kernel='logistic', random_state=42)
			svm_classifier.fit(X_train_scaled, y_train)
	mean_accuracy /= 20
	print("Mean Accuracy:", mean_accuracy)
	# Save the trained SVM model and scaler src/fake/model
	model_filename = "svm_model.pkl"
	scaler_filename = "scaler.pkl"
	joblib.dump(svm_classifier, "src/fake/model/" + model_filename)
	joblib.dump(scaler, "src/fake/model/" + scaler_filename)

def analyze_audio(input_audio_path):
	model_filename = "svm_model.pkl"
	scaler_filename = "scaler.pkl"
	svm_classifier = joblib.load(model_filename)
	scaler = joblib.load(scaler_filename)

	if not os.path.exists(input_audio_path):
		print("Error: The specified file does not exist.")
		return
	elif not input_audio_path.lower().endswith(".wav"):
		print("Error: The specified file is not a .wav file.")
		return

	mfcc_features = extract_mfcc_features(input_audio_path)

	if mfcc_features is not None:
		mfcc_features_scaled = scaler.transform(mfcc_features.reshape(1, -1))
		prediction = svm_classifier.predict(mfcc_features_scaled)
		if prediction[0] == 0:
			print("The input audio is classified as genuine.")
		else:
			print("The input audio is classified as deepfake.")
	else:
		print("Error: Unable to process the input audio.")

def main():
	genuine_dir = r"real_audio"
	deepfake_dir = r"deepfake_audio"

	X_genuine, y_genuine = create_dataset(genuine_dir, label=0)
	X_deepfake, y_deepfake = create_dataset(deepfake_dir, label=1)

	# Check if each class has at least two samples
	if len(X_genuine) < 2 or len(X_deepfake) < 2:
		print("Each class should have at least two samples for stratified splitting.")
		print("Combining both classes into one for training.")
		X = np.vstack((X_genuine, X_deepfake))
		y = np.hstack((y_genuine, y_deepfake))
	else:
		X = np.vstack((X_genuine, X_deepfake))
		y = np.hstack((y_genuine, y_deepfake))

	train_model(X, y)

if __name__ == "__main__":
	main()

	# user_input_file = input("Enter the path of the .wav file to analyze: ")
	# analyze_audio(user_input_file)