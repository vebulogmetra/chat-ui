/**
 * Инициализация чата
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM загружен, инициализация чата начата');
    
    // Сразу устанавливаем обработчик нажатия клавиш для поля ввода
    setupKeyboardHandlers();
    
    // Далее асинхронно загружаем данные
    initChatAsync();
});

/**
 * Асинхронная инициализация чата
 */
async function initChatAsync() {
    try {
        // Загружаем чаты и модели при загрузке страницы
        await loadChats();
        await loadModels();
        
        // Загружаем шаблоны промптов
        await loadPromptTemplates();
        
        // Добавляем обработчики событий
        setupEventListeners();
        
        // Если есть активный чат, загружаем его сообщения
        const activeChat = document.querySelector('.chat-item.active');
        if (activeChat) {
            const chatId = activeChat.dataset.chatId;
            await loadMessages(chatId);
            
            // Если определена константа CHAT_MODEL_NAME, используем ее для предустановки модели
            if (typeof CHAT_MODEL_NAME !== 'undefined' && CHAT_MODEL_NAME) {
                console.log('Используем предустановленную модель:', CHAT_MODEL_NAME);
                const modelSelector = document.getElementById('modelSelector');
                if (modelSelector) {
                    // Убедимся, что модель выбрана в селекторе
                    for (let i = 0; i < modelSelector.options.length; i++) {
                        if (modelSelector.options[i].value === CHAT_MODEL_NAME) {
                            modelSelector.selectedIndex = i;
                            break;
                        }
                    }
                }
            }
        }
        
        // Добавляем обработчик отправки формы сообщения
        const messageForm = document.getElementById('messageForm');
        if (messageForm) {
            messageForm.addEventListener('submit', handleMessageSubmit);
        }
    } catch (error) {
        console.error('Ошибка инициализации:', error);
    }
}

/**
 * Настройка обработчиков клавиатуры
 */
function setupKeyboardHandlers() {
    console.log('Настройка обработчиков клавиатуры...');
    
    // Настройка формы сообщений
    const messageForm = document.getElementById('messageForm');
    if (messageForm) {
        console.log('Найден элемент messageForm, добавляем обработчик отправки формы');
        messageForm.onsubmit = function(e) {
            console.log('Перехвачена отправка формы');
            e.preventDefault(); // Предотвращаем стандартную отправку формы
            handleMessageSubmit(e);
            return false;
        };
    } else {
        console.warn('Элемент messageForm не найден');
    }
    
    // Настройка отправки по клавише Enter
    const messageInput = document.getElementById('messageInput');
    if (messageInput) {
        console.log('Найден элемент messageInput, добавляем обработчик клавиши Enter');
        
        // Привязываем обработчик напрямую к элементу
        messageInput.onkeydown = function(e) {
            console.log('Нажата клавиша:', e.key, 'Shift:', e.shiftKey);
            
            // Отправка по Enter без Shift
            if (e.key === 'Enter' && !e.shiftKey) {
                console.log('Нажата клавиша Enter без Shift - отправляем сообщение');
                e.preventDefault(); // Предотвращаем перенос строки
                
                // Вызываем напрямую обработчик отправки сообщения
                handleMessageSubmit(e);
                return false;
            }
        };
        
        console.log('Обработчик клавиатуры для messageInput установлен');
    } else {
        console.warn('Элемент messageInput не найден для настройки обработчика клавиатуры');
    }
}

/**
 * Настройка обработчиков событий
 */
function setupEventListeners() {
    console.log('Настройка обработчиков событий...');
    
    // Обработчик для основного селектора шаблонов
    const promptTemplatesSelect = document.getElementById('promptTemplates');
    if (promptTemplatesSelect) {
        console.log('Найден элемент promptTemplates, добавляем обработчик');
        promptTemplatesSelect.addEventListener('change', async function() {
            const templateId = this.value;
            if (templateId) {
                await loadTemplateDetails(templateId);
            } else {
                // Очищаем предпросмотр если выбран пустой вариант
                const previewElement = document.getElementById('promptPreview');
                if (previewElement) {
                    previewElement.innerHTML = '';
                }
            }
        });
    } else {
        console.log('Элемент promptTemplates не найден на этой странице');
    }
    
    // Обработчик для кнопки применения шаблона
    const applyTemplateBtn = document.getElementById('applyTemplateBtn');
    if (applyTemplateBtn) {
        console.log('Найден элемент applyTemplateBtn, добавляем обработчик');
        applyTemplateBtn.addEventListener('click', async function() {
            const promptTemplatesElement = document.getElementById('promptTemplates');
            if (!promptTemplatesElement) {
                console.error('Элемент promptTemplates не найден при нажатии на кнопку применения');
                showToast('Ошибка: элемент выбора шаблона не найден', 'error');
                return;
            }
            
            const templateId = promptTemplatesElement.value;
            if (templateId) {
                await applyPromptTemplate(templateId);
            } else {
                alert('Сначала выберите шаблон');
            }
        });
    } else {
        console.log('Элемент applyTemplateBtn не найден на этой странице');
    }
    
    // Обработчик для селектора шаблонов в модальном окне
    const modalPromptTemplatesSelect = document.getElementById('modalPromptTemplates');
    if (modalPromptTemplatesSelect) {
        console.log('Найден элемент modalPromptTemplates, добавляем обработчик');
        modalPromptTemplatesSelect.addEventListener('change', async function() {
            const templateId = this.value;
            if (templateId) {
                // Действия при выборе шаблона в модальном окне
                const template = await loadTemplateDetails(templateId);
                if (template && template.system_prompt && document.getElementById('systemPromptInput')) {
                    document.getElementById('systemPromptInput').value = template.system_prompt;
                }
            }
        });
    } else {
        console.log('Элемент modalPromptTemplates не найден на этой странице');
    }
    
    // Обработчик отправки формы сообщения
    const messageForm = document.getElementById('messageForm');
    if (messageForm) {
        console.log('Найден элемент messageForm, добавляем обработчик отправки');
        messageForm.addEventListener('submit', handleMessageSubmit);
    } else {
        console.log('Элемент messageForm не найден на этой странице');
    }
}

// Глобальные переменные и конфигурация
let isWebSocketActive = false;
let socket = null;
let activeMessageId = null; // Глобальная переменная для отслеживания активного сообщения
const API_BASE_URL = ''; // Базовый URL API (пустой для относительных путей)

/**
 * Настройка WebSocket соединения для чата
 */
function setupWebSocket(chatId) {
    if (window.chatSocket && window.chatSocket.readyState === WebSocket.OPEN) {
        window.chatSocket.close();
    }
    
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/chat/ws/${chatId}`;
    
    window.chatSocket = new WebSocket(wsUrl);
    
    window.chatSocket.onopen = function(e) {
        console.log('WebSocket соединение установлено');
    };
    
    window.chatSocket.onmessage = function(event) {
        const data = JSON.parse(event.data);
        
        if (data.error) {
            showError(data.error);
            return;
        }
        
        if (data.type === 'user_message') {
            // Пользовательское сообщение подтверждено
            console.log('Сообщение пользователя подтверждено:', data);
        } 
        else if (data.type === 'assistant_message_chunk') {
            // Обрабатываем фрагмент ответа от ассистента
            const messageId = data.id;
            const chunk = data.content;
            
            // Находим или создаем сообщение ассистента
            const aiMessageElement = document.getElementById(`message-${messageId}`);
            if (aiMessageElement) {
                const contentElement = aiMessageElement.querySelector('.message-content');
                contentElement.innerHTML = marked.parse(contentElement.innerHTML + chunk);
                // Прокручиваем к последнему сообщению
                scrollToBottom();
            } else {
                // Создаем новое сообщение ассистента
                addAssistantMessageToUI(messageId, chunk);
            }
        }
        else if (data.type === 'done') {
            // Завершение генерации ответа
            console.log('Генерация ответа завершена:', data);
            // Включаем кнопку отправки и поле ввода
            enableMessageInput();
        }
        else if (data.type === 'error') {
            // Обрабатываем ошибку
            showError(data.content);
            enableMessageInput();
        }
    };
    
    window.chatSocket.onclose = function(event) {
        if (event.wasClean) {
            console.log(`Соединение закрыто (код=${event.code} причина=${event.reason})`);
        } else {
            console.log('Соединение прервано');
        }
    };
    
    window.chatSocket.onerror = function(error) {
        console.error(`WebSocket ошибка: ${error.message}`);
        showError('Ошибка WebSocket соединения');
    };
}

/**
 * Добавляет сообщение ассистента в UI
 */
function addAssistantMessageToUI(messageId, content) {
    const messagesList = document.querySelector('.messages-list');
    const messageHTML = `
        <div id="message-${messageId}" class="message message-assistant">
            <div class="message-content">${marked.parse(content)}</div>
        </div>
    `;
    messagesList.insertAdjacentHTML('beforeend', messageHTML);
    highlightCode();
    scrollToBottom();
}

/**
 * Отправка сообщения через WebSocket
 */
function sendMessageViaWebSocket(message, modelName) {
    if (!window.chatSocket || window.chatSocket.readyState !== WebSocket.OPEN) {
        showError('WebSocket соединение не установлено');
        return;
    }
    
    const messageData = {
        prompt: message,
        model: modelName
    };
    
    window.chatSocket.send(JSON.stringify(messageData));
    
    // Добавляем сообщение пользователя в UI сразу
    const messagesList = document.querySelector('.messages-list');
    const messageHTML = `
        <div class="message message-user">
            <div class="message-content">${message}</div>
        </div>
    `;
    messagesList.insertAdjacentHTML('beforeend', messageHTML);
    
    // Отключаем поле ввода и кнопку до получения ответа
    disableMessageInput();
    
    // Прокручиваем к последнему сообщению
    scrollToBottom();
}

/**
 * Отключает поле ввода сообщения и кнопку отправки
 */
function disableMessageInput() {
    console.log('Отключение поля ввода...');
    
    const messageInput = document.getElementById('messageInput');
    const sendButton = document.getElementById('sendButton');
    
    if (messageInput) {
        messageInput.disabled = true;
        messageInput.classList.add('disabled');
    }
    
    if (sendButton) {
        sendButton.disabled = true;
        sendButton.classList.add('disabled');
    }
}

/**
 * Включает поле ввода сообщения и кнопку отправки
 */
function enableMessageInput() {
    console.log('Включение поля ввода...');
    
    const messageInput = document.getElementById('messageInput');
    const sendButton = document.getElementById('sendButton');
    
    if (messageInput) {
        messageInput.disabled = false;
        messageInput.classList.remove('disabled');
    }
    
    if (sendButton) {
        sendButton.disabled = false;
        sendButton.classList.remove('disabled');
    }
}

/**
 * Отправка сообщения
 */
async function sendMessage() {
    const messageInput = document.getElementById('messageInput');
    const modelSelector = document.getElementById('modelSelector');
    const currentChatIdEl = document.getElementById('currentChatId');
    
    // Проверяем наличие всех необходимых элементов
    if (!messageInput || !modelSelector || !currentChatIdEl) {
        console.error('Не найдены необходимые элементы формы:', { messageInput, modelSelector, currentChatIdEl });
        showError('Ошибка отправки сообщения: не найдены элементы формы');
        return;
    }
    
    const message = messageInput.value.trim();
    const model = modelSelector.value;
    const chatId = currentChatIdEl.value;
    
    if (!message) {
        console.log('Пустое сообщение, отправка отменена');
        return;
    }
    
    if (!model) {
        showError('Выберите модель для общения');
        return;
    }
    
    console.log('Отправка сообщения:', { message, model, chatId });
    
    try {
        // Добавляем сообщение пользователя в UI
        addMessageToUI('user', message);
        
        // Очищаем поле ввода
        messageInput.value = '';
        
        // Отключаем поле ввода и кнопку до получения ответа
        disableMessageInput();
        
        // Отправляем запрос
        const response = await fetch(`/chat/${chatId}/messages`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: new URLSearchParams({
                'message': message,
                'model_name': model
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            
            // Добавляем ответ модели в UI
            addMessageToUI(data.model_response.content, 'assistant');
        } else {
            const errorData = await response.json();
            showError(`Ошибка: ${errorData.detail || 'Не удалось получить ответ'}`);
        }
    } catch (error) {
        console.error('Ошибка при отправке сообщения:', error);
        showError(`Ошибка отправки: ${error.message}`);
    } finally {
        // Включаем поле ввода и кнопку
        enableMessageInput();
        
        // Прокручиваем к последнему сообщению
        scrollToBottom();
    }
}

/**
 * Добавляет сообщение в интерфейс чата
 */
function addMessageToUI(role, content) {
    console.log(`Добавление сообщения в UI:`, { role, content });
    
    // Корректировка параметров, если порядок перепутан
    if (typeof role === 'string' && (role === 'user' || role === 'assistant')) {
        // Параметры в правильном порядке
    } else if (typeof content === 'string' && (content === 'user' || content === 'assistant')) {
        // Параметры в обратном порядке
        const temp = role;
        role = content;
        content = temp;
    } else {
        console.error('Неправильные параметры для addMessageToUI:', { role, content });
        return;
    }
    
    const chatMessages = document.getElementById('chatMessages');
    if (!chatMessages) {
        console.error('Элемент chatMessages не найден');
        return;
    }
    
    // Создаем элемент сообщения
    const messageElement = document.createElement('div');
    messageElement.className = `message ${role}-message`;
    
    // Добавляем аватар
    const avatarDiv = document.createElement('div');
    avatarDiv.className = 'message-avatar';
    
    const avatarText = document.createElement('div');
    avatarText.className = `avatar ${role === 'user' ? 'user-avatar' : 'assistant-avatar'}`;
    avatarText.textContent = role === 'user' ? 'Вы' : 'AI';
    
    avatarDiv.appendChild(avatarText);
    messageElement.appendChild(avatarDiv);
    
    // Добавляем контент сообщения
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    // Если это ответ ассистента, форматируем markdown
    if (role === 'assistant') {
        try {
            contentDiv.innerHTML = marked.parse(content);
        } catch (error) {
            console.error('Ошибка при разборе Markdown:', error);
            contentDiv.textContent = content;
        }
    } else {
        contentDiv.textContent = content;
    }
    
    messageElement.appendChild(contentDiv);
    chatMessages.appendChild(messageElement);
    
    // Прокручиваем чат вниз
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    // Подсвечиваем код в блоках кода
    setTimeout(() => {
        highlightCode();
    }, 100);
}

/**
 * Отправка сообщения через обычный HTTP запрос
 */
async function sendMessageViaHTTP(chatId, message) {
    console.log(`Отправка сообщения через HTTP для чата ${chatId}`);
    
    try {
        // Для отладки
        console.log('URL запроса:', `/chat/chats/${chatId}/messages`);
        console.log('Тело запроса:', JSON.stringify({ content: message }));
        
        const response = await fetch(`/chat/chats/${chatId}/messages`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ content: message })
        });
        
        console.log('Статус ответа:', response.status);
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error('Ошибка ответа сервера:', errorText);
            throw new Error(`Ошибка HTTP: ${response.status}. ${errorText}`);
        }
        
        const data = await response.json();
        console.log('Получен ответ:', data);
        
        // Проверяем структуру ответа и добавляем ответ ассистента в интерфейс
        if (data.assistant_message && data.assistant_message.content) {
            addMessageToUI('assistant', data.assistant_message.content);
        } else if (data.response && data.response.content) {
            addMessageToUI('assistant', data.response.content);
        } else {
            console.error('Ответ не содержит сообщения ассистента:', data);
            showToast('Получен некорректный ответ от сервера', 'error');
        }
    } catch (error) {
        console.error('Ошибка отправки сообщения через HTTP:', error);
        showToast(`Ошибка получения ответа от модели: ${error.message}`, 'error');
    }
}

/**
 * Создание HTML разметки для сообщения
 */
function createMessageHTML(content, role, messageId = null) {
    const formattedContent = formatMessage(content);
    const avatarLabel = role === 'user' ? 'Вы' : 'AI';
    
    return `
        <div class="message ${role}-message" ${messageId ? `id="${messageId}"` : ''}>
            <div class="message-avatar">
                <div class="avatar ${role}-avatar">${avatarLabel}</div>
            </div>
            <div class="message-content">${formattedContent}</div>
        </div>
    `;
}

/**
 * Подсветка синтаксиса в блоках кода
 */
function highlightCode() {
    console.log('Применение подсветки синтаксиса к блокам кода');
    
    document.querySelectorAll('pre code').forEach((block) => {
        // Пытаемся автоматически определить язык программирования
        hljs.highlightElement(block);
    });
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
    
    // Обработка блоков кода с указанием языка (```python code```)
    formattedText = formattedText.replace(/```(\w+)?\s*([^`]+)```/g, function(match, language, codeContent) {
        const lang = language ? ` class="language-${language}"` : '';
        return `<pre class="code-block"><code${lang}>${codeContent}</code></pre>`;
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
    const errorElement = document.createElement('div');
    errorElement.className = 'error-message';
    errorElement.textContent = message;
    
    document.body.appendChild(errorElement);
    
    // Автоматически скрыть сообщение через 5 секунд
    setTimeout(() => {
        errorElement.classList.add('fade-out');
        setTimeout(() => {
            document.body.removeChild(errorElement);
        }, 300);
    }, 5000);
}

/**
 * Показать сообщение об успехе
 */
function showSuccess(message) {
    const successElement = document.createElement('div');
    successElement.className = 'success-message';
    successElement.textContent = message;
    
    document.body.appendChild(successElement);
    
    // Автоматически скрыть сообщение через 3 секунды
    setTimeout(() => {
        successElement.classList.add('fade-out');
        setTimeout(() => {
            document.body.removeChild(successElement);
        }, 300);
    }, 3000);
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
    const modalPromptTemplates = document.getElementById('modalPromptTemplates');
    
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
        saveModelSettings(e);
    });
    
    // Выбор шаблона промпта в модальном окне
    if (modalPromptTemplates) {
        modalPromptTemplates.addEventListener('change', function() {
            if (this.value) {
                // Загрузить выбранный шаблон в модальном окне
                loadPromptTemplate(this.value);
            }
        });
    }
    
    // Добавляем обработчик для кнопки применения промпта в текущем сообщении
    const applyPromptBtn = document.getElementById('applyPromptBtn');
    if (applyPromptBtn) {
        applyPromptBtn.addEventListener('click', function() {
            const selectedTemplate = document.getElementById('promptTemplates').value;
            if (selectedTemplate) {
                applyPromptToInput(selectedTemplate);
            }
        });
    }
}

/**
 * Загрузка настроек модели
 */
async function loadModelSettings(modelId) {
    if (!modelId) {
        console.warn('ID модели не указан');
        return null;
    }
    
    console.log(`Загрузка настроек модели ${modelId}...`);
    
    try {
        const response = await fetch(`/models/${modelId}/settings`);
        if (!response.ok) {
            throw new Error(`Ошибка HTTP: ${response.status}`);
        }
        
        const settings = await response.json();
        console.log('Загружены настройки модели:', settings);
        
        // Обновляем UI с настройками
        const temperatureSlider = document.getElementById('temperature');
        const temperatureValue = document.getElementById('temperatureValue');
        const systemPromptInput = document.getElementById('systemPromptInput');
        
        if (temperatureSlider && settings.temperature) {
            temperatureSlider.value = settings.temperature;
            if (temperatureValue) {
                temperatureValue.textContent = settings.temperature;
            }
        }
        
        if (systemPromptInput && settings.system_prompt) {
            systemPromptInput.value = settings.system_prompt;
        }
        
        return settings;
    } catch (error) {
        console.error(`Ошибка загрузки настроек модели ${modelId}:`, error);
        return null;
    }
}

/**
 * Открытие модального окна с настройками модели
 */
async function openModelSettings() {
    const modelSelector = document.getElementById('modelSelector');
    const modelName = modelSelector.value;
    
    if (!modelName) {
        showError('Выберите модель для настройки');
        return;
    }
    
    document.getElementById('currentModelName').textContent = modelName;
    
    try {
        const response = await fetch(`/models/${modelName}/settings`);
        if (response.ok) {
            const settings = await response.json();
            
            document.getElementById('temperature').value = settings.temperature;
            document.getElementById('temperatureValue').textContent = settings.temperature;
            document.getElementById('maxTokens').value = settings.max_tokens;
            document.getElementById('systemPrompt').value = settings.system_prompt || '';
            
            // Загружаем шаблоны промптов
            await loadPromptTemplates();
            
            // Показываем модальное окно
            document.getElementById('modelSettingsModal').style.display = 'block';
        } else {
            showError('Ошибка загрузки настроек');
        }
    } catch (error) {
        console.error('Ошибка:', error);
        showError('Ошибка загрузки настроек');
    }
}

/**
 * Сохранение настроек модели
 */
async function saveModelSettings(event) {
    event.preventDefault();
    
    const modelName = document.getElementById('currentModelName').textContent;
    const temperature = document.getElementById('temperature').value;
    const maxTokens = document.getElementById('maxTokens').value;
    const systemPrompt = document.getElementById('systemPrompt').value;
    
    const formData = new FormData();
    formData.append('temperature', temperature);
    formData.append('max_tokens', maxTokens);
    formData.append('system_prompt', systemPrompt);
    
    try {
        const response = await fetch(`/models/${modelName}/settings`, {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            // Обновляем глобальные настройки текущей модели
            window.currentModelSettings = {
                temperature: parseFloat(temperature),
                max_tokens: parseInt(maxTokens),
                system_prompt: systemPrompt
            };
            
            // Закрываем модальное окно
            document.getElementById('modelSettingsModal').style.display = 'none';
            
            // Показываем уведомление об успехе
            showSuccess('Настройки сохранены');
        } else {
            const errorData = await response.json();
            showError(`Ошибка сохранения настроек: ${errorData.detail || 'Неизвестная ошибка'}`);
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
    console.log('Загрузка шаблонов промптов...');
    
    try {
        // Сначала пробуем URL из модуля моделей (для совместимости)
        let url = '/models/prompts/list';
        console.log('Попытка загрузки шаблонов с:', url);
        
        let response = await fetch(url);
        if (!response.ok) {
            // Если не удалось, пробуем новый URL из модуля шаблонов
            url = '/templates/list';
            console.log('Попытка загрузки шаблонов с альтернативного URL:', url);
            response = await fetch(url);
            
            if (!response.ok) {
                throw new Error(`Ошибка HTTP: ${response.status}`);
            }
        }
        
        const templates = await response.json();
        console.log(`Загружено ${templates.length} шаблонов:`, templates);
        
        // Обновляем выпадающие списки с шаблонами
        const promptTemplatesElements = document.querySelectorAll('#promptTemplates, #modalPromptTemplates');
        console.log(`Найдено ${promptTemplatesElements.length} элементов выбора шаблонов`);
        
        promptTemplatesElements.forEach(selectElement => {
            if (selectElement) {
                console.log('Обновление элемента выбора шаблона:', selectElement.id);
                
                // Очищаем существующие опции
                selectElement.innerHTML = '<option value="">Выберите шаблон...</option>';
                
                // Добавляем новые опции
                templates.forEach(template => {
                    const option = document.createElement('option');
                    option.value = template.id;
                    option.textContent = template.name;
                    selectElement.appendChild(option);
                    
                    // Если это шаблон "Личный ассистент Артём", делаем его выбранным по умолчанию
                    if (template.name === "Личный ассистент Артём") {
                        console.log('Установка шаблона по умолчанию "Личный ассистент Артём"');
                        option.selected = true;
                        window.defaultTemplateId = template.id;
                        
                        // Загружаем детали шаблона
                        setTimeout(async () => {
                            await loadTemplateDetails(template.id);
                        }, 100);
                    }
                });
            } else {
                console.log('Элемент выбора шаблона не найден');
            }
        });
        
        return templates;
    } catch (error) {
        console.error('Ошибка загрузки шаблонов:', error);
        return [];
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
                
                // Показываем пример запроса пользователя
                if (template.user_prompt) {
                    const userPromptPreview = document.getElementById('userPromptPreview');
                    if (userPromptPreview) {
                        userPromptPreview.textContent = template.user_prompt;
                        userPromptPreview.parentElement.style.display = 'block';
                    }
                }
            }
        }
    } catch (error) {
        console.error('Ошибка загрузки шаблона:', error);
    }
}

/**
 * Применение выбранного промпта к полю ввода
 */
async function applyPromptToInput(templateId) {
    try {
        const response = await fetch(`/models/prompts/list`);
        if (response.ok) {
            const templates = await response.json();
            const template = templates.find(t => t.id == templateId);
            
            if (template && template.user_prompt) {
                // Вставляем пример запроса в поле ввода
                const messageInput = document.getElementById('messageInput');
                messageInput.value = template.user_prompt;
                messageInput.focus();
                
                // Применяем системный промпт к настройкам текущей модели
                const modelSelector = document.getElementById('modelSelector');
                const modelName = modelSelector.value;
                
                // Проверяем, что модель выбрана
                if (!modelName) {
                    showError('Сначала выберите модель');
                    return;
                }
                
                // Сохраняем системный промпт для текущей модели без открытия модального окна
                const formData = new FormData();
                formData.append('temperature', window.currentModelSettings?.temperature || 0.7);
                formData.append('max_tokens', window.currentModelSettings?.max_tokens || 1024);
                formData.append('system_prompt', template.system_prompt);
                
                await fetch(`/models/${modelName}/settings`, {
                    method: 'POST',
                    body: formData
                });
            }
        }
    } catch (error) {
        console.error('Ошибка применения шаблона:', error);
    }
}

/**
 * Загрузка деталей шаблона промпта
 */
async function loadTemplateDetails(templateId) {
    console.log(`Загрузка деталей шаблона ${templateId}...`);
    if (!templateId) {
        console.warn('ID шаблона не указан');
        return null;
    }
    
    try {
        // Сначала пробуем URL из модуля моделей
        let url = `/models/prompts/${templateId}`;
        console.log('Попытка загрузки деталей шаблона с:', url);
        
        let response = await fetch(url);
        if (!response.ok) {
            // Если не удалось, пробуем новый URL из модуля шаблонов
            url = `/templates/${templateId}`;
            console.log('Попытка загрузки деталей шаблона с альтернативного URL:', url);
            response = await fetch(url);
            
            if (!response.ok) {
                throw new Error(`Ошибка HTTP: ${response.status}`);
            }
        }
        
        const template = await response.json();
        console.log('Детали шаблона:', template);
        
        // Обновляем предпросмотр шаблона
        const previewElement = document.getElementById('promptPreview');
        if (previewElement) {
            let previewHTML = '';
            
            if (template.description) {
                previewHTML += `<div class="preview-description">${template.description}</div>`;
            }
            
            previewHTML += `<div class="preview-system-prompt">
                <strong>Системный промпт:</strong> 
                <pre>${template.system_prompt}</pre>
            </div>`;
            
            if (template.user_prompt) {
                previewHTML += `<div class="preview-user-prompt">
                    <strong>Пример запроса:</strong>
                    <pre>${template.user_prompt}</pre>
                </div>`;
            }
            
            previewElement.innerHTML = previewHTML;
        }
        
        return template;
    } catch (error) {
        console.error(`Ошибка загрузки шаблона ${templateId}:`, error);
        return null;
    }
}

/**
 * Применение шаблона промпта
 */
async function applyPromptTemplate(templateId) {
    console.log(`Применение шаблона ${templateId}...`);
    if (!templateId) {
        console.warn('ID шаблона не указан');
        return;
    }
    
    const template = await loadTemplateDetails(templateId);
    if (!template) {
        console.error('Не удалось загрузить шаблон');
        return;
    }
    
    // Применяем системный промпт к текущей модели
    const modelSelect = document.getElementById('modelSelect');
    console.log('Элемент modelSelect при применении шаблона:', modelSelect);
    
    if (!modelSelect) {
        console.error('Элемент modelSelect не найден при применении шаблона');
        showToast('Ошибка: элемент выбора модели не найден', 'error');
        return;
    }
    
    const selectedModel = modelSelect.value;
    if (!selectedModel) {
        showToast('Сначала выберите модель', 'warning');
        return;
    }
    
    try {
        console.log(`Сохранение системного промпта для модели ${selectedModel}`);
        // Сохраняем системный промпт в настройках модели
        const formData = new FormData();
        formData.append('system_prompt', template.system_prompt);
        
        const response = await fetch(`/models/${selectedModel}/settings`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`Ошибка HTTP: ${response.status}`);
        }
        
        // Если есть пример запроса, добавляем его в поле ввода
        if (template.user_prompt) {
            const messageInput = document.getElementById('messageInput');
            if (messageInput) {
                messageInput.value = template.user_prompt;
                console.log('Установлен пример запроса в поле ввода');
            } else {
                console.log('Элемент messageInput не найден, пропускаем установку значения');
            }
        }
        
        showToast(`Применен шаблон "${template.name}"`, 'success');
    } catch (error) {
        console.error('Ошибка применения шаблона:', error);
        showToast('Ошибка применения шаблона', 'error');
    }
}

/**
 * Загрузка моделей
 */
async function loadModels() {
    console.log('Загрузка моделей...');
    
    try {
        console.log('Отправка запроса на /models/list');
        
        // Добавляем случайный параметр запроса для предотвращения кеширования
        const timestamp = new Date().getTime();
        const url = `/models/list?_=${timestamp}`;
        
        console.log('Полный URL запроса:', url);
        
        const response = await fetch(url);
        console.log('Статус ответа:', response.status);
        
        if (!response.ok) {
            throw new Error(`Ошибка HTTP: ${response.status}`);
        }
        
        const responseText = await response.text();
        console.log('Ответ сервера (текст):', responseText);
        
        if (!responseText || responseText.trim() === '') {
            console.error('Получен пустой ответ от сервера');
            return [];
        }
        
        let models = [];
        try {
            models = JSON.parse(responseText);
            console.log('Успешно распарсен JSON:', models);
        } catch (e) {
            console.error('Ошибка при разборе JSON:', e);
            console.error('Проблемный текст:', responseText);
            throw new Error('Не удалось разобрать JSON ответ');
        }
        
        console.log(`Загружено ${models.length} моделей:`, models);
        
        // Ищем селект моделей на странице
        const modelSelect = document.getElementById('modelSelect');
        console.log('Найден элемент modelSelect:', modelSelect);
        
        if (!modelSelect) {
            console.error('Элемент выбора модели не найден');
            console.error('Доступные элементы с ID, содержащим "model":', 
                Array.from(document.querySelectorAll('[id*="model"]')).map(el => el.id));
            return models;
        }
        
        // Очистить существующие опции
        modelSelect.innerHTML = '<option value="">Выберите модель...</option>';
        console.log('Очищен селект моделей');
        
        // Добавить новые опции
        models.forEach(model => {
            console.log('Добавление модели в селект:', model);
            const option = document.createElement('option');
            // Используем model.id для значения - это критически важно для корректной работы
            option.value = model.id.toString(); // Преобразуем в строку, чтобы избежать проблем с типами
            option.textContent = model.display_name || model.name;
            option.setAttribute('data-name', model.name);
            option.setAttribute('data-id', model.id);
            modelSelect.appendChild(option);
            console.log(`Добавлена опция: id=${model.id}, value=${option.value}, text=${option.textContent}`);
            
            // Если это qwen2.5:3b, запоминаем его для автоматического выбора
            if (model.name === 'qwen2.5:3b') {
                console.log('Установка модели по умолчанию qwen2.5:3b с ID:', model.id);
                window.defaultModelId = model.id.toString(); // Также преобразуем в строку
            }
        });
        
        // Автоматически выбираем qwen2.5:3b если он есть
        if (window.defaultModelId) {
            console.log('Автоматический выбор модели с ID:', window.defaultModelId);
            modelSelect.value = window.defaultModelId;
            console.log('Текущее выбранное значение после установки:', modelSelect.value);
            
            // Проверяем, что значение действительно установлено
            if (modelSelect.value !== window.defaultModelId) {
                console.warn(`Не удалось установить значение ${window.defaultModelId}, пробуем найти опцию по атрибуту data-id`);
                const option = modelSelect.querySelector(`option[data-id="${window.defaultModelId}"]`);
                if (option) {
                    modelSelect.value = option.value;
                    console.log('Значение установлено через опцию:', modelSelect.value);
                }
            }
            
            await loadModelSettings(window.defaultModelId);
            
            // Если есть шаблон по умолчанию и выбрана модель, автоматически применяем шаблон
            if (window.defaultTemplateId) {
                console.log('Автоматическое применение шаблона с ID:', window.defaultTemplateId);
                setTimeout(async () => {
                    await applyPromptTemplate(window.defaultTemplateId);
                }, 500);
            }
        }
        
        return models;
    } catch (error) {
        console.error('Ошибка загрузки моделей:', error);
        return [];
    }
}

/**
 * Загрузка списка чатов
 */
async function loadChats() {
    console.log('Загрузка чатов...');
    
    try {
        const response = await fetch('/chat/chats/list');
        if (!response.ok) {
            throw new Error(`Ошибка HTTP: ${response.status}`);
        }
        
        const chats = await response.json();
        console.log(`Загружено ${chats.length} чатов`);
        
        // Обновляем список чатов в UI
        const chatsList = document.getElementById('chatsList');
        if (chatsList) {
            // Очищаем текущий список
            chatsList.innerHTML = '';
            
            if (chats.length === 0) {
                chatsList.innerHTML = '<div class="empty-message">У вас пока нет чатов. Создайте новый чат.</div>';
                return chats;
            }
            
            // Добавляем чаты в список
            chats.forEach(chat => {
                const chatDate = new Date(chat.created_at);
                const formattedDate = chatDate.toLocaleDateString() + ' ' + chatDate.toLocaleTimeString();
                
                const chatItem = document.createElement('div');
                chatItem.className = 'chat-item';
                chatItem.dataset.chatId = chat.id;
                
                chatItem.innerHTML = `
                    <div class="chat-item-title">${chat.title}</div>
                    <div class="chat-item-date">${formattedDate}</div>
                `;
                
                chatItem.addEventListener('click', () => {
                    window.location.href = `/chat/chats/${chat.id}`;
                });
                
                chatsList.appendChild(chatItem);
            });
        }
        
        return chats;
    } catch (error) {
        console.error('Ошибка загрузки чатов:', error);
        
        // Показываем сообщение об ошибке
        const chatsList = document.getElementById('chatsList');
        if (chatsList) {
            chatsList.innerHTML = '<div class="error-message">Ошибка загрузки чатов. Попробуйте обновить страницу.</div>';
        }
        
        return [];
    }
}

/**
 * Отображение всплывающего уведомления
 */
function showToast(message, type = 'info') {
    console.log(`Уведомление (${type}): ${message}`);
    
    // Создаем элемент уведомления
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    
    // Добавляем в контейнер для уведомлений
    const toastContainer = document.getElementById('toastContainer');
    if (!toastContainer) {
        // Если контейнера нет, создаем его
        const container = document.createElement('div');
        container.id = 'toastContainer';
        container.className = 'toast-container';
        document.body.appendChild(container);
        container.appendChild(toast);
    } else {
        toastContainer.appendChild(toast);
    }
    
    // Автоматически удаляем через 3 секунды
    setTimeout(() => {
        toast.classList.add('toast-hidden');
        setTimeout(() => {
            toast.remove();
        }, 300);
    }, 3000);
}

/**
 * Обработчик отправки сообщения
 */
async function handleMessageSubmit(event) {
    console.log('ВЫЗВАНА ФУНКЦИЯ handleMessageSubmit', event);
    event.preventDefault();
    console.log('event.preventDefault() выполнен');
    
    const messageInput = document.getElementById('messageInput');
    console.log('Найден элемент messageInput:', messageInput);
    
    if (!messageInput) {
        console.error('Элемент messageInput не найден!');
        return;
    }
    
    const message = messageInput.value.trim();
    console.log('Текст сообщения:', message, 'Длина:', message.length);
    
    // Проверяем, что поле ввода не пустое
    if (!message) {
        console.log('Сообщение пустое, отмена отправки');
        return;
    }
    
    // Получаем ID текущего чата
    const chatContainer = document.getElementById('chatContainer');
    console.log('Найден элемент chatContainer:', chatContainer);
    
    if (!chatContainer) {
        console.error('Не найден элемент chatContainer');
        showToast('Ошибка: не найден контейнер чата', 'error');
        return;
    }
    
    const chatId = chatContainer.dataset.chatId;
    console.log('ID чата:', chatId);
    
    if (!chatId) {
        console.error('ID чата не найден');
        showToast('Выберите или создайте чат', 'error');
        return;
    }
    
    // Получаем имя модели из скрытого поля
    const currentModelName = document.getElementById('currentModelName').value;
    console.log('Используемая модель:', currentModelName);
    
    if (!currentModelName) {
        console.error('Имя модели не найдено');
        showToast('Ошибка: не указана модель', 'error');
        return;
    }
    
    // Добавляем сообщение пользователя в UI и очищаем поле ввода
    console.log('Добавление сообщения пользователя в UI');
    addMessageToUI('user', message);
    messageInput.value = '';
    
    // Добавляем индикатор ожидания
    console.log('Добавление индикатора загрузки');
    const chatMessages = document.getElementById('chatMessages');
    const loadingId = 'loading-' + Date.now();
    console.log('ID индикатора загрузки:', loadingId);
    const loadingHTML = createMessageHTML('<div class="loading-dots"><span>.</span><span>.</span><span>.</span></div>', 'assistant', loadingId);
    chatMessages.insertAdjacentHTML('beforeend', loadingHTML);
    console.log('Индикатор загрузки добавлен в DOM');
    scrollToBottom();
    
    // Отключаем поле ввода и кнопки на время ожидания ответа
    console.log('Отключение поля ввода');
    disableMessageInput();
    
    try {
        console.log('Начало отправки сообщения на сервер...');
        
        // Формируем данные для отправки
        const requestBody = {
            content: message,
            model_name: currentModelName
        };
        console.log('Данные для отправки:', requestBody);
        
        // Отправляем запрос на сервер
        console.log(`Отправка POST запроса на /chat/chats/${chatId}/messages`);
        const response = await fetch(`/chat/chats/${chatId}/messages`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestBody)
        });
        console.log('Получен ответ от сервера, статус:', response.status);
        
        // Удаляем индикатор загрузки
        const loadingElement = document.getElementById(loadingId);
        if (loadingElement) {
            console.log('Удаление индикатора загрузки');
            loadingElement.remove();
        } else {
            console.warn('Индикатор загрузки не найден:', loadingId);
        }
        
        if (!response.ok) {
            throw new Error(`Ошибка HTTP: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Получен ответ от сервера:', data);
        
        // Добавляем ответ модели в UI
        if (data.assistant_message && data.assistant_message.content) {
            console.log('Добавление ответа ассистента в UI');
            addMessageToUI('assistant', data.assistant_message.content);
            // Подсвечиваем код после добавления ответа
            highlightCode();
        } else {
            console.error('Ответ не содержит сообщения ассистента:', data);
            showToast('Получен некорректный ответ от сервера', 'error');
        }
    } catch (error) {
        console.error('Ошибка при отправке сообщения:', error);
        showToast('Ошибка при отправке сообщения: ' + error.message, 'error');
    } finally {
        // Включаем поле ввода и кнопки
        console.log('Включение поля ввода');
        enableMessageInput();
    }
}

/**
 * Проверяет, поддерживает ли браузер WebSocket
 */
function isWebSocketSupported() {
    return 'WebSocket' in window || 'MozWebSocket' in window;
}

/**
 * Создание нового чата
 */
async function createNewChat() {
    const modelSelect = document.getElementById('modelSelect');
    
    if (!modelSelect || !modelSelect.value) {
        showToast('Выберите модель для создания чата', 'warning');
        return;
    }
    
    const modelId = modelSelect.value;
    const chatTitle = "Новый чат";
    
    try {
        console.log(`Отправка запроса на создание чата с моделью ID=${modelId}`);
        
        const response = await fetch('/chat/chats/new', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                title: chatTitle,
                model_id: modelId
            })
        });
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error('Ошибка создания чата:', errorText);
            showToast('Ошибка создания чата', 'error');
            return;
        }
        
        const chat = await response.json();
        console.log('Успешно создан чат:', chat);
        
        // Обновляем список чатов
        await loadChats();
        
        // Переходим к новому чату
        window.location.href = `/chat/chats/${chat.id}`;
    } catch (error) {
        console.error('Ошибка при создании чата:', error);
        showToast('Ошибка при создании чата', 'error');
    }
} 