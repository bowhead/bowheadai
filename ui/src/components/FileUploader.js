import { Box, Heading, Text, Image, Progress } from "@chakra-ui/react";
import { useState, useRef, useEffect } from "react";
import io from "socket.io-client";

const apiKey = process.env.REACT_APP_SOCKET_URL;
const uploadUrl = process.env.REACT_APP_UPLOAD_ENDPOINT;



function FileUploader({ onFilesUploaded,deleteOldFiles,userId, ...props }) {
  const fileInputRef = useRef(null);
  const [files, setFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [requestStatus, setRequestStatus] = useState('Drag and drop files here');
  const [requestError, setRequestError] = useState(false);
  
  

  useEffect(() => {
    if (files.length > 0) {
      createVector();
      setUploading(true);
      setRequestStatus("Uploading files...")
      setProgress(10)
      setRequestError(false)

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
    const socket = io(apiKey, {
      extraHeaders: {
        "uuid": userId
      }
    });
    if (!uploading) return;
  
    // check the upload progress using the /progress endpoint and a fetch call
    const checkProgress = async () => {
      try {
        const response = await fetch(apiKey + '/progress', {
          method: "GET",
          mode: "cors",
          credentials: 'include',
        });

        if (response.ok) {
          const data = await response.json();
          setProgress(data.progress);

          return data.progress;
        } else {
          console.error("Failed to get progress.");
        }
      } catch (error) {
        console.error("Error occurred while getting progress:", error);
      }
    }

    function progressIterator() {
      checkProgress().then((progress) => {
        if (progress === 100) return;

        progressIterator();
      });
    }

  }, [uploading]);

  async function createVector() {
    if (files.length === 0) {
      return;
    }


    const formData = new FormData();
    formData.append('deleteOldFiles', deleteOldFiles ? 'true' : 'false');
    formData.append('userId', userId);
    files.forEach((file, index) => {
      formData.append('files', file);
    });

    
    try {
      const response = await fetch(uploadUrl, {
        method: "POST",
        body:formData,
        mode: "cors",
        credentials: 'include',
      });

      if (response.ok) {
        console.log("File uploaded successfully!");
       
        onFilesUploaded(files);
        setUploading(false);
        
      } else {
        console.log("Failed to upload file.");
        setRequestStatus('Failed to process files!')
        setRequestError(true)
        setUploading(false)
      }
    } catch (error) {
      console.log("Error occurred while uploading the file:", error);
      setRequestStatus('Error occurred while uploading the files!')
      setRequestError(true)
      setUploading(false)
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
          <Heading as="h3" mb={2} color={requestError ? "red" : "daoPurple"}>
            {requestStatus}
          </Heading>
        
          <Progress value={progress} size="md" w="100%" mb={8} mt={8}/>
          {/*<Progress size="md" w="100%" mb={8} mt={8} isIndeterminate/>*/}
        </>
      ) : (
        <Heading as="h3" mb={2} color={requestError ? "red" : "daoPurple"}>
            {requestStatus}
        </Heading>
      )}
      {!uploading && requestError &&(
        <Text fontSize="sm" color="gray.500" mb={4}>
          {requestError ? "Try to Upload again" : "or click to select files"}
        </Text>
        
      )}
        

        <input type="file" style={{ display: "none" }} ref={fileInputRef} onChange={handleFileInputChange} multiple />
      </Box>
      
  );
}

export default FileUploader;