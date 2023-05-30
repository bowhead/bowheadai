import { Box, Heading, Text, Image, Progress } from "@chakra-ui/react";
import { useState, useRef, useEffect } from "react";
import io from "socket.io-client";

const socket = io("https://apichat.bowheadhealth.io/");

function FileUploader({ onFilesUploaded,deleteOldFiles,  ...props }) {
  const fileInputRef = useRef(null);
  const [files, setFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [requestStatus, setRequestStatus] = useState('Uploading files...');
  const [requestError, setRequestError] = useState(false);
  
  useEffect(() => {
    if (files.length > 0) {
      createVector();
      setUploading(true);
      setProgress(10)

    }
  }, [files]);

  function handleDragOver(event) {
    event.preventDefault();
  }

  function handleDragLeave(event) {
    event.preventDefault();
  }

  function handleDrop(event) {
    event.preventDefault();
    const fileList = Array.from(event.dataTransfer.files);
    setFiles(fileList);
  }

  function handleFileInputChange(event) {
    const fileList = Array.from(event.target.files);
    setFiles(fileList);
  }

  useEffect(() => {
    socket.on("progress", (data) => {
      // Update the progress state when receiving 'progress' event from the server
      setProgress(data.progress);
      if (data.progress===33)setRequestStatus('Processing files...')
      if (data.progress===66)setRequestStatus('Creating vector...')
      if (data.progress===100)setRequestStatus('Complete...')

      console.log(data.progress)
    });

    socket.on("message", (data) => {
      // Update the progress state when receiving 'progress' event from the server
      console.log(data.text)
    });

    return () => {
      console.log("off")
      socket.off("progress"); // Clean up the event listener when the component unmounts
    };
  }, []);

  async function createVector() {
    if (files.length === 0) {
      return;
    }


    const formData = new FormData();
    formData.append('deleteOldFiles', deleteOldFiles ? 'true' : 'false');

    files.forEach((file, index) => {
      formData.append('files', file);
    });

    
    try {
      const response = await fetch("https://apichat.bowheadhealth.io/upload", {
        method: "POST",
        body: formData,
      });

      if (response.ok) {
        console.log("File uploaded successfully!");
       
        onFilesUploaded(files);
        setUploading(false);
      } else {
        console.log("Failed to upload file.");
        if (progress===10)setRequestStatus('Failed Uploading Files!')
        if (progress===33)setRequestStatus('Failed Processing Files!')
        if (progress===66)setRequestStatus('Failed Creating Vector!')
        setRequestError(true)
      }
    } catch (error) {
      console.log("Error occurred while uploading the file:", error);
      setRequestStatus('Error occurred while uploading the file!')
      setRequestError(true)
    }
  }
  
  return (
      
      <Box 
        display="flex"
        flexDirection="column"
        justifyContent="center"
        alignItems="center"
        border="2px dashed"
        borderColor="daoPurple"
        borderRadius="md"
        bgColor="white"
        p="6"
        textAlign="center"
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={() => fileInputRef.current.click()}
        {...props}
      >
        
        <Image mb="4" src="/file.png" alt="File" />
        
        {uploading ? (
        <>
          <Heading as="h3" mb={2} color="daoPurple">
            {requestStatus}
          </Heading>
        
          <Progress value={progress} size="md" w="100%" mb={8} mt={8}/>
          {/*<Progress size="md" w="100%" mb={8} mt={8} isIndeterminate/>*/}
        </>
      ) : (
        <Heading as="h3" mb={2} color={requestError ? "red" : "daoPurple"}>
          Drag and drop files here
        </Heading>
      )}
      {!uploading && (
        <Text fontSize="sm" color="gray.500" mb={4}>
          or click to select files
        </Text>
        
      )}
        

        <input type="file" style={{ display: "none" }} ref={fileInputRef} onChange={handleFileInputChange} multiple />
      </Box>
      
  );
}

export default FileUploader;