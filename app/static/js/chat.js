document.addEventListener('DOMContentLoaded', function() {
    const sendMessageBtn = document.getElementById('sendMessageBtn');
    const messageInput = document.getElementById('messageInput');
    const chatMessages = document.getElementById('chatMessages');
    const modelSelector = document.getElementById('modelSelector');
    const modelSettingsBtn = document.getElementById('modelSettingsBtn');
    const chatContainer = document.getElementById('chatContainer');
    
    // Определяем ID текущего чата
    const currentChatId = chatContainer ? chatContainer.dataset.chatId : null;
    
    // Если страница содержит чат
    if (currentChatId && sendMessageBtn && messageInput) {
        // WebSocket для чата
        initWebSocket(currentChatId);
        
        // Обработчик отправки сообщения
        sendMessageBtn.addEventListener('click', function() {
            sendMessage();
        });
        
        // Прокрутка до последнего сообщения при загрузке страницы
        scrollToBottom();
    }
    
    // Настройка модального окна настроек модели
    if (modelSettingsBtn) {
        modelSettingsBtn.addEventListener('click', function() {
            openModelSettings(modelSelector.value);
        });
        
        setupModelSettingsModal();
    }
});

// WebSocket подключение
let socket = null;
let activeMessageId = null;

/**
 * Инициализация WebSocket соединения
 */
function initWebSocket(chatId) {
    // Проверяем, поддерживаются ли WebSockets
    if (!("WebSocket" in window)) {
        alert("Ваш браузер не поддерживает WebSocket!");
        return;
    }
    
    // Закрываем предыдущее соединение, если оно было открыто
    if (socket) {
        socket.close();
    }
    
    // Создаем новое соединение
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/chat/ws/${chatId}`;
    
    socket = new WebSocket(wsUrl);
    
    // Обработчики WebSocket
    socket.onopen = function() {
        console.log("WebSocket соединение установлено");
    };
    
    socket.onmessage = function(event) {
        const data = JSON.parse(event.data);
        handleWebSocketMessage(data);
    };
    
    socket.onclose = function() {
        console.log("WebSocket соединение закрыто");
        // Пытаемся переподключиться через 3 секунды
        setTimeout(function() {
            initWebSocket(chatId);
        }, 3000);
    };
    
    socket.onerror = function(error) {
        console.error("WebSocket ошибка:", error);
    };
}

/**
 * Обработка сообщений от WebSocket
 */
function handleWebSocketMessage(data) {
    if (data.error) {
        showError(data.error);
        return;
    }
    
    const chatMessages = document.getElementById('chatMessages');
    
    switch (data.type) {
        case 'user_message':
            // Добавляем сообщение пользователя в чат
            const userMessageHTML = createMessageHTML(data.content, 'user');
            chatMessages.insertAdjacentHTML('beforeend', userMessageHTML);
            scrollToBottom();
            break;
            
        case 'assistant_start':
            // Создаем пустое сообщение модели
            activeMessageId = data.id;
            const assistantMessageHTML = createMessageHTML('', 'assistant', activeMessageId);
            chatMessages.insertAdjacentHTML('beforeend', assistantMessageHTML);
            scrollToBottom();
            break;
            
        case 'assistant_chunk':
            // Добавляем фрагмент текста в текущее сообщение модели
            if (activeMessageId) {
                const messageContent = document.querySelector(`.message[data-message-id="${activeMessageId}"] .message-content`);
                if (messageContent) {
                    messageContent.innerHTML += formatMessage(data.chunk);
                    scrollToBottom();
                }
            }
            break;
            
        case 'assistant_end':
            // Завершаем сообщение модели
            activeMessageId = null;
            scrollToBottom();
            // Очищаем поле ввода
            document.getElementById('messageInput').value = '';
            break;
    }
}

/**
 * Отправка сообщения
 */
function sendMessage() {
    const messageInput = document.getElementById('messageInput');
    const modelSelector = document.getElementById('modelSelector');
    const message = messageInput.value.trim();
    
    if (!message) return;
    
    if (socket && socket.readyState === WebSocket.OPEN) {
        // Отправляем через WebSocket
        socket.send(JSON.stringify({
            message: message,
            model: modelSelector.value
        }));
    } else {
        // Отправляем через обычный HTTP запрос, если WebSocket не доступен
        sendMessageHttp(message, modelSelector.value);
    }
}

/**
 * Отправка сообщения через HTTP если WebSocket не доступен
 */
async function sendMessageHttp(message, model) {
    const chatContainer = document.getElementById('chatContainer');
    const chatId = chatContainer.dataset.chatId;
    const chatMessages = document.getElementById('chatMessages');
    
    try {
        // Добавляем сообщение пользователя в UI
        const userMessageHTML = createMessageHTML(message, 'user');
        chatMessages.insertAdjacentHTML('beforeend', userMessageHTML);
        scrollToBottom();
        
        // Очищаем поле ввода
        document.getElementById('messageInput').value = '';
        
        // Добавляем индикатор загрузки
        const loadingHTML = createMessageHTML('<div class="loading-dots"><span>.</span><span>.</span><span>.</span></div>', 'assistant');
        chatMessages.insertAdjacentHTML('beforeend', loadingHTML);
        scrollToBottom();
        
        // Отправляем HTTP запрос
        const formData = new FormData();
        formData.append('message', message);
        formData.append('model_name', model);
        
        const response = await fetch(`/chat/${chatId}/messages`, {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            const data = await response.json();
            
            // Удаляем индикатор загрузки
            const loadingMessage = chatMessages.querySelector('.message:last-child');
            if (loadingMessage) {
                loadingMessage.remove();
            }
            
            // Добавляем ответ модели
            const aiMessageHTML = createMessageHTML(data.ai_message.content, 'assistant');
            chatMessages.insertAdjacentHTML('beforeend', aiMessageHTML);
            scrollToBottom();
        } else {
            showError('Ошибка при отправке сообщения');
        }
    } catch (error) {
        console.error('Ошибка:', error);
        showError('Ошибка при отправке сообщения');
    }
}

/**
 * Создание HTML разметки для сообщения
 */
function createMessageHTML(content, role, messageId = null) {
    const formattedContent = formatMessage(content);
    const avatarLabel = role === 'user' ? 'Вы' : 'AI';
    
    return `
        <div class="message ${role}-message" ${messageId ? `data-message-id="${messageId}"` : ''}>
            <div class="message-avatar">
                <div class="avatar ${role}-avatar">${avatarLabel}</div>
            </div>
            <div class="message-content">${formattedContent}</div>
        </div>
    `;
}

/**
 * Форматирование текста сообщения (обработка кода, ссылок и др.)
 */
function formatMessage(text) {
    if (!text) return '';
    
    // Безопасный HTML
    let formattedText = text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
    
    // Обработка новых строк
    formattedText = formattedText.replace(/\n/g, '<br>');
    
    // Обработка блоков кода (```code```)
    formattedText = formattedText.replace(/```([^`]+)```/g, function(match, codeContent) {
        return `<pre class="code-block"><code>${codeContent}</code></pre>`;
    });
    
    // Обработка inline кода (`code`)
    formattedText = formattedText.replace(/`([^`]+)`/g, function(match, codeContent) {
        return `<code class="inline-code">${codeContent}</code>`;
    });
    
    return formattedText;
}

/**
 * Прокрутка чата вниз
 */
function scrollToBottom() {
    const chatMessages = document.getElementById('chatMessages');
    if (chatMessages) {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
}

/**
 * Показать сообщение об ошибке
 */
function showError(message) {
    console.error(message);
    alert(message);
}

/**
 * Настройка модального окна настроек модели
 */
function setupModelSettingsModal() {
    const modal = document.getElementById('modelSettingsModal');
    const closeBtn = modal.querySelector('.close-modal');
    const form = document.getElementById('modelSettingsForm');
    const temperatureSlider = document.getElementById('temperature');
    const temperatureValue = document.getElementById('temperatureValue');
    const promptTemplates = document.getElementById('promptTemplates');
    
    // Загрузить шаблоны промптов
    loadPromptTemplates();
    
    // Обработчик изменения значения температуры
    temperatureSlider.addEventListener('input', function() {
        temperatureValue.textContent = this.value;
    });
    
    // Закрытие модального окна
    closeBtn.addEventListener('click', function() {
        modal.style.display = 'none';
    });
    
    // Закрытие по клику вне модального окна
    window.addEventListener('click', function(e) {
        if (e.target === modal) {
            modal.style.display = 'none';
        }
    });
    
    // Обработка отправки формы
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        saveModelSettings();
    });
    
    // Выбор шаблона промпта
    promptTemplates.addEventListener('change', function() {
        if (this.value) {
            // Загрузить выбранный шаблон
            loadPromptTemplate(this.value);
        }
    });
}

/**
 * Открытие модального окна настроек модели
 */
async function openModelSettings(modelName) {
    const modal = document.getElementById('modelSettingsModal');
    const currentModelName = document.getElementById('currentModelName');
    
    currentModelName.textContent = modelName;
    
    // Загрузить текущие настройки модели
    try {
        const response = await fetch(`/models/${modelName}/settings`);
        if (response.ok) {
            const settings = await response.json();
            
            // Заполнить форму
            document.getElementById('temperature').value = settings.temperature;
            document.getElementById('temperatureValue').textContent = settings.temperature;
            document.getElementById('maxTokens').value = settings.max_tokens;
            document.getElementById('systemPrompt').value = settings.system_prompt || '';
        }
    } catch (error) {
        console.error('Ошибка загрузки настроек:', error);
    }
    
    // Показать модальное окно
    modal.style.display = 'block';
}

/**
 * Сохранение настроек модели
 */
async function saveModelSettings() {
    const modal = document.getElementById('modelSettingsModal');
    const modelName = document.getElementById('currentModelName').textContent;
    const temperature = document.getElementById('temperature').value;
    const maxTokens = document.getElementById('maxTokens').value;
    const systemPrompt = document.getElementById('systemPrompt').value;
    
    try {
        const formData = new FormData();
        formData.append('temperature', temperature);
        formData.append('max_tokens', maxTokens);
        formData.append('system_prompt', systemPrompt);
        
        const response = await fetch(`/models/${modelName}/settings`, {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            // Закрыть модальное окно
            modal.style.display = 'none';
        } else {
            showError('Ошибка сохранения настроек');
        }
    } catch (error) {
        console.error('Ошибка:', error);
        showError('Ошибка сохранения настроек');
    }
}

/**
 * Загрузка шаблонов промптов
 */
async function loadPromptTemplates() {
    try {
        const response = await fetch('/models/prompts/list');
        if (response.ok) {
            const templates = await response.json();
            const promptsSelect = document.getElementById('promptTemplates');
            
            // Очистить существующие опции
            promptsSelect.innerHTML = '<option value="">Выберите шаблон...</option>';
            
            // Добавить новые опции
            templates.forEach(template => {
                const option = document.createElement('option');
                option.value = template.id;
                option.textContent = template.name;
                promptsSelect.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Ошибка загрузки шаблонов:', error);
    }
}

/**
 * Загрузка конкретного шаблона промпта
 */
async function loadPromptTemplate(templateId) {
    try {
        const response = await fetch(`/models/prompts/list`);
        if (response.ok) {
            const templates = await response.json();
            const template = templates.find(t => t.id == templateId);
            
            if (template) {
                document.getElementById('systemPrompt').value = template.system_prompt;
            }
        }
    } catch (error) {
        console.error('Ошибка загрузки шаблона:', error);
    }
} 