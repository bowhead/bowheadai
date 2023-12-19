import { Box, Input, IconButton,Text} from "@chakra-ui/react";
import { useState } from "react";
import { FaPaperPlane } from "react-icons/fa";

const sendMessageUrl = 'http://127.0.0.1:3000/send-message'

// Define your arguments or replace with a more robust solution like yargs or command-line-args
const args = {
  controllerAddress: 'http://0.0.0.0:21001',
  workerAddress: 'http://127.0.0.1:21002',
  modelName: 'meditron-7b', // Replace with actual model name
  temperature: 0.3,
  maxNewTokens: 512,
};

function Chat({userId,...props}) {
  const [messages, setMessages] = useState([]);
  const [history, setHistory] = useState([]);
  const [inputValue, setInputValue] = useState("");
  const [loadingResp, setLoadingResp] = useState(false);

  async function handleSendMessage() {
    if (inputValue.trim() !== "" ) {
      setMessages([...messages, { "class":"user-msg", "msg": inputValue}]);
      setHistory([...history, { "input": inputValue}]);
      setInputValue("");
      setLoadingResp(true);
      try {
        const response = await fetch(sendMessageUrl, {
          method: "POST",
          mode: "cors",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify({ message: inputValue, history: history, userId:userId})
        });

        setLoadingResp(false);

        if (response.ok) {
          const responseJSON = await response.json();
          setMessages(messages => [...messages, { "class": "system-msg", "msg": responseJSON.response}]);
          setHistory(history => [...history, { "output": responseJSON.response }]);
        } else {
          throw new Error("Error en la solicitud");
        }
      } catch (error) {
        console.error(error);
        // Manejar el error en la solicitud
      }
    }
  }

  function handleInputValueChange(event) {
    setInputValue(event.target.value);
    
  }

  function handleKeyPress(event) {
    if (event.key === "Enter") {
      handleSendMessage();
    }
  }
  

  return (
    <Box p={4}>
      <Box height="80vh" width="83%" sx={{ overflow: "auto" }} flex="1">
        {messages.map((message, index) => (
          <Box
            key={index}
            p={2}
            color="black"
            borderRadius="md"
            mb={2}
            className={message.class}
          >
            <Text whiteSpace="pre-wrap">{message.msg}</Text>
            
          </Box>
        ))}
        {loadingResp && <Box alignItems="center">
          <img src={process.env.PUBLIC_URL + 'loader.gif'} alt="loader"/>
        </Box>}
        
      </Box>

      <Box>
        <Input 
          value={inputValue}
          color="black"
          onChange={handleInputValueChange}
          onKeyPress={handleKeyPress}
          placeholder="Message..."
          isDisabled={loadingResp}
          {...props}
        />
        <IconButton aria-label='Send' icon={<FaPaperPlane />} bgColor="daoPurple" onClick={handleSendMessage} isDisabled={loadingResp}/>
      </Box>
    </Box>
  );
}

export default Chat;