import { Flex, Box, ChakraProvider, Center, extendTheme } from '@chakra-ui/react';
import FileUploader from './components/FileUploader';
import Search from './components/Search';
import FilesList from './components/FilesList';

import './App.css';
import { useState } from 'react';

const daoTheme = extendTheme({
  colors: {
    daoTeal: "#25CCDE",
    daoPurple: "#6D64FF",
  },
});


function App() {
  let [canChat, setCanChat] = useState(false);
  let [files, setFiles] = useState([]);

  const handleFilesUpload = files => {
    setFiles(oldFiles => [...oldFiles, ...files]);
    setCanChat(true);
  }

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
          <FilesList fileList={files} removeFile={handleFileRemoval}/>
          {canChat && <FileUploader width="80%" filesAddedCallback={handleFilesUpload} margin="0 auto"/>}
        </Box>
        <Box flex="1" height="100%" direction="column">
            <Center height="85%">
              {!canChat && <FileUploader width="80%" filesAddedCallback={handleFilesUpload}/>}
            </Center>
            {canChat && <Box textAlign="center">
              <Search width="80%" bgColor="white"/>
            </Box>}
        </Box>
      </Flex>
    </ChakraProvider>
  );
}

export default App;
