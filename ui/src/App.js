import React, { useState } from 'react';
import {Flex, Box, ChakraProvider, extendTheme, Center } from '@chakra-ui/react';
import FileUploader from './components/FileUploader';
import Chat from './components/Chat';
import Sidebar from './components/Sidebar';
import './App.css';

const daoTheme = extendTheme({
  colors: {
    daoTeal: "#25CCDE",
    daoPurple: "#6D64FF",
  },
});

function App() {
  const [filesUploaded, setFilesUploaded] = useState(false);
  const [filesList, setFilesList] = useState([]);

  const handleFilesUploaded = (files) => {
    setFilesUploaded(true);
    setFilesList((prevFiles) => [...prevFiles, ...files]);
  };

  const handleFileRemoval = (idx) => {
    setFilesList(oldFiles => {
      let copy = [...oldFiles];
      console.log(idx, copy)
      copy.splice(idx, 1);
      console.log(copy)
      return copy;
    });
  }

  return (
    <ChakraProvider theme={daoTheme}>
      <Flex color="white" alignItems="stretch" height="100%">
        {filesUploaded && <Box width="20%" height="100%" bgColor="white" id='filesContainer'>
          <Sidebar fileList={filesList} removeFile={handleFileRemoval}/>
          <FileUploader width="80%" onFilesUploaded={handleFilesUploaded} deleteOldFiles={false} margin="0 auto"/>
        </Box>}
        <Box flex="1" height="100%" direction="column">
          
            {!filesUploaded && 
            <Box height="100%" display="flex" flexDirection="column" alignItems="center" justifyContent="center">
              <p style={{color: 'black', marginBottom:"12px"}}>Upload any PDF, CSV, image or JSON and start chatting with your health data.</p>
              <FileUploader width="80%" onFilesUploaded={handleFilesUploaded} deleteOldFiles={true}/>
            </Box>
            }
            
            {filesUploaded &&
              <Chat width="80%" bgColor="white" />
           }
          
        </Box>
      </Flex>
    </ChakraProvider>
  );
}


export default App;
