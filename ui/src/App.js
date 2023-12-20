import React, { useState, useEffect } from 'react';
import { Flex, Box, ChakraProvider, extendTheme, Spinner } from '@chakra-ui/react';
import FileUploader from './components/FileUploader';
import Chat from './components/Chat';
import Sidebar from './components/Sidebar';
import './App.css';
import { v4 as uuidv4 } from 'uuid';

const daoTheme = extendTheme({
  colors: {
    daoTeal: "#25CCDE",
    daoPurple: "#6D64FF",
  },
});

function App() {
  const [filesUploaded, setFilesUploaded] = useState(false);
  const [filesList, setFilesList] = useState([]);
  const [userId, setUserId] = useState(uuidv4());
  const [logged, setLogged] = useState(false);

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

  useEffect(() => {
    // create async function
    const fetchData = async () => {
      return await fetch(process.env.REACT_APP_SOCKET_URL + '/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        mode: "cors",
        credentials: 'include',
        body: JSON.stringify({ uuid: userId })
      }) 
    }

    fetchData().then(() => setLogged(true))
  }, []);


  return (
    <ChakraProvider theme={daoTheme}>
      {
      logged? (
      <Flex color="white" alignItems="stretch" height="100%">
        
        <Box flex="1" height="100%" direction="column">
          
            {filesUploaded && 
            <Box height="100%" display="flex" flexDirection="column" alignItems="center" justifyContent="center">
              <p style={{color: 'black', marginBottom:"12px"}}>Upload any PDF, CSV, image or JSON and start chatting with your health data.</p>
              <FileUploader width="80%" onFilesUploaded={handleFilesUploaded} deleteOldFiles={true} userId={userId}/>
            </Box>
            }
            
            {!filesUploaded &&
              <Chat userId={userId} width="80%" bgColor="white" />
           }
          
        </Box>
      </Flex>
      )
      :
      (
        // display a chakra spinner
        <Flex height="100%" alignItems="center" justifyContent="center">
          <Spinner size='xl' />
        </Flex>
      )
      }
    </ChakraProvider>
  );
}


export default App;
