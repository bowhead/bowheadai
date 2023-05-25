
//i have the following estructures in my App.js: 
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
  const [files, setFiles] = useState([]);

  const handleFilesUploaded = (files) => {
    console.log(files)
    setFilesUploaded(true);
    setFiles(files);
  };

  const handleFileRemoval = (idx) => {
    setFiles(oldFiles => {
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
        <Box width="20%" height="100%" bgColor="white" id='filesContainer'>
          <Sidebar fileList={files} removeFile={handleFileRemoval}/>
          {filesUploaded && <FileUploader width="80%" onFilesUploaded={handleFilesUploaded} margin="0 auto"/>}
        </Box>
        <Box flex="1" height="100%" direction="column">
          
            {!filesUploaded && <Center height="85%"><FileUploader width="80%" onFilesUploaded={handleFilesUploaded} /></Center>}
            
            {filesUploaded &&
              <Chat width="80%" bgColor="white" uploadedFiles={files} />
           }
          
        </Box>
      </Flex>
    </ChakraProvider>
  );
}

export default App;
