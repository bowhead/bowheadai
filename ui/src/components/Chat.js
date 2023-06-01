import { Box, Input, IconButton} from "@chakra-ui/react";
import { useState } from "react";
import { FaPaperPlane } from "react-icons/fa";

function Chat({...props}) {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState("");

  async function handleSendMessage() {
    if (inputValue.trim() !== "" ) {
        setMessages([...messages, "User: " + inputValue]);
        setInputValue("");
      try {
        const response = await fetch("https://gptpi.bowheadhealth.io/send-message", {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify({ message: inputValue, history: messages})
        });

        if (response.ok) {
          const responseData = await response.json();
          setMessages(messages => [...messages, "System: " + responseData.response]);
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
    <Box p={4} align="center" >
      <Box height="80vh" width="83%" sx={{ overflow: "auto" }}>
        {messages.map((message, index) => (
          <Box
            align="left"
            key={index}
            bg="white"
            p={2}
            color="black"
            borderRadius="md"
            mb={2}
            alignSelf={index % 2 === 0 ? "flex-start" : "flex-end"}
          >
            {message}
          </Box>
        ))}
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