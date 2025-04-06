# Интеграция внешнего фронтенд-приложения с API

В этом документе представлены примеры того, как можно интегрировать внешнее фронтенд-приложение (например, на Vue.js) с API-слоем проекта LLM-UI.

## Настройка CORS для API

Для работы с внешним фронтенд-приложением необходимо правильно настроить CORS-политики. В файле `app/main.py` уже есть настройка CORS, но её можно улучшить:

```python
# app/main.py

# ... существующий код ...

# Добавление поддержки CORS
app.add_middleware(
    CORSMiddleware,
    # Список разрешенных источников запросов
    allow_origins=["http://localhost:3000", "http://localhost:8080", "https://your-production-frontend.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ... существующий код ...
```

## Пример интеграции с Vue.js

### Настройка клиента API на Vue.js

```javascript
// src/api/client.js

import axios from 'axios';

// Создаем экземпляр axios с настройками
const apiClient = axios.create({
  baseURL: 'http://localhost:8000/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  }
});

export default apiClient;
```

### Сервис для работы с чатами

```javascript
// src/api/chatService.js

import apiClient from './client';

export default {
  // Получить список всех чатов
  getAllChats() {
    return apiClient.get('/chat/chats');
  },

  // Получить чат по ID
  getChat(chatId) {
    return apiClient.get(`/chat/chats/${chatId}`);
  },

  // Создать новый чат
  createChat(title, modelId) {
    return apiClient.post('/chat/chats', {
      title: title,
      model_id: modelId
    });
  },

  // Получить сообщения чата
  getChatMessages(chatId) {
    return apiClient.get(`/chat/chats/${chatId}/messages`);
  },

  // Отправить сообщение и получить ответ
  sendMessage(chatId, content) {
    return apiClient.post(`/chat/chats/${chatId}/messages`, {
      content: content
    });
  },

  // Удалить чат
  deleteChat(chatId) {
    return apiClient.delete(`/chat/chats/${chatId}`);
  }
};
```

### Пример компонента чата на Vue.js

```vue
<!-- src/components/Chat.vue -->

<template>
  <div class="chat-container">
    <div v-if="loading" class="loading">Загрузка...</div>
    
    <div v-else>
      <h1>{{ chat.title }}</h1>
      
      <div class="messages">
        <div v-for="message in messages" :key="message.id" 
             :class="['message', message.role]">
          <div class="message-content">{{ message.content }}</div>
          <div class="message-timestamp">{{ formatDate(message.created_at) }}</div>
        </div>
      </div>
      
      <div class="message-form">
        <textarea v-model="newMessage" 
                  placeholder="Введите сообщение..." 
                  @keypress.enter.ctrl="sendMessage"></textarea>
        <button @click="sendMessage" :disabled="isSending">Отправить</button>
      </div>
    </div>
  </div>
</template>

<script>
import chatService from '@/api/chatService';

export default {
  name: 'Chat',
  
  props: {
    chatId: {
      type: [Number, String],
      required: true
    }
  },
  
  data() {
    return {
      chat: null,
      messages: [],
      newMessage: '',
      loading: true,
      isSending: false
    };
  },
  
  async created() {
    await this.loadChat();
    await this.loadMessages();
    this.loading = false;
  },
  
  methods: {
    async loadChat() {
      try {
        const response = await chatService.getChat(this.chatId);
        this.chat = response.data;
      } catch (error) {
        console.error('Ошибка при загрузке чата:', error);
      }
    },
    
    async loadMessages() {
      try {
        const response = await chatService.getChatMessages(this.chatId);
        this.messages = response.data;
      } catch (error) {
        console.error('Ошибка при загрузке сообщений:', error);
      }
    },
    
    async sendMessage() {
      if (!this.newMessage.trim() || this.isSending) return;
      
      this.isSending = true;
      
      try {
        // Добавляем сообщение пользователя в UI сразу
        const userMessage = {
          id: 'temp-' + Date.now(),
          role: 'user',
          content: this.newMessage,
          created_at: new Date().toISOString()
        };
        
        this.messages.push(userMessage);
        const messageContent = this.newMessage;
        this.newMessage = '';
        
        // Отправляем сообщение на сервер
        const response = await chatService.sendMessage(this.chatId, messageContent);
        
        // Добавляем ответ ассистента
        this.messages.push(response.data);
      } catch (error) {
        console.error('Ошибка при отправке сообщения:', error);
      } finally {
        this.isSending = false;
      }
    },
    
    formatDate(dateString) {
      const date = new Date(dateString);
      return date.toLocaleTimeString() + ' ' + date.toLocaleDateString();
    }
  }
};
</script>

<style scoped>
.chat-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.loading {
  text-align: center;
  padding: 20px;
}

.messages {
  margin: 20px 0;
  max-height: 500px;
  overflow-y: auto;
  border: 1px solid #eee;
  padding: 10px;
}

.message {
  margin-bottom: 15px;
  padding: 10px;
  border-radius: 5px;
}

.message.user {
  background-color: #e3f2fd;
  margin-left: 20%;
}

.message.assistant {
  background-color: #f1f1f1;
  margin-right: 20%;
}

.message-content {
  white-space: pre-wrap;
}

.message-timestamp {
  font-size: 0.8em;
  color: #888;
  text-align: right;
  margin-top: 5px;
}

.message-form {
  display: flex;
  margin-top: 20px;
}

textarea {
  flex: 1;
  min-height: 80px;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 5px;
  margin-right: 10px;
  resize: vertical;
}

button {
  padding: 10px 20px;
  background-color: #4caf50;
  color: white;
  border: none;
  border-radius: 5px;
  cursor: pointer;
}

button:disabled {
  background-color: #cccccc;
}
</style>
```

### Пример маршрутизации во Vue.js

```javascript
// src/router/index.js

import { createRouter, createWebHistory } from 'vue-router';
import Home from '@/views/Home.vue';
import ChatList from '@/views/ChatList.vue';
import ChatView from '@/views/ChatView.vue';
import ModelList from '@/views/ModelList.vue';

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home
  },
  {
    path: '/chats',
    name: 'Chats',
    component: ChatList
  },
  {
    path: '/chats/:id',
    name: 'Chat',
    component: ChatView,
    props: true
  },
  {
    path: '/models',
    name: 'Models',
    component: ModelList
  }
];

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes
});

export default router;
```

## Пример использования WebSocket для чата

Для реализации интерактивного чата с потоковой передачей ответов можно использовать WebSocket:

```javascript
// src/api/websocketService.js

export default {
  // Установить WebSocket соединение для чата
  connect(chatId, onMessage, onError) {
    const ws = new WebSocket(`ws://localhost:8000/chat/ws/${chatId}`);
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      onMessage(data);
    };
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      if (onError) onError(error);
    };
    
    return {
      // Отправить сообщение через WebSocket
      sendMessage(content) {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ content }));
        } else {
          console.error('WebSocket not connected');
        }
      },
      
      // Закрыть соединение
      close() {
        ws.close();
      }
    };
  }
};
```

Пример использования WebSocket в компоненте Vue:

```vue
<!-- src/components/StreamingChat.vue -->

<template>
  <div class="chat-container">
    <!-- Аналогично обычному компоненту чата... -->
    
    <div class="message-form">
      <textarea v-model="newMessage" 
                placeholder="Введите сообщение..." 
                @keypress.enter.ctrl="sendMessage"></textarea>
      <button @click="sendMessage" :disabled="isSending">Отправить</button>
    </div>
  </div>
</template>

<script>
import websocketService from '@/api/websocketService';
import chatService from '@/api/chatService';

export default {
  name: 'StreamingChat',
  
  props: {
    chatId: {
      type: [Number, String],
      required: true
    }
  },
  
  data() {
    return {
      chat: null,
      messages: [],
      newMessage: '',
      loading: true,
      isSending: false,
      ws: null,
      currentStreamingMessage: null
    };
  },
  
  async created() {
    await this.loadChat();
    await this.loadMessages();
    this.setupWebSocket();
    this.loading = false;
  },
  
  beforeUnmount() {
    // Закрыть WebSocket при уничтожении компонента
    if (this.ws) {
      this.ws.close();
    }
  },
  
  methods: {
    // Загрузка чата и сообщений аналогична предыдущему примеру...
    
    setupWebSocket() {
      this.ws = websocketService.connect(
        this.chatId,
        this.handleWebSocketMessage,
        this.handleWebSocketError
      );
    },
    
    handleWebSocketMessage(data) {
      if (data.type === 'stream_start') {
        // Начало потока - создаем новое сообщение
        this.currentStreamingMessage = {
          id: 'stream-' + Date.now(),
          role: 'assistant',
          content: '',
          created_at: new Date().toISOString()
        };
        this.messages.push(this.currentStreamingMessage);
      } 
      else if (data.type === 'stream_token') {
        // Получен токен - добавляем к текущему сообщению
        if (this.currentStreamingMessage) {
          this.currentStreamingMessage.content += data.token;
        }
      } 
      else if (data.type === 'stream_end') {
        // Конец потока - обновляем ID сообщения
        if (this.currentStreamingMessage && data.message_id) {
          this.currentStreamingMessage.id = data.message_id;
        }
        this.currentStreamingMessage = null;
        this.isSending = false;
      }
    },
    
    handleWebSocketError(error) {
      console.error('WebSocket error:', error);
      this.isSending = false;
    },
    
    sendMessage() {
      if (!this.newMessage.trim() || this.isSending) return;
      
      this.isSending = true;
      
      // Добавляем сообщение пользователя в UI
      const userMessage = {
        id: 'temp-' + Date.now(),
        role: 'user',
        content: this.newMessage,
        created_at: new Date().toISOString()
      };
      
      this.messages.push(userMessage);
      
      // Отправляем через WebSocket
      this.ws.sendMessage(this.newMessage);
      this.newMessage = '';
    }
  }
};
</script>

<style scoped>
/* Стили аналогичны предыдущему примеру... */
</style>
```

## Кэширование данных с использованием Vuex

Для управления состоянием приложения и кэширования данных рекомендуется использовать Vuex:

```javascript
// src/store/index.js

import { createStore } from 'vuex';
import chatService from '@/api/chatService';
import modelService from '@/api/modelService';

export default createStore({
  state: {
    chats: [],
    models: [],
    currentChat: null,
    currentMessages: []
  },
  
  getters: {
    getChats: state => state.chats,
    getModels: state => state.models,
    getCurrentChat: state => state.currentChat,
    getCurrentMessages: state => state.currentMessages
  },
  
  mutations: {
    SET_CHATS(state, chats) {
      state.chats = chats;
    },
    SET_MODELS(state, models) {
      state.models = models;
    },
    SET_CURRENT_CHAT(state, chat) {
      state.currentChat = chat;
    },
    SET_CURRENT_MESSAGES(state, messages) {
      state.currentMessages = messages;
    },
    ADD_MESSAGE(state, message) {
      state.currentMessages.push(message);
    },
    ADD_CHAT(state, chat) {
      state.chats.push(chat);
    }
  },
  
  actions: {
    async fetchChats({ commit }) {
      try {
        const response = await chatService.getAllChats();
        commit('SET_CHATS', response.data);
        return response.data;
      } catch (error) {
        console.error('Ошибка при получении списка чатов:', error);
        throw error;
      }
    },
    
    async fetchModels({ commit }) {
      try {
        const response = await modelService.getAllModels();
        commit('SET_MODELS', response.data);
        return response.data;
      } catch (error) {
        console.error('Ошибка при получении списка моделей:', error);
        throw error;
      }
    },
    
    async fetchChat({ commit }, chatId) {
      try {
        const response = await chatService.getChat(chatId);
        commit('SET_CURRENT_CHAT', response.data);
        return response.data;
      } catch (error) {
        console.error('Ошибка при получении чата:', error);
        throw error;
      }
    },
    
    async fetchMessages({ commit }, chatId) {
      try {
        const response = await chatService.getChatMessages(chatId);
        commit('SET_CURRENT_MESSAGES', response.data);
        return response.data;
      } catch (error) {
        console.error('Ошибка при получении сообщений:', error);
        throw error;
      }
    },
    
    async sendMessage({ commit }, { chatId, content }) {
      try {
        const response = await chatService.sendMessage(chatId, content);
        commit('ADD_MESSAGE', response.data);
        return response.data;
      } catch (error) {
        console.error('Ошибка при отправке сообщения:', error);
        throw error;
      }
    },
    
    async createChat({ commit }, { title, modelId }) {
      try {
        const response = await chatService.createChat(title, modelId);
        commit('ADD_CHAT', response.data);
        return response.data;
      } catch (error) {
        console.error('Ошибка при создании чата:', error);
        throw error;
      }
    }
  }
});