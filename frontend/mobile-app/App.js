import React, { useState } from 'react';
import { StyleSheet, Button, Image, Platform, Text, View } from 'react-native';
import * as ImagePicker from 'expo-image-picker'; // pick videos from gallery
import * as FileSystem from 'expo-file-system'; // lets me read files

export default function App() {

  // video is our state, setVideo changes our state
  const [video, setVideo] = useState(null);

  // have the user select a video for analysis
  const pickVideo = async () => {

    // get permission from user to access media library
    const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
    console.log("Media permission status:", status);
    if (status !== 'granted') {
      alert("Permission to access media library is required.");
      return;
    }

    // only pop up videos for this media submission
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Videos,
      allowsEditing: false,
    });

    // if the user does not cancel, the new video state should hold the local URI to the video
    if(!result.canceled) {
      setVideo(result.assets[0].uri);
    }
  };

  // upload the video to the backend
  const uploadVideo = async () => {
    if(!video) return;

    // this line opens the video file and reads it as a base64 string
    // allows us to send the video as text over a network
    const videoData = await FileSystem.readAsStringAsync(video, {
      encoding: FileSystem.EncodingType.Base64,
    });

    console.log("Video data ready to upload");
    console.log("Base64 length: ", videoData.length);
  }

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Upload Workout Video</Text>
      <Button title="Pick a Video" onPress={pickVideo} />
      {video && (
        <View style={styles.previewContainer}>
          <Text>Video Selected!</Text>
        </View>
      )}
      <Button title="Submit for Analysis" onPress={uploadVideo} disabled={!video} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
    alignItems: 'center',
    justifyContent: 'center',
  },
  title: {
    fontSize: 22,
    marginBottom: 20,
    textAlign: 'center',
  },
  previewContainer: {
    marginVertical: 20,
    alignItems: 'center',
  },
});
