document.addEventListener('DOMContentLoaded', function() {
    // Обработчики для существующих чатов
    setupChatItemHandlers();
    
    // Обработка клавиш ввода (для отправки сообщения по Enter)
    setupMessageInputHandlers();
});

/**
 * Настройка обработчиков для элементов чата в боковой панели
 */
function setupChatItemHandlers() {
    // Обработчик кликов по элементам чата в боковой панели
    const chatItems = document.querySelectorAll('.chat-item');
    chatItems.forEach(item => {
        // Клик по элементу чата - переход к чату
        item.addEventListener('click', function(e) {
            if (!e.target.classList.contains('delete-chat-btn')) {
                const chatId = this.dataset.chatId;
                window.location.href = `/chat/chats/${chatId}`;
            }
        });
    });
    
    // Обработчик кнопок удаления чата
    const deleteBtns = document.querySelectorAll('.delete-chat-btn');
    deleteBtns.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.stopPropagation();
            const chatId = this.dataset.chatId;
            if (confirm('Вы действительно хотите удалить этот чат?')) {
                deleteChat(chatId);
            }
        });
    });
}

/**
 * Создание нового чата
 */
async function createNewChat() {
    console.log('===== ВЫЗВАНА ФУНКЦИЯ createNewChat() =====');
    const modelSelect = document.getElementById('modelSelect');
    console.log('Элемент modelSelect:', modelSelect);
    
    if (!modelSelect || !modelSelect.value) {
        console.error('Не выбрана модель для чата');
        showError('Выберите модель для создания чата');
        return;
    }
    
    const modelId = modelSelect.value;
    const chatTitle = "Новый чат";
    
    console.log('Данные для создания чата:', { modelId, chatTitle });
    
    try {
        console.log(`Отправка запроса на создание чата с моделью ID=${modelId}`);
        
        // Создаем объект для отправки
        const requestData = {
            title: chatTitle,
            model_id: modelId
        };
        
        console.log('Сформированный запрос:', JSON.stringify(requestData));
        console.log('URL запроса:', '/chat/chats/new');
        
        const response = await fetch('/chat/chats/new', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        });
        
        console.log('Получен ответ от сервера:', response.status, response.statusText);
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error('Ошибка создания чата:', errorText);
            showError('Ошибка создания чата');
            return;
        }
        
        const chat = await response.json();
        console.log('Успешно создан чат:', chat);
        
        // Переходим к новому чату
        console.log('Переход к чату:', `/chat/chats/${chat.id}`);
        window.location.href = `/chat/chats/${chat.id}`;
    } catch (error) {
        console.error('Исключение при создании чата:', error);
        showError('Ошибка при создании чата: ' + error.message);
    }
}

/**
 * Удаление чата
 */
async function deleteChat(chatId) {
    try {
        const response = await fetch(`/chat/chats/${chatId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            // Если мы находимся на странице этого чата, перенаправляем на главную
            if (window.location.pathname.includes(`/chat/chats/${chatId}`)) {
                window.location.href = '/';
            } else {
                // Иначе просто удаляем элемент из DOM
                const chatElement = document.querySelector(`.chat-item[data-chat-id="${chatId}"]`);
                if (chatElement) {
                    chatElement.remove();
                }
            }
        } else {
            console.error('Ошибка удаления чата');
        }
    } catch (error) {
        console.error('Ошибка:', error);
    }
}

/**
 * Настройка обработчиков для поля ввода сообщения (отправка по Enter)
 */
function setupMessageInputHandlers() {
    const messageInput = document.getElementById('messageInput');
    if (messageInput) {
        messageInput.addEventListener('keydown', function(e) {
            // Ctrl+Enter или просто Enter для отправки
            if ((e.ctrlKey && e.key === 'Enter') || (!e.shiftKey && e.key === 'Enter')) {
                e.preventDefault();
                const sendBtn = document.getElementById('sendMessageBtn');
                if (sendBtn) {
                    sendBtn.click();
                }
            }
        });
    }
}

/**
 * Показать сообщение об ошибке
 */
function showError(message) {
    // Удаляем старые сообщения об ошибках, если они есть
    document.querySelectorAll('.error-message').forEach(el => el.remove());
    
    // Создаем элемент сообщения
    const errorElement = document.createElement('div');
    errorElement.className = 'error-message';
    errorElement.textContent = message;
    
    // Добавляем элемент в DOM
    document.body.appendChild(errorElement);
    
    // Анимация появления
    setTimeout(() => {
        errorElement.classList.add('fade-in');
    }, 10);
    
    // Автоматическое скрытие через 5 секунд
    setTimeout(() => {
        errorElement.classList.add('fade-out');
        setTimeout(() => {
            errorElement.remove();
        }, 500);
    }, 5000);
} 