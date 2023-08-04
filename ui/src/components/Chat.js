import { Box, Input, IconButton,Text} from "@chakra-ui/react";
import { useState } from "react";
import { FaPaperPlane } from "react-icons/fa";

const sendMessageUrl = process.env.REACT_APP_SEND_MESSAGE_ENDPOINT;

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
          credentials: 'include',
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify({ message: inputValue, history: history, userId:userId})
        });

        setLoadingResp(false);

        if (response.ok) {
          const responseData = await response.json();
          const responseJSON = JSON.parse(responseData.response)
          setMessages(messages => [...messages, { "class": "system-msg", "msg": responseJSON.answer + ( typeof responseJSON.sources !== 'undefined' && responseJSON.sources.length > 0 ? "\nSources:\n"+responseJSON.sources.join("\n"):"" )}]);
          setHistory(history => [...history, { "output": responseJSON.answer }]);
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
          {...props}
        />
        <IconButton aria-label='Send' icon={<FaPaperPlane />} bgColor="daoPurple" onClick={handleSendMessage}/>
      </Box>
    </Box>
  );
}

export default Chat;